"""Legacy-compatible SAR export routes."""

from __future__ import annotations

import io
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response

from app.audit import record as record_audit
from app.auth import current_tenant_id, require_auth
from app.db import fetch_all, fetch_one


router = APIRouter()


def _fetch_case(request: Request, case_id: int) -> dict[str, Any]:
    row = fetch_one(
        "SELECT * FROM cases WHERE id = ? AND tenant_id = ?",
        (case_id, current_tenant_id(request)),
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return row


def _build_sar_payload(case: dict[str, Any]) -> dict[str, Any]:
    portfolio = (
        fetch_one("SELECT * FROM portfolios WHERE id = ?", (case["portfolio_id"],))
        if case.get("portfolio_id")
        else None
    )
    transaction = (
        fetch_one("SELECT * FROM transactions WHERE id = ?", (case["transaction_id"],))
        if case.get("transaction_id")
        else None
    )
    events = fetch_all(
        """
        SELECT id, event_type, actor_user_id, actor_email, from_state, to_state, body, data, timestamp
        FROM case_events
        WHERE case_id = ?
        ORDER BY COALESCE(timestamp, created_at) ASC, id ASC
        """,
        (case["id"],),
    )

    flags = json.loads(case.get("flags") or "[]")
    narrative_lines = [
        f"Case #{case['id']} - {case.get('title')}",
        f"Opened {case.get('opened_at') or 'n/a'} by automated detection.",
        f"Current state: {case.get('state')}, priority: {case.get('priority')}.",
        f"Risk score at open: {case.get('risk_score')}/100 ({case.get('risk_label')}).",
    ]
    if flags:
        narrative_lines.append("Triggered detection flags: " + ", ".join(flags))
    if transaction:
        narrative_lines.append(
            f"Subject transaction #{transaction['id']}: {transaction['transaction_type']} "
            f"{transaction['quantity']} {transaction['symbol']} @ {transaction['price']} "
            f"(total {transaction['total_amount']:.2f}) on {transaction['timestamp']}."
        )
    if portfolio:
        narrative_lines.append(
            f"Subject account (portfolio): {portfolio['user_id']} ({portfolio['name']}), "
            f"balance {portfolio['cash_balance']:.2f}, total value {portfolio['total_value']:.2f}."
        )
    if case.get("ai_analysis"):
        narrative_lines.append("AI analysis at open time is attached in section 5.")

    return {
        "filing_metadata": {
            "report_type": "SAR",
            "report_version": "2026-04",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "case_id": case["id"],
            "tenant_id": case.get("tenant_id"),
        },
        "subject": {
            "customer_ref": case.get("subject_user"),
            "portfolio_id": portfolio["id"] if portfolio else None,
            "portfolio_name": portfolio["name"] if portfolio else None,
        },
        "suspicious_activity": {
            "title": case.get("title"),
            "symbol": case.get("symbol"),
            "amount": case.get("amount"),
            "risk_score": case.get("risk_score"),
            "risk_label": case.get("risk_label"),
            "flags": flags,
            "state": case.get("state"),
            "priority": case.get("priority"),
            "opened_at": case.get("opened_at"),
            "closed_at": case.get("closed_at"),
        },
        "transaction": (
            {
                "id": transaction["id"],
                "type": transaction["transaction_type"],
                "symbol": transaction["symbol"],
                "quantity": transaction["quantity"],
                "price": transaction["price"],
                "total_amount": transaction["total_amount"],
                "fees": transaction["fees"],
                "timestamp": transaction["timestamp"],
                "notes": transaction["notes"],
            }
            if transaction
            else None
        ),
        "narrative": "\n".join(narrative_lines),
        "timeline": [
            {
                "id": event["id"],
                "event_type": event["event_type"],
                "actor_user_id": event.get("actor_user_id"),
                "actor_email": event.get("actor_email"),
                "from_state": event.get("from_state"),
                "to_state": event.get("to_state"),
                "body": event.get("body"),
                "data": json.loads(event.get("data") or "{}"),
                "timestamp": event.get("timestamp"),
            }
            for event in events
        ],
        "ai_analysis": case.get("ai_analysis"),
    }


@router.get("/api/sar/{case_id}.json")
def sar_json(case_id: int, request: Request) -> dict[str, Any]:
    require_auth(request)
    case = _fetch_case(request, case_id)
    payload = _build_sar_payload(case)
    record_audit(
        "sar.exported",
        request=request,
        resource="case",
        resource_id=str(case["id"]),
        details={"format": "json"},
    )
    return payload


@router.get("/api/sar/{case_id}.pdf")
def sar_pdf(case_id: int, request: Request) -> Response:
    require_auth(request)
    case = _fetch_case(request, case_id)
    try:
        pdf_bytes = _render_pdf(_build_sar_payload(case))
    except ImportError as exc:
        raise HTTPException(
            status_code=501,
            detail={
                "error": "PDF export unavailable - reportlab not installed.",
                "hint": "pip install reportlab, or use /api/sar/<case_id>.json",
            },
        ) from exc

    record_audit(
        "sar.exported",
        request=request,
        resource="case",
        resource_id=str(case["id"]),
        details={"format": "pdf"},
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="SAR_case_{case["id"]}.pdf"'
        },
    )


