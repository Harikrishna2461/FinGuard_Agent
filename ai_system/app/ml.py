"""Lazy ML engine loader for ai_system."""

from __future__ import annotations

_risk_engine = None


def get_risk_engine():
    global _risk_engine
    if _risk_engine is not None:
        return _risk_engine

    try:
        from ml.risk_scoring_engine import TransactionRiskEngine
    except ImportError:
        try:
            from backend.ml.risk_scoring_engine import TransactionRiskEngine
        except ImportError:
            return None

    try:
        _risk_engine = TransactionRiskEngine()
    except Exception:
        _risk_engine = None
    return _risk_engine
