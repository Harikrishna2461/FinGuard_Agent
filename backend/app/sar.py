"""
SAR (Suspicious Activity Report) export.

Two formats:

  GET /api/sar/<case_id>.json    → FinCEN-aligned JSON payload
  GET /api/sar/<case_id>.pdf     → printable filing package (reportlab)

We don't pretend to be a BSA E-Filing integration — this produces the
analyst's SAR worksheet and a human-readable narrative from the case
timeline, portfolio, transaction, and AI analysis. It's what the
compliance officer ships up the chain or keeps on file.

Filing a SAR (state → closed_sar_filed) is gated to supervisor+ elsewhere;
*exporting* the worksheet is allowed for anyone who can read the case.
"""

from __future__ import annotations

import io
import logging
from datetime import datetime
from typing import Optional

from flask import Blueprint, jsonify, send_file, abort

from app.auth import require_auth, current_tenant_id
from app import audit
from models.models import Case, CaseEvent, Portfolio, Transaction

logger = logging.getLogger(__name__)

sar_bp = Blueprint("sar", __name__)


# ─────────────────────────────────────────────────────────────────────
#  Shared payload builder
# ─────────────────────────────────────────────────────────────────────

def _fetch_case(case_id: int) -> Optional[Case]:
    tid = current_tenant_id()
    q = Case.query.filter(Case.id == case_id)
    if tid is not None:
        q = q.filter(Case.tenant_id == tid)
    return q.first()


def _build_sar_payload(case: Case) -> dict:
    """Build the structured SAR worksheet payload for a case."""
    portfolio = Portfolio.query.get(case.portfolio_id) if case.portfolio_id else None
    txn = Transaction.query.get(case.transaction_id) if case.transaction_id else None
    events = (
        CaseEvent.query.filter_by(case_id=case.id)
        .order_by(CaseEvent.timestamp.asc())
        .all()
    )

    # Narrative is what a SAR reviewer actually reads.
    narrative_lines = [
        f"Case #{case.id} — {case.title}",
        f"Opened {case.opened_at.isoformat() if case.opened_at else 'n/a'} by automated detection.",
        f"Current state: {case.state}, priority: {case.priority}.",
        f"Risk score at open: {case.risk_score}/100 ({case.risk_label}).",
    ]
    if case.flags:
        narrative_lines.append("Triggered detection flags: " + ", ".join(case.flags))
    if txn:
        narrative_lines.append(
            f"Subject transaction #{txn.id}: {txn.transaction_type} {txn.quantity} "
            f"{txn.symbol} @ {txn.price} (total {txn.total_amount:.2f}) on "
            f"{txn.timestamp.isoformat() if txn.timestamp else 'unknown'}."
        )
    if portfolio:
        narrative_lines.append(
            f"Subject account (portfolio): {portfolio.user_id} ({portfolio.name}), "
            f"balance {portfolio.cash_balance:.2f}, total value {portfolio.total_value:.2f}."
        )
    if case.ai_analysis:
        narrative_lines.append("AI analysis at open time is attached in section 5.")

    return {
        "filing_metadata": {
            "report_type": "SAR",
            "report_version": "2026-04",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "case_id": case.id,
            "tenant_id": case.tenant_id,
        },
        "subject": {
            "customer_ref": case.subject_user,
            "portfolio_id": portfolio.id if portfolio else None,
            "portfolio_name": portfolio.name if portfolio else None,
        },
        "suspicious_activity": {
            "title": case.title,
            "symbol": case.symbol,
            "amount": case.amount,
            "risk_score": case.risk_score,
            "risk_label": case.risk_label,
            "flags": case.flags or [],
            "state": case.state,
            "priority": case.priority,
            "opened_at": case.opened_at.isoformat() if case.opened_at else None,
            "closed_at": case.closed_at.isoformat() if case.closed_at else None,
        },
        "transaction": (
            {
                "id": txn.id,
                "type": txn.transaction_type,
                "symbol": txn.symbol,
                "quantity": txn.quantity,
                "price": txn.price,
                "total_amount": txn.total_amount,
                "fees": txn.fees,
                "timestamp": txn.timestamp.isoformat() if txn.timestamp else None,
                "notes": txn.notes,
            }
            if txn else None
        ),
        "narrative": "\n".join(narrative_lines),
        "timeline": [e.to_dict() for e in events],
        "ai_analysis": case.ai_analysis,
    }


# ─────────────────────────────────────────────────────────────────────
#  Endpoints
# ─────────────────────────────────────────────────────────────────────

@sar_bp.route("/sar/<int:case_id>.json", methods=["GET"])
@require_auth
def sar_json(case_id: int):
    case = _fetch_case(case_id)
    if not case:
        return jsonify({"error": "Case not found"}), 404
    payload = _build_sar_payload(case)
    audit.record(
        "sar.exported",
        resource="case",
        resource_id=str(case.id),
        details={"format": "json"},
    )
    return jsonify(payload), 200


