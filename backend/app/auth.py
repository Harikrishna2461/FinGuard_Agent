"""Legacy-compatible auth helpers for the FastAPI backend."""

from __future__ import annotations

import os
import time
from typing import Any

import jwt
from fastapi import HTTPException, Request
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import execute, fetch_one


DEFAULT_TENANT_SLUG = "default"
SYSTEM_USER_EMAIL = "system@default.local"
ROLES = ("analyst", "supervisor", "admin")
ROLE_RANK = {"analyst": 1, "supervisor": 2, "admin": 3}


def _secret() -> str:
    return os.getenv("JWT_SECRET") or "finguard-dev-secret-change-in-production"


def ttl_seconds() -> int:
    return int(os.getenv("JWT_TTL_SECONDS", "43200"))


def auth_enforced() -> bool:
    return str(os.getenv("AUTH_ENFORCED", "false")).lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def issue_token(user: dict[str, Any]) -> str:
    now = int(time.time())
    payload = {
        "sub": str(user["id"]),
        "tenant_id": user["tenant_id"],
        "email": user["email"],
        "role": user["role"],
        "iat": now,
        "exp": now + ttl_seconds(),
    }
    return jwt.encode(payload, _secret(), algorithm="HS256")


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, _secret(), algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def _extract_bearer(request: Request) -> str | None:
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return None


def _tenant_by_slug(slug: str) -> dict[str, Any] | None:
    return fetch_one("SELECT * FROM tenants WHERE slug = ?", (slug,))


def _tenant_by_id(tenant_id: int) -> dict[str, Any] | None:
    return fetch_one("SELECT * FROM tenants WHERE id = ?", (tenant_id,))


def _user_by_id(user_id: int) -> dict[str, Any] | None:
    return fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))


def _user_by_email(email: str) -> dict[str, Any] | None:
    return fetch_one("SELECT * FROM users WHERE email = ?", (email,))


def _create_tenant(slug: str, name: str) -> dict[str, Any]:
    tenant_id = execute(
        """
        INSERT INTO tenants (slug, name, created_at)
        VALUES (?, ?, datetime('now'))
        """,
        (slug, name),
    )
    tenant = _tenant_by_id(tenant_id)
    if tenant is None:
        raise RuntimeError("tenant missing after insert")
    return tenant


def user_to_dict(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user["id"],
        "tenant_id": user["tenant_id"],
        "email": user["email"],
        "name": user.get("name"),
        "role": user["role"],
        "is_active": bool(user["is_active"]),
    }


def _ensure_system_user(tenant: dict[str, Any]) -> dict[str, Any]:
    user = _user_by_email(SYSTEM_USER_EMAIL)
    if user is not None:
        return user
    user_id = execute(
        """
        INSERT INTO users (
            tenant_id, email, password_hash, name, role, is_active, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (
            tenant["id"],
            SYSTEM_USER_EMAIL,
            "!",
            "System (demo)",
            "admin",
            1,
        ),
    )
    user = _user_by_id(user_id)
    if user is None:
        raise RuntimeError("system user missing after insert")
    return user


def resolve_identity(
    request: Request,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    token = _extract_bearer(request)
    if token:
        payload = decode_token(token)
        if payload:
            user = _user_by_id(int(payload["sub"]))
            if user and bool(user["is_active"]):
                tenant = _tenant_by_id(int(user["tenant_id"]))
                if tenant is not None:
                    return user, tenant

    if auth_enforced():
        return None, None

    tenant = _tenant_by_slug(DEFAULT_TENANT_SLUG)
    if tenant is None:
        tenant = _create_tenant(DEFAULT_TENANT_SLUG, "Default")
    return _ensure_system_user(tenant), tenant


def get_request_identity(
    request: Request,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    user = getattr(request.state, "current_user", None)
    tenant = getattr(request.state, "current_tenant", None)
    if user is None and tenant is None:
        user, tenant = resolve_identity(request)
        request.state.current_user = user
        request.state.current_tenant = tenant
    return user, tenant


def current_user(request: Request) -> dict[str, Any] | None:
    user, _ = get_request_identity(request)
    return user


def current_tenant(request: Request) -> dict[str, Any] | None:
    _, tenant = get_request_identity(request)
    return tenant


def current_tenant_id(request: Request) -> int | None:
    tenant = current_tenant(request)
    return int(tenant["id"]) if tenant else None


def require_auth(request: Request) -> dict[str, Any]:
    user = current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_role(request: Request, min_role: str) -> dict[str, Any]:
    user = require_auth(request)
    if ROLE_RANK.get(str(user["role"]), 0) < ROLE_RANK[min_role]:
        raise HTTPException(
            status_code=403,
            detail={"error": "Forbidden", "detail": f"Requires role >= {min_role}"},
        )
    return user


def register_user(
    *,
    email: str,
    password: str,
    name: str,
    role: str,
    tenant_slug: str,
    tenant_name: str | None = None,
) -> dict[str, Any]:
    if role not in ROLES:
        raise HTTPException(status_code=400, detail=f"role must be one of {ROLES}")
    if _user_by_email(email):
        raise HTTPException(status_code=409, detail="email already registered")

    tenant = _tenant_by_slug(tenant_slug)
    if tenant is None:
        tenant = _create_tenant(tenant_slug, tenant_name or tenant_slug.title())

    user_id = execute(
        """
        INSERT INTO users (
            tenant_id, email, password_hash, name, role, is_active, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (
            tenant["id"],
            email,
            generate_password_hash(password),
            name,
            role,
            1,
        ),
    )
    user = _user_by_id(user_id)
    if user is None:
        raise RuntimeError("user missing after insert")
    return user


def authenticate_user(email: str, password: str) -> dict[str, Any]:
    user = _user_by_email(email)
    if (
        not user
        or not bool(user["is_active"])
        or not check_password_hash(str(user["password_hash"]), password)
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    execute(
        "UPDATE users SET last_login = datetime('now') WHERE id = ?",
        (user["id"],),
    )
    refreshed = _user_by_id(int(user["id"]))
    if refreshed is None:
        raise RuntimeError("user missing after login update")
    return refreshed
