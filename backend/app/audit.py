"""Hash-chained audit log helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from app.db import execute, fetch_all, fetch_one


def _canonical(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _row_payload(
    *,
    tenant_id: int | None,
    user_id: str | None,
    user_email: str | None,
    action: str,
    resource: str | None,
    resource_id: str | None,
    details: dict[str, Any] | None,
    ip_address: str | None,
    user_agent: str | None,
    timestamp: str,
) -> dict[str, Any]:
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
        "timestamp": timestamp,
    }


def _compute_hash(prev_hash: str, payload: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    digest.update((prev_hash or "").encode("utf-8"))
    digest.update(_canonical(payload).encode("utf-8"))
    return digest.hexdigest()


def _last_hash_for_tenant(tenant_id: int | None) -> str:
    if tenant_id is None:
        row = fetch_one("SELECT entry_hash FROM audit_logs ORDER BY id DESC LIMIT 1")
    else:
        row = fetch_one(
            "SELECT entry_hash FROM audit_logs WHERE tenant_id = ? ORDER BY id DESC LIMIT 1",
            (tenant_id,),
        )
    return str(row["entry_hash"]) if row and row.get("entry_hash") else ""


def record(
    action: str,
    *,
    request: Any | None = None,
    resource: str | None = None,
    resource_id: str | None = None,
    details: dict[str, Any] | None = None,
    tenant_id: int | None = None,
    user_id: str | None = None,
    user_email: str | None = None,
) -> int:
    if request is not None:
        from app.auth import current_tenant_id, current_user

        tenant_id = tenant_id if tenant_id is not None else current_tenant_id(request)
        user = current_user(request)
        if user is not None:
            user_id = user_id or str(user["id"])
            user_email = user_email or str(user["email"])
        ip_address = request.headers.get(
            "X-Forwarded-For", request.client.host if request.client else None
        )
        user_agent = request.headers.get("User-Agent")
    else:
        ip_address = None
        user_agent = None

    timestamp = datetime.utcnow().isoformat()
    payload = _row_payload(
        tenant_id=tenant_id,
        user_id=user_id,
        user_email=user_email,
        action=action,
        resource=resource,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
        timestamp=timestamp,
    )
    prev_hash = _last_hash_for_tenant(tenant_id)
    entry_hash = _compute_hash(prev_hash, payload)
    return execute(
        """
        INSERT INTO audit_logs (
            tenant_id, user_id, user_email, action, resource, resource_id,
            details, ip_address, user_agent, timestamp, prev_hash, entry_hash
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tenant_id,
            user_id,
            user_email,
            action,
            resource,
            resource_id,
            json.dumps(details or {}),
            ip_address,
            user_agent,
            timestamp,
            prev_hash,
            entry_hash,
        ),
    )


def verify_chain(tenant_id: int | None = None) -> dict[str, Any]:
    if tenant_id is None:
        rows = fetch_all("SELECT * FROM audit_logs ORDER BY id ASC")
    else:
        rows = fetch_all(
            "SELECT * FROM audit_logs WHERE tenant_id = ? ORDER BY id ASC", (tenant_id,)
        )

    prev_hash = ""
    for row in rows:
        payload = _row_payload(
            tenant_id=row.get("tenant_id"),
            user_id=row.get("user_id"),
            user_email=row.get("user_email"),
            action=row["action"],
            resource=row.get("resource"),
            resource_id=row.get("resource_id"),
            details=json.loads(row.get("details") or "{}"),
            ip_address=row.get("ip_address"),
            user_agent=row.get("user_agent"),
            timestamp=row["timestamp"],
        )
        expected_hash = _compute_hash(prev_hash, payload)
        if row.get("prev_hash") != prev_hash or row.get("entry_hash") != expected_hash:
            return {"ok": False, "checked": len(rows), "broken_at": row["id"]}
        prev_hash = row["entry_hash"]

    return {"ok": True, "checked": len(rows), "broken_at": None}


def row_to_dict(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "tenant_id": row.get("tenant_id"),
        "user_id": row.get("user_id"),
        "user_email": row.get("user_email"),
        "action": row["action"],
        "resource": row.get("resource"),
        "resource_id": row.get("resource_id"),
        "details": json.loads(row.get("details") or "{}"),
        "ip_address": row.get("ip_address"),
        "user_agent": row.get("user_agent"),
        "timestamp": row["timestamp"],
        "prev_hash": row.get("prev_hash"),
        "entry_hash": row.get("entry_hash"),
    }
