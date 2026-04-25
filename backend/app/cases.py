"""
Case management for FinGuard Agent.

Cases are the analyst-facing workspace for investigating suspicious
transactions/alerts. One case ≈ one investigation. The state machine in
models.CASE_TRANSITIONS enforces legal transitions (new → under_review →
escalated → closed_*). Every mutation:

  1. writes a CaseEvent (timeline row), and
  2. records an AuditLog entry (hash-chained, tamper-evident)

so a supervisor can always reconstruct who did what and when.

Role policy:
  - analyst:    open, view, assign to self, add notes, transition to
                under_review / closed_cleared / closed_false_positive
  - supervisor: everything analyst can do + escalate, close_sar_filed,
                reassign to others
  - admin:      supervisor + (future) destructive ops

Tenancy: cases are strictly tenant-scoped. A user can never see cases from
another tenant, even with a guessed id.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from flask import Blueprint, request, jsonify, g
from sqlalchemy import or_, func

from app import db
from app.auth import (
    require_auth,
    require_role,
    current_user,
    current_tenant_id,
    ROLE_RANK,
)
from app import audit
from models.models import (
    Case,
    CaseEvent,
    CASE_STATES,
    CASE_TRANSITIONS,
    User,
    Portfolio,
    Asset,
    Transaction,
    Alert,
)

logger = logging.getLogger(__name__)

cases_bp = Blueprint("cases", __name__)


# Which roles are allowed to drive each transition.
# Anything not listed here requires supervisor+.
_ANALYST_ALLOWED = {
    ("new", "under_review"),
    ("new", "closed_false_positive"),
    ("new", "closed_cleared"),
    ("under_review", "closed_cleared"),
    ("under_review", "closed_false_positive"),
}

_TERMINAL_STATES = {"closed_cleared", "closed_sar_filed", "closed_false_positive"}

# Priority → SLA in hours (when the case is due).
_SLA_HOURS = {"critical": 4, "high": 12, "medium": 48, "low": 120}


# ─────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────

def _risk_label(score: int) -> str:
    if score >= 80:
        return "critical"
    if score >= 55:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


def _priority_from_label(label: str) -> str:
    return {"critical": "critical", "high": "high", "medium": "medium", "low": "low"}.get(label, "medium")


def _sla_due(priority: str, opened_at: datetime) -> datetime:
    return opened_at + timedelta(hours=_SLA_HOURS.get(priority, 48))


def _tenant_case_or_404(case_id: int) -> Optional[Case]:
    """Fetch a case scoped to the current tenant, or return None."""
    tid = current_tenant_id()
    q = Case.query.filter(Case.id == case_id)
    if tid is not None:
        q = q.filter(Case.tenant_id == tid)
    return q.first()


def _log_event(
    case: Case,
    event_type: str,
    *,
    body: Optional[str] = None,
    data: Optional[dict] = None,
    from_state: Optional[str] = None,
    to_state: Optional[str] = None,
) -> CaseEvent:
    u = current_user()
    ev = CaseEvent(
        case_id=case.id,
        event_type=event_type,
        actor_user_id=u.id if u else None,
        actor_email=u.email if u else None,
        from_state=from_state,
        to_state=to_state,
        body=body,
        data=data or {},
    )
    db.session.add(ev)
    return ev


def open_case_for_transaction(
    *,
    tenant_id: int,
    transaction: Transaction,
    portfolio: Optional[Portfolio],
    risk_score: int,
    flags: list,
    ai_analysis: Optional[str] = None,
    alert: Optional[Alert] = None,
) -> Optional[Case]:
    """
    Auto-open a case when a transaction comes in above the risk threshold.

    Called from the transaction endpoint. Returns None when score is below
    the open-case threshold (we only want cases for things worth reviewing).
    """
    if risk_score < 55:
        return None

    label = _risk_label(risk_score)
    priority = _priority_from_label(label)
    now = datetime.utcnow()
    subject = portfolio.user_id if portfolio else None

    case = Case(
        tenant_id=tenant_id,
        portfolio_id=portfolio.id if portfolio else None,
        transaction_id=transaction.id,
        alert_id=alert.id if alert else None,
        title=f"Review {transaction.symbol} {transaction.transaction_type} — {label}",
        subject_user=subject,
        symbol=transaction.symbol,
        amount=transaction.total_amount,
        risk_score=risk_score,
        risk_label=label,
        flags=flags or [],
        state="new",
        priority=priority,
        opened_at=now,
        sla_due_at=_sla_due(priority, now),
        ai_analysis=ai_analysis,
    )
    db.session.add(case)
    db.session.flush()  # need case.id for the event + audit row

    ev = CaseEvent(
        case_id=case.id,
        event_type="auto_opened",
        from_state=None,
        to_state="new",
        body=f"Auto-opened from transaction #{transaction.id} (score={risk_score}).",
        data={"flags": flags, "risk_score": risk_score, "risk_label": label},
    )
    db.session.add(ev)

    audit.record(
        "case.opened",
        resource="case",
        resource_id=str(case.id),
        details={
            "auto": True,
            "transaction_id": transaction.id,
            "risk_score": risk_score,
            "flags": flags,
        },
        tenant_id=tenant_id,
        commit=False,
    )
    return case


# ─────────────────────────────────────────────────────────────────────
#  Queue / detail
# ─────────────────────────────────────────────────────────────────────

@cases_bp.route("/cases", methods=["GET"])
@require_auth
def list_cases():
    """
    Analyst queue. Filters: state, priority, assignee (me/unassigned/<id>),
    q (matches title, subject_user, symbol). Ordered newest-first by default.
    """
    tid = current_tenant_id()
    q = Case.query.filter_by(tenant_id=tid)

    state = request.args.get("state")
    priority = request.args.get("priority")
    assignee = request.args.get("assignee")
    search = request.args.get("q")

    if state:
        if state == "open":
            q = q.filter(~Case.state.in_(list(_TERMINAL_STATES)))
        else:
            q = q.filter(Case.state == state)
    if priority:
        q = q.filter(Case.priority == priority)
    if assignee == "me":
        u = current_user()
        q = q.filter(Case.assignee_id == (u.id if u else -1))
    elif assignee == "unassigned":
        q = q.filter(Case.assignee_id.is_(None))
    elif assignee and assignee.isdigit():
        q = q.filter(Case.assignee_id == int(assignee))
    if search:
        pat = f"%{search}%"
        q = q.filter(or_(
            Case.title.ilike(pat),
            Case.subject_user.ilike(pat),
            Case.symbol.ilike(pat),
        ))

    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(max(int(request.args.get("per_page", 25)), 1), 200)
    except ValueError:
        return jsonify({"error": "page/per_page must be integers"}), 400

    total = q.count()
    rows = (
        q.order_by(Case.opened_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return jsonify({
        "page": page,
        "per_page": per_page,
        "total": total,
        "items": [c.to_dict() for c in rows],
    }), 200


@cases_bp.route("/cases/<int:case_id>", methods=["GET"])
@require_auth
def get_case(case_id: int):
    case = _tenant_case_or_404(case_id)
    if not case:
        return jsonify({"error": "Case not found"}), 404
    return jsonify(case.to_dict(include_events=True)), 200


# ─────────────────────────────────────────────────────────────────────
#  Manual open (analyst-initiated)
# ─────────────────────────────────────────────────────────────────────

@cases_bp.route("/cases", methods=["POST"])
@require_auth
def create_case():
    data = request.json or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400

    tid = current_tenant_id()
    priority = (data.get("priority") or "medium").lower()
    if priority not in _SLA_HOURS:
        return jsonify({"error": f"priority must be one of {list(_SLA_HOURS)}"}), 400

    now = datetime.utcnow()
    case = Case(
        tenant_id=tid,
        portfolio_id=data.get("portfolio_id"),
        transaction_id=data.get("transaction_id"),
        alert_id=data.get("alert_id"),
        title=title,
        subject_user=data.get("subject_user"),
        symbol=(data.get("symbol") or "").upper() or None,
        amount=data.get("amount"),
        risk_score=int(data.get("risk_score") or 0),
        risk_label=data.get("risk_label") or _risk_label(int(data.get("risk_score") or 0)),
        flags=data.get("flags") or [],
        state="new",
        priority=priority,
        opened_at=now,
        sla_due_at=_sla_due(priority, now),
        notes=data.get("notes"),
    )
    db.session.add(case)
    db.session.flush()

    _log_event(
        case, "opened",
        body=f"Manually opened by {current_user().email if current_user() else 'system'}.",
        to_state="new",
    )
    audit.record(
        "case.opened",
        resource="case",
        resource_id=str(case.id),
        details={"auto": False, "title": title, "priority": priority},
        commit=False,
    )
    db.session.commit()
    return jsonify(case.to_dict()), 201


# ─────────────────────────────────────────────────────────────────────
#  Mutations: assignment, notes, state transitions
# ─────────────────────────────────────────────────────────────────────

@cases_bp.route("/cases/<int:case_id>/assign", methods=["POST"])
@require_auth
def assign_case(case_id: int):
    """
    Assign a case. Analysts can self-assign only; supervisors+ can assign
    to anyone in their tenant.
    """
    case = _tenant_case_or_404(case_id)
    if not case:
        return jsonify({"error": "Case not found"}), 404
    if case.state in _TERMINAL_STATES:
        return jsonify({"error": "Cannot assign a closed case"}), 409

    data = request.json or {}
    u = current_user()
    assignee_id = data.get("assignee_id")

    if assignee_id in (None, "", "me"):
        assignee_id = u.id
    else:
        try:
            assignee_id = int(assignee_id)
        except (TypeError, ValueError):
            return jsonify({"error": "assignee_id must be an integer or 'me'"}), 400

    # Analysts can only self-assign.
    if ROLE_RANK.get(u.role, 0) < ROLE_RANK["supervisor"] and assignee_id != u.id:
        return jsonify({"error": "Analysts can only assign cases to themselves"}), 403

    assignee = User.query.filter_by(id=assignee_id, tenant_id=case.tenant_id).first()
    if not assignee:
        return jsonify({"error": "Assignee not found in this tenant"}), 404

    prev_id = case.assignee_id
    case.assignee_id = assignee.id

    _log_event(
        case, "assignment",
        body=f"Assigned to {assignee.email}.",
        data={"from_assignee_id": prev_id, "to_assignee_id": assignee.id},
    )
    audit.record(
        "case.assigned",
        resource="case",
        resource_id=str(case.id),
        details={"from": prev_id, "to": assignee.id},
        commit=False,
    )
    db.session.commit()
    return jsonify(case.to_dict()), 200


@cases_bp.route("/cases/<int:case_id>/notes", methods=["POST"])
@require_auth
def add_note(case_id: int):
    case = _tenant_case_or_404(case_id)
    if not case:
        return jsonify({"error": "Case not found"}), 404
    data = request.json or {}
    body = (data.get("body") or "").strip()
    if not body:
        return jsonify({"error": "body is required"}), 400

    _log_event(case, "note", body=body)
    audit.record(
        "case.note_added",
        resource="case",
        resource_id=str(case.id),
        details={"length": len(body)},
        commit=False,
    )
    db.session.commit()
    return jsonify({"ok": True}), 201


@cases_bp.route("/cases/<int:case_id>/transition", methods=["POST"])
@require_auth
def transition(case_id: int):
    """
    Drive the case state machine. Body: {"to_state": "...", "reason": "..."}.
    Enforces legal transitions from models.CASE_TRANSITIONS and role limits.
    """
    case = _tenant_case_or_404(case_id)
    if not case:
        return jsonify({"error": "Case not found"}), 404

    data = request.json or {}
    to_state = (data.get("to_state") or "").strip()
    reason = (data.get("reason") or "").strip()

    if to_state not in CASE_STATES:
        return jsonify({"error": f"to_state must be one of {CASE_STATES}"}), 400
    if case.state in _TERMINAL_STATES:
        return jsonify({"error": "Case is closed — no further transitions"}), 409
    allowed = CASE_TRANSITIONS.get(case.state, set())
    if to_state not in allowed:
        return jsonify({
            "error": "Illegal state transition",
            "from_state": case.state,
            "to_state": to_state,
            "allowed": sorted(allowed),
        }), 409

    # Role gate: supervisors+ for escalate & closed_sar_filed.
    u = current_user()
    rank = ROLE_RANK.get(u.role, 0)
    if (case.state, to_state) not in _ANALYST_ALLOWED and rank < ROLE_RANK["supervisor"]:
        return jsonify({
            "error": "This transition requires supervisor role",
            "from_state": case.state,
            "to_state": to_state,
        }), 403

    prev = case.state
    case.state = to_state
    if to_state in _TERMINAL_STATES:
        case.closed_at = datetime.utcnow()

    _log_event(
        case, "state_change",
        body=reason or None,
        from_state=prev,
        to_state=to_state,
    )
    audit.record(
        "case.state_changed",
        resource="case",
        resource_id=str(case.id),
        details={"from": prev, "to": to_state, "reason": reason},
        commit=False,
    )
    db.session.commit()
    return jsonify(case.to_dict()), 200


# ─────────────────────────────────────────────────────────────────────
#  Re-run AI analysis from inside a case  (closes gap #1)
# ─────────────────────────────────────────────────────────────────────

# Map of analyst-facing action → (orchestrator method name, event label).
# Kept explicit so the analyst picks from a known menu; we don't want
# arbitrary crew invocation from the case UI.
_ANALYZE_ACTIONS = {
    "risk":            ("quick_risk_assessment",        "Risk reassessment"),
    "compliance":      ("quick_compliance_review",      "Compliance review"),
    "portfolio":       ("quick_portfolio_analysis",     "Portfolio review"),
    "recommendation":  ("quick_portfolio_recommendation", "Lightweight recommendation"),
}


def _portfolio_dict(p: Optional[Portfolio]) -> dict:
    if not p:
        return {}
    return {
        "id": p.id,
        "user_id": p.user_id,
        "name": p.name,
        "total_value": p.total_value,
        "cash_balance": p.cash_balance,
    }


def _txn_dict(t: Transaction) -> dict:
    return {
        "id": t.id,
        "symbol": t.symbol,
        "transaction_type": t.transaction_type,
        "quantity": t.quantity,
        "price": t.price,
        "amount": t.total_amount,
        "fees": t.fees,
        "timestamp": t.timestamp.isoformat() if t.timestamp else None,
    }


@cases_bp.route("/cases/<int:case_id>/analyze", methods=["POST"])
@require_auth
def analyze_case(case_id: int):
    """
    Re-run one of the existing CrewAI crews against this case's subject and
    attach the result to the case timeline.

    Body: {"action": "risk" | "compliance" | "portfolio" | "recommendation"}
    """
    case = _tenant_case_or_404(case_id)
    if not case:
        return jsonify({"error": "Case not found"}), 404
    if case.state in _TERMINAL_STATES:
        return jsonify({"error": "Case is closed — re-run analysis before closing"}), 409

    data = request.json or {}
    action = (data.get("action") or "").strip().lower()
    if action not in _ANALYZE_ACTIONS:
        return jsonify({
            "error": "Unknown action",
            "allowed": sorted(_ANALYZE_ACTIONS),
        }), 400

    method_name, label = _ANALYZE_ACTIONS[action]

    # Pull the case's portfolio + a transaction window. If no portfolio is
    # attached we still try to service "risk" / "compliance" with just the
    # case's transaction; orchestrator is tolerant of thin inputs.
    portfolio = Portfolio.query.get(case.portfolio_id) if case.portfolio_id else None
    transactions = []
    if portfolio:
        recent = (
            Transaction.query.filter_by(portfolio_id=portfolio.id)
            .order_by(Transaction.timestamp.desc())
            .limit(20)
            .all()
        )
        transactions = [_txn_dict(t) for t in recent]
    elif case.transaction_id:
        t = Transaction.query.get(case.transaction_id)
        if t:
            transactions = [_txn_dict(t)]

    # Delegate to the agent-service over HTTP (non-blocking).
    # The frontend will open an SSE stream to get real-time thinking + results.
    from app.routes import _fire_agent
    import uuid
    
    stream_id = str(uuid.uuid4())
    
    # Map case analysis actions to agent-service endpoints
    endpoint_map = {
        "risk":          ("insights", {"transaction": {}, "score": 0, "factors": {}, "cleaned_input": f"Risk assessment for case {case.id}"}),
        "compliance":    ("insights", {"transaction": {}, "score": 0, "factors": {}, "cleaned_input": f"Compliance check for case {case.id}"}),
        "portfolio":     ("analyze", {"portfolio_data": _portfolio_dict(portfolio) if portfolio else {}, "transactions": transactions}),
        "recommendation":("quick-recommendation", {"portfolio_data": _portfolio_dict(portfolio) if portfolio else {}, "transactions": transactions}),
    }
    
    agent_endpoint, base_payload = endpoint_map.get(action, ("analyze", {}))
    
    # Add case context to payload
    payload = {
        "case_id": case.id,
        "action": action,
        "label": label,
        **base_payload
    }
    
    # Fire async job to agent-service
    _fire_agent(agent_endpoint, stream_id, payload)
    
    # Log that analysis was requested
    _log_event(
        case, "analysis_requested",
        body=f"Analysis requested: {label}",
        data={"action": action, "stream_id": stream_id, "endpoint": agent_endpoint},
    )
    
    audit.record(
        "case.analysis_requested",
        resource="case",
        resource_id=str(case.id),
        details={"action": action, "stream_id": stream_id, "endpoint": agent_endpoint},
        commit=False,
    )
    db.session.commit()
    
    # Return stream_id for frontend to connect via SSE
    return jsonify({
        "stream_id": stream_id,
        "action": action,
        "label": label,
    }), 202


@cases_bp.route("/cases/<int:case_id>/analyze/stream/<stream_id>", methods=["GET"])
@require_auth
def analyze_case_stream(case_id: int, stream_id: str):
    """
    Proxy SSE stream from agent-service for case analysis.
    Streams real-time agent thinking, crew updates, and final results.
    """
    from app.routes import _local_or_proxy_stream
    return _local_or_proxy_stream(stream_id)


# ─────────────────────────────────────────────────────────────────────
#  Customer 360  (closes gap #2)
# ─────────────────────────────────────────────────────────────────────

@cases_bp.route("/cases/<int:case_id>/customer-360", methods=["GET"])
@require_auth
def customer_360(case_id: int):
    """
    Aggregate view of the customer on this case: prior cases, transaction
    volume, alert history, current portfolio snapshot. Pure SQL — no LLM
    call — so it's fast and cheap to open every time the analyst loads a case.
    """
    case = _tenant_case_or_404(case_id)
    if not case:
        return jsonify({"error": "Case not found"}), 404

    tid = case.tenant_id
    subject = case.subject_user

    # 1) Prior cases on this same subject (tenant-scoped, excluding self).
    prior_q = Case.query.filter(Case.tenant_id == tid, Case.id != case.id)
    if subject:
        prior_q = prior_q.filter(Case.subject_user == subject)
    else:
        # Fall back to portfolio-linked cases so there's still *something* useful.
        prior_q = prior_q.filter(Case.portfolio_id == case.portfolio_id) if case.portfolio_id else prior_q.filter(False)

    prior_rows = prior_q.order_by(Case.opened_at.desc()).limit(25).all()

    # Bucket by state family for the summary header.
    def _bucket(state: str) -> str:
        if state in _TERMINAL_STATES:
            return state
        return "open"

    buckets: dict = {}
    for c in prior_rows:
        buckets[_bucket(c.state)] = buckets.get(_bucket(c.state), 0) + 1

    # 2) Portfolio snapshot + transaction aggregates (if we have a portfolio).
    portfolio = Portfolio.query.get(case.portfolio_id) if case.portfolio_id else None
    txn_summary = None
    recent_txns: list = []
    asset_rows: list = []
    alerts_count = 0
    if portfolio:
        agg = db.session.query(
            func.count(Transaction.id),
            func.coalesce(func.sum(Transaction.total_amount), 0.0),
            func.coalesce(func.avg(Transaction.total_amount), 0.0),
            func.coalesce(func.max(Transaction.total_amount), 0.0),
        ).filter(Transaction.portfolio_id == portfolio.id).first()

        txn_summary = {
            "count":        int(agg[0] or 0),
            "total_amount": float(agg[1] or 0.0),
            "avg_amount":   float(agg[2] or 0.0),
            "max_amount":   float(agg[3] or 0.0),
        }
        recent_txns = [
            _txn_dict(t) for t in
            Transaction.query.filter_by(portfolio_id=portfolio.id)
            .order_by(Transaction.timestamp.desc())
            .limit(10)
            .all()
        ]
        asset_rows = [
            {
                "symbol": a.symbol, "name": a.name, "quantity": a.quantity,
                "current_price": a.current_price, "asset_type": a.asset_type,
            }
            for a in Asset.query.filter_by(portfolio_id=portfolio.id).limit(25).all()
        ]
        alerts_count = Alert.query.filter_by(portfolio_id=portfolio.id).count()

    # 3) Frequency of detection flags across this subject's case history.
    flag_counts: dict = {}
    for c in prior_rows + [case]:
        for f in (c.flags or []):
            flag_counts[f] = flag_counts.get(f, 0) + 1

    return jsonify({
        "subject_user": subject,
        "summary": {
            "prior_case_count":       len(prior_rows),
            "state_buckets":          buckets,
            "sar_filed_count":        buckets.get("closed_sar_filed", 0),
            "false_positive_count":   buckets.get("closed_false_positive", 0),
            "open_case_count":        buckets.get("open", 0),
            "top_flags":              sorted(
                flag_counts.items(), key=lambda kv: -kv[1]
            )[:6],
        },
        "prior_cases": [
            {
                "id": c.id, "title": c.title, "state": c.state,
                "priority": c.priority, "risk_score": c.risk_score,
                "risk_label": c.risk_label,
                "opened_at": c.opened_at.isoformat() if c.opened_at else None,
                "closed_at": c.closed_at.isoformat() if c.closed_at else None,
            } for c in prior_rows
        ],
        "portfolio": _portfolio_dict(portfolio) if portfolio else None,
        "transaction_summary": txn_summary,
        "recent_transactions": recent_txns,
        "assets": asset_rows,
        "alerts_count": alerts_count,
    }), 200
