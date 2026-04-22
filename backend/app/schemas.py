"""Pydantic schemas for the FastAPI backend."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreatePortfolioRequest(BaseModel):
    user_id: str = "demo-user"
    name: str = "My Portfolio"
    initial_investment: float = 0


class PortfolioResponse(BaseModel):
    id: int
    user_id: str
    name: str
    total_value: float
    cash_balance: float
    created_at: str
    updated_at: str


class CreateTransactionRequest(BaseModel):
    symbol: str
    type: str = "buy"
    quantity: float
    price: float
    fees: float = 0
    notes: str | None = None


class TransactionResponse(BaseModel):
    id: int
    portfolio_id: int
    symbol: str
    type: str
    quantity: float
    price: float
    total_amount: float
    fees: float
    notes: str | None = None
    timestamp: str


class QuickRecommendationRequest(BaseModel):
    mode: str = Field(default="quick")
