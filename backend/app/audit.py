"""
Append-only, hash-chained audit log for FinGuard Agent.

Each AuditLog row stores:
    entry_hash = SHA-256(prev_hash || canonical_json(payload))

where `payload` is a deterministic dict of the row's fields. The first row in
a tenant's chain has prev_hash = "" (empty string), so the whole chain is
self-anchoring. Tampering with any historical row — or reordering them —
invalidates the chain from that row forward, which `verify_chain()` detects.

Why not just rely on the DB's append-only intent?
- A compromised DB could still rewrite rows silently. The hash chain makes
  tampering *detectable* without a separate WORM store, which is enough for
  our target segment (small neobanks / payment fintechs doing FinCEN SAR
  filings). It's not a cryptographic notary, but it's materially better
  than "trust the DB".
"""

from __future__ import annotations

import json
import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, Optional, List

from flask import Blueprint, request, jsonify, g

from app import db
from app.auth import require_auth, require_role, current_user, current_tenant_id
from models.models import AuditLog

logger = logging.getLogger(__name__)

audit_bp = Blueprint("audit", __name__)


# ─────────────────────────────────────────────────────────────────────
#  Hash chain primitives
# ─────────────────────────────────────────────────────────────────────

def _canonical(payload: Dict[str, Any]) -> str:
    """Deterministic JSON for hashing — sorted keys, no whitespace."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _row_payload(
    *,
    tenant_id: Optional[int],
    user_id: Optional[str],
    user_email: Optional[str],
    action: str,
    resource: Optional[str],
    resource_id: Optional[str],
    details: Optional[dict],
    ip_address: Optional[str],
    user_agent: Optional[str],
    timestamp: datetime,
) -> Dict[str, Any]:
    return {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "user_email": user_email,
        "action": action,
        "resource": resource,
        "resource_id": resource_id,
        "details": details or {},
        "ip_address": ip_address,
        "user_agent": user_agent,
        "timestamp": timestamp.isoformat(),
    }


def _compute_hash(prev_hash: str, payload: Dict[str, Any]) -> str:
    h = hashlib.sha256()
    h.update((prev_hash or "").encode("utf-8"))
    h.update(_canonical(payload).encode("utf-8"))
    return h.hexdigest()


def _last_hash_for_tenant(tenant_id: Optional[int]) -> str:
    """Tail hash for a tenant's chain, or "" if empty."""
    q = AuditLog.query
    if tenant_id is not None:
        q = q.filter_by(tenant_id=tenant_id)
    last = q.order_by(AuditLog.id.desc()).first()
    return last.entry_hash if last and last.entry_hash else ""


# ─────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────

def record(
    action: str,
    *,
    resource: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[dict] = None,
    tenant_id: Optional[int] = None,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    commit: bool = True,
) -> AuditLog:
    """
    Append a hash-chained audit entry.

    Pulls tenant/user from Flask `g` if not passed explicitly so callers can
    just write `audit.record("case.created", resource="case", resource_id=str(c.id))`.
    """
    if tenant_id is None:
        tenant_id = current_tenant_id()
    if user_id is None or user_email is None:
        u = current_user()
        if u is not None:
            user_id = user_id or str(u.id)
            user_email = user_email or u.email

    ip = None
    ua = None
    try:
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        ua = request.headers.get("User-Agent")
    except RuntimeError:
        # Outside request context (e.g., background job) — skip transport metadata.
        pass

    ts = datetime.utcnow()
    payload = _row_payload(
        tenant_id=tenant_id,
        user_id=user_id,
        user_email=user_email,
        action=action,
        resource=resource,
        resource_id=resource_id,
        details=details,
        ip_address=ip,
        user_agent=ua,
        timestamp=ts,
    )
    prev = _last_hash_for_tenant(tenant_id)
    entry_hash = _compute_hash(prev, payload)

    row = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        user_email=user_email,
        action=action,
        resource=resource,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip,
        user_agent=ua,
        timestamp=ts,
        prev_hash=prev,
        entry_hash=entry_hash,
    )
    db.session.add(row)
    if commit:
        db.session.commit()
    return row


def verify_chain(tenant_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Walk a tenant's audit chain and validate each entry_hash.

    Returns {"ok": bool, "checked": int, "broken_at": Optional[int]}.
    """
    q = AuditLog.query
    if tenant_id is not None:
        q = q.filter_by(tenant_id=tenant_id)
    rows: List[AuditLog] = q.order_by(AuditLog.id.asc()).all()

    prev = ""
    for r in rows:
        payload = _row_payload(
            tenant_id=r.tenant_id,
            user_id=r.user_id,
            user_email=r.user_email,
            action=r.action,
            resource=r.resource,
            resource_id=r.resource_id,
            details=r.details,
            ip_address=r.ip_address,
            user_agent=r.user_agent,
            timestamp=r.timestamp,
        )
        expected = _compute_hash(prev, payload)
        if r.prev_hash != prev or r.entry_hash != expected:
            return {"ok": False, "checked": len(rows), "broken_at": r.id}
        prev = r.entry_hash

    return {"ok": True, "checked": len(rows), "broken_at": None}


def _row_to_dict(r: AuditLog) -> dict:
    return {
        "id": r.id,
        "tenant_id": r.tenant_id,
        "user_id": r.user_id,
        "user_email": r.user_email,
        "action": r.action,
        "resource": r.resource,
        "resource_id": r.resource_id,
        "details": r.details,
        "ip_address": r.ip_address,
        "user_agent": r.user_agent,
        "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        "prev_hash": r.prev_hash,
        "entry_hash": r.entry_hash,
    }


# ─────────────────────────────────────────────────────────────────────
#  Endpoints
# ─────────────────────────────────────────────────────────────────────

@audit_bp.route("/audit/logs", methods=["GET"])
@require_auth
def list_logs():
    """Paginated, tenant-scoped audit trail. Analysts+ can read their own tenant's chain."""
    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(max(int(request.args.get("per_page", 50)), 1), 500)
    except ValueError:
        return jsonify({"error": "page/per_page must be integers"}), 400

    action = request.args.get("action")
    resource = request.args.get("resource")
    resource_id = request.args.get("resource_id")

    q = AuditLog.query.filter_by(tenant_id=current_tenant_id())
    if action:
        q = q.filter(AuditLog.action == action)
    if resource:
        q = q.filter(AuditLog.resource == resource)
    if resource_id:
        q = q.filter(AuditLog.resource_id == resource_id)

    total = q.count()
    rows = (
        q.order_by(AuditLog.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return jsonify({
        "page": page,
        "per_page": per_page,
        "total": total,
        "items": [_row_to_dict(r) for r in rows],
    }), 200


@audit_bp.route("/audit/verify", methods=["GET"])
@require_role("supervisor")
def verify():
    """Chain-integrity check for the caller's tenant. Supervisor+."""
    result = verify_chain(current_tenant_id())
    status = 200 if result["ok"] else 409
    return jsonify(result), status
