"""Transaction utility routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.ai_client import (
    AIServiceError,
    request_transaction_insights,
    request_transaction_risk,
)


router = APIRouter()


@router.post("/api/transaction/score-risk")
def score_transaction_risk(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    transaction = (
        payload.get("transaction")
        if isinstance(payload.get("transaction"), dict)
        else payload
    )
    if not transaction.get("amount") and not (
        transaction.get("quantity") and transaction.get("price")
    ):
        raise HTTPException(status_code=400, detail="amount is required")
    if (
        "amount" not in transaction
        and transaction.get("quantity")
        and transaction.get("price")
    ):
        transaction = {
            **transaction,
            "amount": float(transaction["quantity"]) * float(transaction["price"]),
        }
    try:
        return request_transaction_risk(transaction)
    except AIServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/transaction/get-ai-insights")
def get_transaction_ai_insights(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    transaction = payload.get("transaction") or {}
    if not transaction:
        raise HTTPException(status_code=400, detail="transaction required")
    try:
        return request_transaction_insights(
            transaction, float(payload.get("score", 50)), payload.get("factors") or {}
        )
    except AIServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
