"""Portfolio analysis logic aligned to the legacy prompts."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from ai_system.app.llm import chat


def analyze_portfolio(portfolio: dict) -> dict:
    prompt = (
        "You are a professional portfolio analyst. Analyse this portfolio and provide:\n"
        "1. Asset allocation assessment\n"
        "2. Diversification score (0-100)\n"
        "3. Risk assessment\n"
        "4. Performance review\n"
        "5. Specific recommendations\n\n"
        f"Portfolio Data:\n{json.dumps(portfolio, indent=2)}\n\n"
        "Provide structured analysis with scores and specific actionable recommendations."
    )
    response = chat(prompt)
    return {
        "agent": "PortfolioAnalyzer",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "analysis": response or "Portfolio analysis unavailable.",
    }


def rebalance_portfolio(portfolio_data: dict, target_allocation: dict[str, float]) -> dict:
    prompt = (
        "You are a portfolio rebalancing expert. Based on this portfolio and target allocation:\n\n"
        f"Current Portfolio:\n{json.dumps(portfolio_data, indent=2)}\n\n"
        f"Target Allocation:\n{json.dumps(target_allocation, indent=2)}\n\n"
        "Generate a detailed rebalancing plan with:\n"
        "1. Current vs target allocation comparison\n"
        "2. Specific trades to execute\n"
        "3. Expected impact on returns\n"
        "4. Tax implications to consider\n"
        "5. Implementation timeline"
    )
    response = chat(prompt)
    return {
        "agent": "PortfolioAnalyzer",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "rebalance",
        "plan": response or "Rebalancing plan unavailable.",
    }


def invoke(portfolio: dict, transactions: list[dict], mode: str = "quick") -> dict:
    if mode == "full":
        result = analyze_portfolio(portfolio)
        return {
            "agent": "portfolio",
            "mode": mode,
            "summary": result["analysis"],
            "analysis": result["analysis"],
            "findings": [result["analysis"]],
        }

    total_value = float(portfolio.get("total_value") or 0)
    cash_balance = float(portfolio.get("cash_balance") or 0)
    unique_symbols = len(
        {txn.get("symbol") for txn in transactions if txn.get("symbol")}
    )
    cash_ratio = (cash_balance / total_value) if total_value else 0.0

    findings = []
    if total_value == 0:
        findings.append(
            "Portfolio has no funded value yet, so allocation analysis is preliminary."
        )
    if unique_symbols <= 2 and transactions:
        findings.append(
            "Portfolio diversification appears thin based on recent symbol activity."
        )
    if cash_ratio > 0.35:
        findings.append("Cash allocation is high relative to portfolio value.")
    elif 0 < cash_ratio < 0.05:
        findings.append("Cash buffer is thin for near-term flexibility.")
    if not findings:
        findings.append("Quick portfolio screen looks balanced at a high level.")

    return {
        "agent": "portfolio",
        "mode": mode,
        "summary": " ".join(findings),
        "findings": findings,
    }


class PortfolioAnalysisAgent:
    AGENT_DOMAIN = "portfolio_analysis"

    def analyze_portfolio(self, portfolio_data: dict) -> dict:
        return analyze_portfolio(portfolio_data)

    def rebalance_portfolio(self, portfolio_data: dict, target_allocation: dict[str, float]) -> dict:
        return rebalance_portfolio(portfolio_data, target_allocation)
