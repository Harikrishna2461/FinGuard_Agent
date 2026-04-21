"""
Authentication for FinGuard Agent.

Design notes:
- JWT bearer tokens issued at login. Payload carries user_id, tenant_id, role.
- Auth enforcement is *opt-in* via the AUTH_ENFORCED config flag. Off by
  default so the existing portfolio-side API keeps working without any
  client changes; turn it on for the case-ops endpoints where we need
  identity and tenant isolation.
- Three roles: analyst (read + triage), supervisor (+ escalate/close),
  admin (+ manage users, purge, SAR filing).
"""

from __future__ import annotations

import os
import time
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Tuple

from flask import Blueprint, request, jsonify, current_app, g
from werkzeug.security import generate_password_hash, check_password_hash

import jwt

from app import db
from models.models import User, Tenant, DEFAULT_TENANT_SLUG

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)

ROLES = ("analyst", "supervisor", "admin")
ROLE_RANK = {"analyst": 1, "supervisor": 2, "admin": 3}


# ─────────────────────────────────────────────────────────────────────
#  Token helpers
# ─────────────────────────────────────────────────────────────────────

def _secret() -> str:
    return (
        current_app.config.get("JWT_SECRET")
        or os.getenv("JWT_SECRET")
        or current_app.config.get("SECRET_KEY")
        or "finguard-dev-secret-change-in-production"
    )


def _ttl_seconds() -> int:
    return int(os.getenv("JWT_TTL_SECONDS", "43200"))  # 12h default


def issue_token(user: User) -> str:
    now = int(time.time())
    payload = {
        "sub": str(user.id),
        "tenant_id": user.tenant_id,
        "email": user.email,
        "role": user.role,
        "iat": now,
        "exp": now + _ttl_seconds(),
    }
    return jwt.encode(payload, _secret(), algorithm="HS256")


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, _secret(), algorithms=["HS256"])
    except jwt.PyJWTError as e:
        logger.debug("JWT decode failed: %s", e)
        return None


def _auth_enforced() -> bool:
    """Is auth required on protected endpoints?"""
    val = current_app.config.get("AUTH_ENFORCED")
    if val is None:
        val = os.getenv("AUTH_ENFORCED", "false")
    return str(val).lower() in ("1", "true", "yes", "on")


# ─────────────────────────────────────────────────────────────────────
#  Request context resolver
# ─────────────────────────────────────────────────────────────────────

def _extract_bearer() -> Optional[str]:
    h = request.headers.get("Authorization", "")
    if h.lower().startswith("bearer "):
        return h[7:].strip()
    return None


SYSTEM_USER_EMAIL = "system@default.local"


def _get_or_create_system_user(tenant: Tenant) -> User:
    """Built-in demo user so the UI works without AUTH_ENFORCED."""
    u = User.query.filter_by(email=SYSTEM_USER_EMAIL).first()
    if u is None:
        u = User(
            tenant_id=tenant.id,
            email=SYSTEM_USER_EMAIL,
            password_hash="!",  # unusable — login cannot succeed via this path
            name="System (demo)",
            role="admin",
            is_active=True,
        )
        db.session.add(u)
        db.session.commit()
    return u


def resolve_identity() -> Tuple[Optional[User], Optional[Tenant]]:
    """
    Resolve (user, tenant) for the current request.

    - If a valid Bearer token is provided, use it.
    - Otherwise, when auth is not enforced, fall back to the default tenant
      and a built-in system user so the Cases / SAR / audit endpoints work
      for demos without forcing a login flow.
    - When auth IS enforced and no valid token, returns (None, None) and the
      caller is expected to 401.
    """
    token = _extract_bearer()
    if token:
        payload = decode_token(token)
        if payload:
            user = db.session.get(User, int(payload["sub"]))
            if user and user.is_active:
                tenant = db.session.get(Tenant, user.tenant_id)
                return user, tenant

    if _auth_enforced():
        return None, None

    tenant = Tenant.query.filter_by(slug=DEFAULT_TENANT_SLUG).first()
    if tenant is None:
        return None, None
    return _get_or_create_system_user(tenant), tenant