@sar_bp.route("/sar/<int:case_id>.pdf", methods=["GET"])
@require_auth
def sar_pdf(case_id: int):
    case = _fetch_case(case_id)
    if not case:
        return jsonify({"error": "Case not found"}), 404

    try:
        pdf_bytes = _render_pdf(_build_sar_payload(case))
    except ImportError:
        # reportlab not installed — give the analyst a clear fallback.
        return jsonify({
            "error": "PDF export unavailable — reportlab not installed.",
            "hint": "pip install reportlab, or use /api/sar/<case_id>.json",
        }), 501

    audit.record(
        "sar.exported",
        resource="case",
        resource_id=str(case.id),
        details={"format": "pdf"},
    )
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"SAR_case_{case.id}.pdf",
    )


# ─────────────────────────────────────────────────────────────────────
#  PDF rendering (reportlab)
# ─────────────────────────────────────────────────────────────────────

def _render_pdf(payload: dict) -> bytes:
    """Render the SAR worksheet as a simple PDF. Kept deliberately plain."""
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    )
    from reportlab.lib import colors

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=LETTER,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
        title=f"SAR Case #{payload['filing_metadata']['case_id']}",
    )
    styles = getSampleStyleSheet()
    h1 = styles["Heading1"]
    h2 = styles["Heading2"]
    body = styles["BodyText"]
    mono = ParagraphStyle(
        "mono", parent=body, fontName="Courier", fontSize=8, leading=10,
    )

    story = []
    meta = payload["filing_metadata"]
    sub = payload["subject"]
    sa = payload["suspicious_activity"]
    txn = payload["transaction"]

    story.append(Paragraph(
        f"Suspicious Activity Report — Case #{meta['case_id']}", h1
    ))
    story.append(Paragraph(
        f"Generated {meta['generated_at']} · Tenant {meta['tenant_id']}", body
    ))
    story.append(Spacer(1, 0.2 * inch))

    # Section 1: subject
    story.append(Paragraph("1. Subject", h2))
    story.append(_kv_table([
        ("Customer reference", sub.get("customer_ref") or "—"),
        ("Portfolio ID", sub.get("portfolio_id") or "—"),
        ("Portfolio name", sub.get("portfolio_name") or "—"),
    ]))
    story.append(Spacer(1, 0.15 * inch))

    # Section 2: suspicious activity summary
    story.append(Paragraph("2. Suspicious Activity", h2))
    story.append(_kv_table([
        ("Title", sa.get("title")),
        ("Symbol", sa.get("symbol") or "—"),
        ("Amount", sa.get("amount") or "—"),
        ("Risk score", f"{sa.get('risk_score')}/100 ({sa.get('risk_label')})"),
        ("Flags", ", ".join(sa.get("flags") or []) or "—"),
        ("State", sa.get("state")),
        ("Priority", sa.get("priority")),
        ("Opened", sa.get("opened_at") or "—"),
        ("Closed", sa.get("closed_at") or "—"),
    ]))
    story.append(Spacer(1, 0.15 * inch))

    # Section 3: transaction
    story.append(Paragraph("3. Subject Transaction", h2))
    if txn:
        story.append(_kv_table([
            ("Transaction ID", txn.get("id")),
            ("Type", txn.get("type")),
            ("Symbol", txn.get("symbol")),
            ("Quantity", txn.get("quantity")),
            ("Price", txn.get("price")),
            ("Total amount", txn.get("total_amount")),
            ("Fees", txn.get("fees")),
            ("Timestamp", txn.get("timestamp")),
            ("Notes", txn.get("notes") or "—"),
        ]))
    else:
        story.append(Paragraph("No transaction associated with this case.", body))
    story.append(Spacer(1, 0.15 * inch))

    # Section 4: narrative
    story.append(Paragraph("4. Narrative", h2))
    for line in (payload.get("narrative") or "").split("\n"):
        story.append(Paragraph(line, body))
    story.append(Spacer(1, 0.15 * inch))

    # Section 5: AI analysis
    if payload.get("ai_analysis"):
        story.append(Paragraph("5. AI Analysis (at open time)", h2))
        for chunk in payload["ai_analysis"].split("\n"):
            story.append(Paragraph(chunk or " ", mono))
        story.append(Spacer(1, 0.15 * inch))

    # Section 6: timeline
    story.append(PageBreak())
    story.append(Paragraph("6. Case Timeline", h2))
    rows = [["Time", "Actor", "Event", "Detail"]]
    for ev in payload.get("timeline") or []:
        rows.append([
            ev.get("timestamp") or "",
            ev.get("actor_email") or "system",
            ev.get("event_type") or "",
            (ev.get("body") or "")[:120],
        ])
    if len(rows) > 1:
        t = Table(rows, colWidths=[1.4 * inch, 1.6 * inch, 1.2 * inch, 2.8 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No timeline entries.", body))

    doc.build(story)
    return buf.getvalue()


def _kv_table(rows):
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    data = [[str(k), str(v) if v is not None else "—"] for k, v in rows]
    t = Table(data, colWidths=[1.6 * inch, 5.0 * inch])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t
