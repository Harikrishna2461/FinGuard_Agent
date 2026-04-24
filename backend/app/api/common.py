"""Shared helpers for backend route modules."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from app.db import fetch_all, fetch_one


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_portfolio_or_404(portfolio_id: int) -> dict[str, Any]:
    portfolio = fetch_one("SELECT * FROM portfolios WHERE id = ?", (portfolio_id,))
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


def fetch_assets(portfolio_id: int) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT id, portfolio_id, symbol, name, quantity, purchase_price,
               current_price, asset_type, sector, created_at
        FROM assets
        WHERE portfolio_id = ?
        ORDER BY created_at DESC, id DESC
        """,
        (portfolio_id,),
    )


def fetch_transactions(
    portfolio_id: int, limit: int | None = None
) -> list[dict[str, Any]]:
    query = """
        SELECT id, portfolio_id, symbol, transaction_type, quantity, price,
               total_amount, fees, notes, timestamp
        FROM transactions
        WHERE portfolio_id = ?
        ORDER BY timestamp DESC, id DESC
        """
    if limit is not None:
        query += f" LIMIT {int(limit)}"
    return fetch_all(query, (portfolio_id,))


def serialize_asset(asset: dict[str, Any]) -> dict[str, Any]:
    current_value = float(asset["quantity"]) * float(asset["current_price"])
    gain_loss = (
        float(asset["current_price"]) - float(asset["purchase_price"])
    ) * float(asset["quantity"])
    return {
        "id": asset["id"],
        "symbol": asset["symbol"],
        "name": asset["name"],
        "quantity": asset["quantity"],
        "purchase_price": asset["purchase_price"],
        "current_price": asset["current_price"],
        "current_value": current_value,
        "gain_loss": gain_loss,
        "return_percent": (
            (float(asset["current_price"]) - float(asset["purchase_price"]))
            / float(asset["purchase_price"])
            * 100
        )
        if float(asset["purchase_price"] or 0)
        else 0,
        "asset_type": asset["asset_type"],
        "sector": asset["sector"],
        "created_at": asset["created_at"],
    }


def serialize_transaction(transaction: dict[str, Any]) -> dict[str, Any]:
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


def serialize_alert(alert: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": alert["id"],
        "type": alert["alert_type"],
        "symbol": alert["symbol"],
        "target_price": alert["target_price"],
        "threshold": alert["threshold"],
        "is_active": bool(alert["is_active"]),
        "triggered": bool(alert["triggered"]),
        "message": alert["message"],
        "created_at": alert["created_at"],
    }


def build_review_payload(
    portfolio_id: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    portfolio = get_portfolio_or_404(portfolio_id)
    assets = fetch_assets(portfolio_id)
    transactions = fetch_transactions(portfolio_id, limit=50)
    review_portfolio = {
        "id": portfolio["id"],
        "name": portfolio["name"],
        "total_value": portfolio["total_value"],
        "cash_balance": portfolio["cash_balance"],
        "assets": [
            {
                "symbol": asset["symbol"],
                "name": asset["name"],
                "quantity": asset["quantity"],
                "current_price": asset["current_price"],
                "purchase_price": asset["purchase_price"],
                "asset_type": asset["asset_type"],
            }
            for asset in assets
        ],
    }
    review_transactions = [
        {
            "id": transaction["id"],
            "symbol": transaction["symbol"],
            "type": transaction["transaction_type"],
            "quantity": transaction["quantity"],
            "price": transaction["price"],
            "timestamp": transaction["timestamp"],
        }
        for transaction in transactions
    ]
    return review_portfolio, review_transactions


def parse_json_payload(raw_payload: str) -> Any:
    try:
        return json.loads(raw_payload)
    except json.JSONDecodeError:
        return raw_payload


def search_analysis_records(
    query: str, portfolio_id: int | None = None, symbol: str | None = None
) -> list[dict[str, Any]]:
    pattern = f"%{query.lower()}%"
    clauses = ["LOWER(payload) LIKE ?"]
    params: list[Any] = [pattern]

    if portfolio_id is not None:
        clauses.append("portfolio_id = ?")
        params.append(portfolio_id)
    if symbol:
        clauses.append("LOWER(payload) LIKE ?")
        params.append(f"%{symbol.lower()}%")

    rows = fetch_all(
        f"""
        SELECT id, portfolio_id, analysis_type, payload, created_at
        FROM analyses
        WHERE {" AND ".join(clauses)}
        ORDER BY created_at DESC, id DESC
        LIMIT 20
        """,
        tuple(params),
    )
    return [
        {
            "id": row["id"],
            "portfolio_id": row["portfolio_id"],
            "analysis_type": row["analysis_type"],
            "payload": parse_json_payload(row["payload"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def search_risk_records(
    query: str, portfolio_id: int | None = None
) -> list[dict[str, Any]]:
    pattern = f"%{query.lower()}%"
    clauses = [
        "(LOWER(COALESCE(c.flags, '')) LIKE ? OR LOWER(COALESCE(t.symbol, '')) LIKE ? OR LOWER(COALESCE(c.status, '')) LIKE ?)"
    ]
    params: list[Any] = [pattern, pattern, pattern]

    if portfolio_id is not None:
        clauses.append("c.portfolio_id = ?")
        params.append(portfolio_id)

    rows = fetch_all(
        f"""
        SELECT c.id, c.portfolio_id, c.transaction_id, c.risk_score, c.flags, c.status, c.created_at, t.symbol
        FROM cases c
        LEFT JOIN transactions t ON t.id = c.transaction_id
        WHERE {" AND ".join(clauses)}
        ORDER BY c.created_at DESC, c.id DESC
        LIMIT 20
        """,
        tuple(params),
    )
    return [
        {
            "id": row["id"],
            "portfolio_id": row["portfolio_id"],
            "transaction_id": row["transaction_id"],
            "symbol": row["symbol"],
            "risk_score": row["risk_score"],
            "flags": parse_json_payload(row["flags"]),
            "status": row["status"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