def _render_pdf(payload: dict[str, Any]) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title=f"SAR Case #{payload['filing_metadata']['case_id']}",
    )
    styles = getSampleStyleSheet()
    body = styles["BodyText"]
    mono = ParagraphStyle(
        "mono", parent=body, fontName="Courier", fontSize=8, leading=10
    )
    story: list[Any] = [
        Paragraph(
            f"Suspicious Activity Report - Case #{payload['filing_metadata']['case_id']}",
            styles["Heading1"],
        ),
        Paragraph(
            f"Generated {payload['filing_metadata']['generated_at']} - "
            f"Tenant {payload['filing_metadata']['tenant_id']}",
            body,
        ),
        Spacer(1, 0.2 * inch),
        Paragraph("1. Subject", styles["Heading2"]),
        _kv_table(
            [
                ("Customer reference", payload["subject"].get("customer_ref") or "-"),
                ("Portfolio ID", payload["subject"].get("portfolio_id") or "-"),
                ("Portfolio name", payload["subject"].get("portfolio_name") or "-"),
            ]
        ),
        Spacer(1, 0.15 * inch),
        Paragraph("2. Suspicious Activity", styles["Heading2"]),
        _kv_table(
            [
                ("Title", payload["suspicious_activity"].get("title")),
                ("Symbol", payload["suspicious_activity"].get("symbol") or "-"),
                ("Amount", payload["suspicious_activity"].get("amount") or "-"),
                (
                    "Risk score",
                    f"{payload['suspicious_activity'].get('risk_score')}/100 ({payload['suspicious_activity'].get('risk_label')})",
                ),
                (
                    "Flags",
                    ", ".join(payload["suspicious_activity"].get("flags") or []) or "-",
                ),
                ("State", payload["suspicious_activity"].get("state")),
                ("Priority", payload["suspicious_activity"].get("priority")),
                ("Opened", payload["suspicious_activity"].get("opened_at") or "-"),
                ("Closed", payload["suspicious_activity"].get("closed_at") or "-"),
            ]
        ),
        Spacer(1, 0.15 * inch),
        Paragraph("3. Subject Transaction", styles["Heading2"]),
    ]
    transaction = payload.get("transaction")
    if transaction:
        story.append(
            _kv_table(
                [
                    ("Transaction ID", transaction.get("id")),
                    ("Type", transaction.get("type")),
                    ("Symbol", transaction.get("symbol")),
                    ("Quantity", transaction.get("quantity")),
                    ("Price", transaction.get("price")),
                    ("Total amount", transaction.get("total_amount")),
                    ("Fees", transaction.get("fees")),
                    ("Timestamp", transaction.get("timestamp")),
                    ("Notes", transaction.get("notes") or "-"),
                ]
            )
        )
    else:
        story.append(Paragraph("No transaction associated with this case.", body))

    story.extend(
        [Spacer(1, 0.15 * inch), Paragraph("4. Narrative", styles["Heading2"])]
    )
    for line in (payload.get("narrative") or "").split("\n"):
        story.append(Paragraph(line, body))
    if payload.get("ai_analysis"):
        story.extend(
            [
                Spacer(1, 0.15 * inch),
                Paragraph("5. AI Analysis (at open time)", styles["Heading2"]),
            ]
        )
        for chunk in payload["ai_analysis"].split("\n"):
            story.append(Paragraph(chunk or " ", mono))

    story.extend([PageBreak(), Paragraph("6. Case Timeline", styles["Heading2"])])
    rows = [["Time", "Actor", "Event", "Detail"]]
    for event in payload.get("timeline") or []:
        rows.append(
            [
                event.get("timestamp") or "",
                event.get("actor_email") or "system",
                event.get("event_type") or "",
                (event.get("body") or "")[:120],
            ]
        )
    if len(rows) > 1:
        table = Table(rows, colWidths=[1.4 * inch, 1.6 * inch, 1.2 * inch, 2.8 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(table)
    else:
        story.append(Paragraph("No timeline entries.", body))
    doc.build(story)
    return buffer.getvalue()


def _kv_table(rows: list[tuple[str, Any]]) -> Any:
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import Table, TableStyle

    table = Table(
        [[str(key), str(value) if value is not None else "-"] for key, value in rows],
        colWidths=[1.6 * inch, 5.0 * inch],
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table
