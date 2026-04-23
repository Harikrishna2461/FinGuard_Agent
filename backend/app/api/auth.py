"""Legacy-compatible auth routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.auth import (
    DEFAULT_TENANT_SLUG,
    auth_enforced,
    authenticate_user,
    current_tenant,
    current_user,
    issue_token,
    register_user,
    ttl_seconds,
    user_to_dict,
)
from app.db import fetch_one


router = APIRouter()


@router.post("/api/auth/register", status_code=201)
def register(request: Request, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    email = str(payload.get("email") or "").strip().lower()
    password = str(payload.get("password") or "")
    name = str(payload.get("name") or email)
    role = str(payload.get("role") or "analyst").lower()
    tenant_slug = str(payload.get("tenant_slug") or DEFAULT_TENANT_SLUG).lower()

    if not email or not password:
        raise HTTPException(status_code=400, detail="email and password required")

    any_user = fetch_one("SELECT id FROM users LIMIT 1")
    existing_user = current_user(request)
    if any_user is not None and (
        existing_user is None or str(existing_user["role"]) != "admin"
    ):
        raise HTTPException(
            status_code=403, detail="Only admins can register new users"
        )

    return user_to_dict(
        register_user(
            email=email,
            password=password,
            name=name,
            role=role,
            tenant_slug=tenant_slug,
            tenant_name=payload.get("tenant_name"),
        )
    )


@router.post("/api/auth/login")
def login(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    email = str(payload.get("email") or "").strip().lower()
    password = str(payload.get("password") or "")
    user = authenticate_user(email, password)
    return {
        "token": issue_token(user),
        "token_type": "Bearer",
        "expires_in": ttl_seconds(),
        "user": user_to_dict(user),
    }


@router.get("/api/auth/me")
def me(request: Request) -> dict[str, Any]:
    user = current_user(request)
    tenant = current_tenant(request)
    return {
        "authenticated": user is not None,
        "auth_enforced": auth_enforced(),
        "user": user_to_dict(user) if user else None,
        "tenant": (
            {"id": tenant["id"], "slug": tenant["slug"], "name": tenant["name"]}
            if tenant
            else None
        ),
    }
