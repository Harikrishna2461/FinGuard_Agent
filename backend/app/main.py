"""Minimal FastAPI backend for FinGuard."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException

from app.ai_client import AIServiceError, request_portfolio_review
from app.db import execute, fetch_all, fetch_one, init_db
from app.schemas import (
    CreatePortfolioRequest,
    CreateTransactionRequest,
    QuickRecommendationRequest,
)


app = FastAPI(title="FinGuard Backend")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/api/portfolios")
def create_portfolio(payload: CreatePortfolioRequest) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    portfolio_id = execute(
        """
        INSERT INTO portfolios (user_id, name, total_value, cash_balance, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            payload.user_id,
            payload.name,
            payload.initial_investment,
            payload.initial_investment,
            now,
            now,
        ),
    )
    portfolio = fetch_one("SELECT * FROM portfolios WHERE id = ?", (portfolio_id,))
    return portfolio or {}


@app.get("/api/portfolios")
def list_portfolios() -> dict[str, list[dict]]:
    portfolios = fetch_all("SELECT * FROM portfolios ORDER BY created_at DESC")
    return {"portfolios": portfolios}


@app.get("/api/portfolios/{portfolio_id}")
def get_portfolio(portfolio_id: int) -> dict[str, Any]:
    portfolio = fetch_one("SELECT * FROM portfolios WHERE id = ?", (portfolio_id,))
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    transactions = fetch_all(
        "SELECT * FROM transactions WHERE portfolio_id = ? ORDER BY timestamp DESC",
        (portfolio_id,),
    )
    portfolio["transactions_count"] = len(transactions)
    portfolio["symbols"] = sorted({txn["symbol"] for txn in transactions})
    return portfolio


@app.post("/api/portfolios/{portfolio_id}/transactions")
def add_transaction(portfolio_id: int, payload: CreateTransactionRequest) -> dict[str, Any]:
    portfolio = fetch_one("SELECT * FROM portfolios WHERE id = ?", (portfolio_id,))
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    total_amount = payload.quantity * payload.price
    cash_delta = total_amount + payload.fees if payload.type == "buy" else -(total_amount - payload.fees)
    new_cash_balance = float(portfolio["cash_balance"]) - cash_delta
    now = datetime.now(timezone.utc).isoformat()

    transaction_id = execute(
        """
        INSERT INTO transactions (
            portfolio_id, symbol, transaction_type, quantity, price,
            total_amount, fees, notes, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            portfolio_id,
            payload.symbol.upper(),
            payload.type,
            payload.quantity,
            payload.price,
            total_amount,
            payload.fees,
            payload.notes,
            now,
        ),
    )

    execute(
        """
        UPDATE portfolios
        SET cash_balance = ?, updated_at = ?
        WHERE id = ?
        """,
        (new_cash_balance, now, portfolio_id),
    )

    transaction = fetch_one("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
    if transaction is None:
        raise HTTPException(status_code=500, detail="Transaction was not persisted")

    return {
        "id": transaction["id"],
        "portfolio_id": transaction["portfolio_id"],
        "symbol": transaction["symbol"],
        "type": transaction["transaction_type"],
        "quantity": transaction["quantity"],
        "price": transaction["price"],
        "total_amount": transaction["total_amount"],
        "fees": transaction["fees"],
        "notes": transaction["notes"],
        "timestamp": transaction["timestamp"],
    }


@app.get("/api/portfolios/{portfolio_id}/transactions")
def list_transactions(portfolio_id: int) -> dict[str, list[dict]]:
    portfolio = fetch_one("SELECT * FROM portfolios WHERE id = ?", (portfolio_id,))
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    transactions = fetch_all(
        """
        SELECT id, portfolio_id, symbol, transaction_type, quantity, price,
               total_amount, fees, notes, timestamp
        FROM transactions
        WHERE portfolio_id = ?
        ORDER BY timestamp DESC
        """,
        (portfolio_id,),
    )
    return {
        "transactions": [
            {
                "id": txn["id"],
                "portfolio_id": txn["portfolio_id"],
                "symbol": txn["symbol"],
                "type": txn["transaction_type"],
                "quantity": txn["quantity"],
                "price": txn["price"],
                "total_amount": txn["total_amount"],
                "fees": txn["fees"],
                "notes": txn["notes"],
                "timestamp": txn["timestamp"],
            }
            for txn in transactions
        ]
    }


@app.post("/api/portfolios/{portfolio_id}/quick-recommendation")
def quick_recommendation(portfolio_id: int, payload: QuickRecommendationRequest) -> dict[str, Any]:
    portfolio = fetch_one("SELECT * FROM portfolios WHERE id = ?", (portfolio_id,))
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    transactions = fetch_all(
        """
        SELECT id, symbol, transaction_type, quantity, price, timestamp
        FROM transactions
        WHERE portfolio_id = ?
        ORDER BY timestamp DESC
        LIMIT 50
        """,
        (portfolio_id,),
    )

    review_portfolio = {
        "id": portfolio["id"],
        "name": portfolio["name"],
        "total_value": portfolio["total_value"],
        "cash_balance": portfolio["cash_balance"],
        "assets": [],
    }
    review_transactions = [
        {
            "id": txn["id"],
            "symbol": txn["symbol"],
            "type": txn["transaction_type"],
            "quantity": txn["quantity"],
            "price": txn["price"],
            "timestamp": txn["timestamp"],
        }
        for txn in transactions
    ]

    try:
        return request_portfolio_review(review_portfolio, review_transactions, payload.mode)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
