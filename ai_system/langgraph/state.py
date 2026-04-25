"""Shared state objects for LangGraph workflows."""

from typing import Any, Literal, TypedDict


class PortfolioAnalysisState(TypedDict, total=False):
    request_id: str
    portfolio: dict[str, Any]
    transactions: list[dict[str, Any]]
    route: Literal["quick", "full"]
    portfolio_summary: str
    transaction_summary: str
    ml_summary: str
    crew1_output: str
    crew2_output: str
    crew3_output: str
    crews_run: int
    rate_limited: bool
    findings: list[str]
    response: dict[str, Any]
    errors: list[str]
    analysis_trace: list[dict[str, Any]]
