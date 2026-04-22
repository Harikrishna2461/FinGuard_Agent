"""Shared state objects for LangGraph workflows."""

from typing import Any, Literal, TypedDict


class PortfolioAnalysisState(TypedDict, total=False):
    request_id: str
    portfolio: dict[str, Any]
    transactions: list[dict[str, Any]]
    route: Literal["quick", "full"]
    findings: list[str]
    risk_summary: str
    portfolio_summary: str
    compliance_summary: str
    explanation_summary: str
    response: dict[str, Any]
    errors: list[str]
