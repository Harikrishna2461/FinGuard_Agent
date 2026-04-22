"""Minimal ai_system service with internal agent modules and LangGraph scaffold."""

from typing import Any

from fastapi import FastAPI

from ai_system.app.agents import compliance, portfolio, risk
from ai_system.app.orchestrator import portfolio_review
from ai_system.app.schemas import PortfolioReviewRequest


app = FastAPI(title="FinGuard AI System")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/agents/risk/invoke")
def invoke_risk_agent(payload: PortfolioReviewRequest) -> dict[str, Any]:
    return risk.invoke(payload.portfolio.model_dump(), [txn.model_dump() for txn in payload.transactions], payload.mode)


@app.post("/agents/portfolio/invoke")
def invoke_portfolio_agent(payload: PortfolioReviewRequest) -> dict[str, Any]:
    return portfolio.invoke(payload.portfolio.model_dump(), [txn.model_dump() for txn in payload.transactions], payload.mode)


@app.post("/agents/compliance/invoke")
def invoke_compliance_agent(payload: PortfolioReviewRequest) -> dict[str, Any]:
    return compliance.invoke(payload.portfolio.model_dump(), [txn.model_dump() for txn in payload.transactions], payload.mode)


@app.post("/orchestrate/portfolio-review")
def orchestrate_portfolio_review(payload: PortfolioReviewRequest) -> dict[str, Any]:
    return portfolio_review(
        payload.portfolio.model_dump(),
        [txn.model_dump() for txn in payload.transactions],
        payload.mode,
    )
