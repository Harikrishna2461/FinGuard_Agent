"""Legacy-compatible audit routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.audit import row_to_dict, verify_chain
from app.auth import current_tenant_id, require_auth, require_role
from app.db import fetch_all, fetch_one


router = APIRouter()


@router.get("/api/audit/logs")
def list_logs(
    request: Request,
    page: int = 1,
    per_page: int = 50,
    action: str | None = None,
    resource: str | None = None,
    resource_id: str | None = None,
) -> dict[str, Any]:
    require_auth(request)
    if page < 1 or per_page < 1:
        raise HTTPException(status_code=400, detail="page/per_page must be integers")
    per_page = min(per_page, 500)

    query = "SELECT * FROM audit_logs WHERE tenant_id = ?"
    params: list[Any] = [current_tenant_id(request)]
    if action:
        query += " AND action = ?"
        params.append(action)
    if resource:
        query += " AND resource = ?"
        params.append(resource)
    if resource_id:
        query += " AND resource_id = ?"
        params.append(resource_id)

    total_row = fetch_one(f"SELECT COUNT(*) AS count FROM ({query})", tuple(params))
    rows = fetch_all(
        query + " ORDER BY id DESC LIMIT ? OFFSET ?",
        tuple(params + [per_page, (page - 1) * per_page]),
    )
    return {
        "page": page,
        "per_page": per_page,
        "total": int(total_row["count"]) if total_row else 0,
        "items": [row_to_dict(row) for row in rows],
    }


@router.get("/api/audit/verify")
def verify(request: Request) -> dict[str, Any]:
    require_role(request, "supervisor")
    result = verify_chain(current_tenant_id(request))
    if not result["ok"]:
        raise HTTPException(status_code=409, detail=result)
    return result
