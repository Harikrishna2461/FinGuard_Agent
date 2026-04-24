"""System and catalog routes."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter

from app.symbols import DEFAULT_SYMBOLS, get_all_symbols, get_symbols_by_sector


router = APIRouter()


@router.get("/health")
@router.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@router.get("/")
def root() -> dict[str, str]:
    return {"name": "FinGuard Backend", "status": "healthy", "health": "/api/health"}


@router.get("/api/symbols")
def list_symbols() -> dict[str, Any]:
    return {"symbols": get_all_symbols(), "default_symbols": DEFAULT_SYMBOLS}


@router.get("/api/symbols/sectors")
def list_symbol_sectors() -> dict[str, Any]:
    return {"sectors": get_symbols_by_sector()}
