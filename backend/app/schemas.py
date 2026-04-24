"""Pydantic schemas for the FastAPI backend."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CreatePortfolioRequest(BaseModel):
    user_id: str | None = None
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
    model_config = ConfigDict(extra="allow")

    symbol: str = ""
    type: str = "buy"
    quantity: float = 0
    price: float = 0
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


class CreateAssetRequest(BaseModel):
    symbol: str = ""
    name: str = ""
    quantity: float = 0
    purchase_price: float = 0
    current_price: float | None = None
    asset_type: str = "stock"
    sector: str | None = None


class CreateAlertRequest(BaseModel):
    alert_type: str = ""
    symbol: str | None = None
    target_price: float | None = None
    threshold: float | None = None
    message: str | None = None


class RecommendationRequest(BaseModel):
    symbol: str = ""
    risk_profile: str = "moderate"
