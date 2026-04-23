"""Market sentiment routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.ai_client import AIServiceError, request_market_sentiment

try:
    import vector_store
except Exception:  # pragma: no cover - optional runtime dependency
    vector_store = None


router = APIRouter()


@router.get("/api/sentiment")
@router.get("/api/sentiment/{symbol}")
def get_sentiment(
    symbol: str | None = None, symbols: str | None = None
) -> dict[str, Any]:
    requested = (
        [symbol.upper()]
        if symbol
        else [
            item.strip().upper() for item in (symbols or "").split(",") if item.strip()
        ]
    )
    if not requested:
        raise HTTPException(
            status_code=400,
            detail="Symbol(s) required. Use /sentiment/AAPL or /sentiment?symbols=AAPL,MSFT",
        )
    try:
        result = request_market_sentiment(requested[:10])
    except AIServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if vector_store is not None:
        for symbol_name in requested[:10]:
            try:
                vector_store.store_market_analysis(
                    symbol_name,
                    result.get("sentiment_analysis", ""),
                )
            except Exception:
                pass
    return result