def _attach_to_g(user: Optional[User], tenant: Optional[Tenant]) -> None:
    g.current_user = user
    g.current_tenant = tenant


def current_user() -> Optional[User]:
    return getattr(g, "current_user", None)


def current_tenant() -> Optional[Tenant]:
    return getattr(g, "current_tenant", None)


def current_tenant_id() -> Optional[int]:
    t = current_tenant()
    return t.id if t else None


# ─────────────────────────────────────────────────────────────────────
#  Decorators for protected routes
# ─────────────────────────────────────────────────────────────────────

def _ensure_context_resolved():
    if not hasattr(g, "current_user") and not hasattr(g, "current_tenant"):
        u, t = resolve_identity()
        _attach_to_g(u, t)


def require_auth(fn):
    """Route guard: requires a valid JWT. Returns 401 otherwise."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        _ensure_context_resolved()
        if current_user() is None:
            return jsonify({"error": "Authentication required"}), 401
        return fn(*args, **kwargs)
    return wrapper


def require_role(min_role: str):
    """Route guard: requires a JWT with role >= min_role."""
    assert min_role in ROLE_RANK, f"Unknown role {min_role!r}"

    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            _ensure_context_resolved()
            u = current_user()
            if u is None:
                return jsonify({"error": "Authentication required"}), 401
            if ROLE_RANK.get(u.role, 0) < ROLE_RANK[min_role]:
                return jsonify({
                    "error": "Forbidden",
                    "detail": f"Requires role >= {min_role}",
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return deco


# ─────────────────────────────────────────────────────────────────────
#  Auth endpoints
# ─────────────────────────────────────────────────────────────────────

@auth_bp.route("/auth/register", methods=["POST"])
def register():
    """Create a user under a tenant. Admin-only unless this is the very first user."""
    data = request.json or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name = data.get("name") or email
    role = (data.get("role") or "analyst").lower()
    tenant_slug = (data.get("tenant_slug") or DEFAULT_TENANT_SLUG).lower()

    if not email or not password:
        return jsonify({"error": "email and password required"}), 400
    if role not in ROLES:
        return jsonify({"error": f"role must be one of {ROLES}"}), 400

    # Admin-only once at least one user exists — bootstrap is open.
    any_user = User.query.first()
    if any_user is not None:
        _ensure_context_resolved()
        u = current_user()
        if u is None or u.role != "admin":
            return jsonify({"error": "Only admins can register new users"}), 403

    tenant = Tenant.query.filter_by(slug=tenant_slug).first()
    if not tenant:
        tenant = Tenant(slug=tenant_slug, name=data.get("tenant_name") or tenant_slug.title())
        db.session.add(tenant)
        db.session.flush()

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email already registered"}), 409

    user = User(
        tenant_id=tenant.id,
        email=email,
        password_hash=generate_password_hash(password),
        name=name,
        role=role,
    )
    db.session.add(user)
    db.session.commit()
    logger.info("Registered user id=%s email=%s role=%s tenant=%s", user.id, email, role, tenant.slug)
    return jsonify(user.to_dict()), 201


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.json or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    user = User.query.filter_by(email=email).first()
    if not user or not user.is_active or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    user.last_login = datetime.utcnow()
    db.session.commit()
    token = issue_token(user)
    return jsonify({
        "token": token,
        "token_type": "Bearer",
        "expires_in": _ttl_seconds(),
        "user": user.to_dict(),
    }), 200


@auth_bp.route("/auth/me", methods=["GET"])
def me():
    _ensure_context_resolved()
    u = current_user()
    t = current_tenant()
    return jsonify({
        "authenticated": u is not None,
        "auth_enforced": _auth_enforced(),
        "user": u.to_dict() if u else None,
        "tenant": {"id": t.id, "slug": t.slug, "name": t.name} if t else None,
    }), 200
