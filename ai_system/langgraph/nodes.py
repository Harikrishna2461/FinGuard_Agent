"""LangGraph nodes for portfolio review with legacy-compatible semantics."""

from __future__ import annotations

from ai_system.app.agents import (
    explanation_agent as explanation,
    portfolio_analysis_agent as portfolio,
    risk_assessment_agent as risk,
)
from ai_system.app.analysis_utils import ml_score_transactions
from ai_system.app.llm import is_rate_limit_error
from ai_system.langgraph.state import PortfolioAnalysisState


def _truncate_error(exc: Exception) -> str:
    return str(exc)[:200]


def _compliance_snapshot(transactions: list[dict]) -> str:
    findings: list[str] = []
    unknown_types = sorted(
        {
            (txn.get("type") or "").lower()
            for txn in transactions
            if (txn.get("type") or "").lower() not in {"buy", "sell", "dividend", ""}
        }
    )
    if unknown_types:
        findings.append(
            f"Unsupported transaction types seen: {', '.join(unknown_types)}."
        )
    if len(transactions) >= 20:
        findings.append(
            "Transaction volume is elevated and may merit reporting-threshold review."
        )
    if not findings:
        findings.append(
            "No immediate compliance concern was found in the quick policy scan."
        )
    return " ".join(findings)


def _market_snapshot(symbols: list[str]) -> str:
    if not symbols:
        return "No active symbols were available for a focused market sentiment pass."
    return (
        f"Market context was summarized for {', '.join(symbols[:5])}. "
        "Use the dedicated sentiment endpoint for a deeper symbol-level read."
    )


def _customer_snapshot(portfolio_data: dict, transactions: list[dict]) -> str:
    return (
        f"Customer context: portfolio '{portfolio_data.get('name', 'Unnamed')}' "
        f"has {len(portfolio_data.get('assets', []))} assets and {len(transactions)} recent transactions. "
        "Current behavior appears consistent with routine portfolio activity."
    )


def _alert_snapshot(state: PortfolioAnalysisState) -> str:
    ml_summary = state.get("ml_summary", "")
    if "High/Critical: 0" in ml_summary:
        return "Alert intake found no urgent escalation signal from the ML pre-screening summary."
    if ml_summary:
        return "Alert intake flagged the portfolio for analyst review because elevated ML risk indicators were present."
    return "Alert intake had limited machine-scored context and recommends normal analyst discretion."


def _escalation_snapshot(state: PortfolioAnalysisState) -> str:
    ml_summary = state.get("ml_summary", "")
    if "High/Critical: 0" in ml_summary:
        return "Escalation path: remain in standard monitoring unless new risk signals appear."
    return "Escalation path: queue for human review if related alerts or repeated high-risk transactions continue."


def ingest_request(state: PortfolioAnalysisState) -> PortfolioAnalysisState:
    state.setdefault("findings", [])
    state.setdefault("errors", [])
    state.setdefault("crews_run", 0)
    state.setdefault("rate_limited", False)
    state["route"] = state.get("route") or (
        "quick" if len(state.get("transactions", [])) < 10 else "full"
    )

    portfolio_data = state.get("portfolio") or {}
    transactions = state.get("transactions") or []
    state["portfolio_summary"] = (
        f"Portfolio '{portfolio_data.get('name')}': "
        f"${portfolio_data.get('total_value', 0):,.0f} total, "
        f"{len(portfolio_data.get('assets', []))} assets, "
        f"symbols: {', '.join(asset.get('symbol', '') for asset in portfolio_data.get('assets', [])[:5] if asset.get('symbol'))}"
    )
    state["transaction_summary"] = (
        f"Recent {len(transactions[:10])} transactions; "
        f"types: {', '.join(sorted({txn.get('type', 'unknown') for txn in transactions[:10]}))}"
    )
    state["ml_summary"] = ml_score_transactions(transactions[:10])
    return state


def run_quick_recommendation(state: PortfolioAnalysisState) -> PortfolioAnalysisState:
    state["response"] = risk.quick_portfolio_recommendation(
        state.get("portfolio") or {},
        state.get("transactions") or [],
    )
    return state


def run_full_crew_one(state: PortfolioAnalysisState) -> PortfolioAnalysisState:
    if state.get("rate_limited"):
        return state

    portfolio_data = state.get("portfolio") or {}
    transactions = state.get("transactions") or []

    try:
        ml_scores = [risk.score_transaction(txn) for txn in transactions[:10]]
        risk_assessment = risk.assess_portfolio_risk(
            portfolio_data,
            {"volatility": "current market conditions"},
        )
        state["crew1_output"] = (
            f"{risk_assessment['risk_analysis']}\n\n"
            f"{risk.detect_fraud_risk(transactions, portfolio_data, ml_scores)['assessment']}\n\n"
            f"{_compliance_snapshot(transactions)}"
        )
        state["crews_run"] = 1
        return state
    except Exception as exc:
        if is_rate_limit_error(exc):
            state["rate_limited"] = True
            state["crews_run"] = 1
            state["crew1_output"] = (
                "⚠️ Rate limit exceeded. Please wait 30 seconds and try again."
            )
            return state

        state["crew1_output"] = f"⚠️ Risk Analysis failed: {_truncate_error(exc)}"
        state["crews_run"] = 1
        return state


def run_full_crew_two(state: PortfolioAnalysisState) -> PortfolioAnalysisState:
    if state.get("rate_limited"):
        return state

    portfolio_data = state.get("portfolio") or {}
    transactions = state.get("transactions") or []
    symbols = [
        asset.get("symbol")
        for asset in portfolio_data.get("assets", [])
        if asset.get("symbol")
    ]
    fallback_symbols = [txn.get("symbol") for txn in transactions if txn.get("symbol")][
        :5
    ]

    try:
        portfolio_analysis = portfolio.analyze_portfolio(portfolio_data)
        state["crew2_output"] = (
            f"{portfolio_analysis['analysis']}\n\n"
            f"{_market_snapshot(symbols or fallback_symbols)}\n\n"
            f"{_customer_snapshot(portfolio_data, transactions)}"
        )
        state["crews_run"] = 2
        return state
    except Exception as exc:
        if is_rate_limit_error(exc):
            state["rate_limited"] = True
            state["crews_run"] = 2
            state["crew2_output"] = "⚠️ Rate limit exceeded. Skipping remaining crews."
            return state

        state["crew2_output"] = f"⚠️ Portfolio Analysis failed: {_truncate_error(exc)}"
        state["crews_run"] = 2
        return state


def run_full_crew_three(state: PortfolioAnalysisState) -> PortfolioAnalysisState:
    if state.get("rate_limited"):
        return state

    portfolio_data = state.get("portfolio") or {}

    try:
        summary = explanation.summarize_analysis(
            {
                "crew_1": state.get("crew1_output", ""),
                "crew_2": state.get("crew2_output", ""),
                "portfolio": portfolio_data.get("name"),
            },
            "medium",
        )
        state["crew3_output"] = (
            f"{_alert_snapshot(state)}\n\n"
            f"{summary['summary']}\n\n"
            f"{_escalation_snapshot(state)}"
        )
        state["crews_run"] = 3
        return state
    except Exception as exc:
        if is_rate_limit_error(exc):
            state["rate_limited"] = True
            state["crews_run"] = 3
            state["crew3_output"] = "⚠️ Rate limit exceeded. Analysis incomplete."
            return state

        state["crew3_output"] = f"⚠️ Summary Crew failed: {_truncate_error(exc)}"
        state["crews_run"] = 3
        return state


def compile_quick_response(state: PortfolioAnalysisState) -> PortfolioAnalysisState:
    return state


def compile_full_response(state: PortfolioAnalysisState) -> PortfolioAnalysisState:
    portfolio = state.get("portfolio") or {}
    ml_summary = state.get("ml_summary", "")
    crews_run = state.get("crews_run", 0)

    if state.get("rate_limited"):
        if crews_run <= 1:
            crew_output = (
                "## 📊 Portfolio Analysis - Rate Limited\n\n"
                "⏰ **Model API Rate Limit Reached**\n\n"
                "**What happened:**\n"
                "The AI analysis system exceeded its current token quota.\n\n"
                "**Your options:**\n"
                "1. **Wait 30-60 seconds** and retry your analysis\n"
                "2. **Increase your model service usage tier** if this happens frequently\n"
                "3. **Switch to a lighter endpoint** - try 'Quick Recommendation' instead\n\n"
                f"**Current Analysis Status:**\n{state.get('crew1_output', '')}\n\n"
                f"### ML Pre-Screening (Always Available)\n{ml_summary}"
            )
        elif crews_run == 2:
            crew_output = (
                "## 📊 Portfolio Analysis - Rate Limited (Crew 2)\n\n"
                "⏰ **Model API Rate Limit Reached**\n\n"
                "**What happened:**\n"
                "The AI analysis system exceeded its token quota during Crew 2.\n\n"
                "**Your options:**\n"
                "1. **Wait 30-60 seconds** and retry your analysis\n"
                "2. **Increase your model service usage tier** if this happens frequently\n"
                "3. **Switch to a lighter endpoint** - try 'Quick Recommendation' instead\n\n"
                "**Completed Analysis:**\n"
                f"- Crew 1 (Risk): {str(state.get('crew1_output', ''))[:100]}...\n"
                f"- Crew 2 (Portfolio): {str(state.get('crew2_output', ''))[:100]}...\n\n"
                f"### ML Pre-Screening (Always Available)\n{ml_summary}"
            )
        else:
            crew_output = (
                "## 📊 Portfolio Analysis - Partial (Rate Limited)\n\n"
                "⏰ **Model API Rate Limit Reached**\n\n"
                "**What happened:**\n"
                "The AI analysis system exceeded its token quota.\n\n"
                "**Your options:**\n"
                "1. **Wait 30-60 seconds** and retry your analysis\n"
                "2. **Increase your model service usage tier** if this happens frequently\n"
                "3. **Switch to a lighter endpoint** - try 'Quick Recommendation' instead\n\n"
                "**Partial Analysis (Completed):**\n"
                f"- Crew 1 (Risk): {str(state.get('crew1_output', ''))[:100]}...\n"
                f"- Crew 2 (Portfolio): {str(state.get('crew2_output', ''))[:100]}...\n"
                f"- Crew 3 (Summary): {str(state.get('crew3_output', ''))[:100]}...\n\n"
                f"### ML Pre-Screening (Always Available)\n{ml_summary}"
            )

        state["response"] = {
            "timestamp": state.get("request_id"),
            "portfolio_id": portfolio.get("id"),
            "crew_output": crew_output,
            "agents_used": 9,
            "crews_run": crews_run,
            "rate_limited": True,
        }
        return state

    state["response"] = {
        "timestamp": state.get("request_id"),
        "portfolio_id": portfolio.get("id"),
        "crew_output": (
            "## 📊 Multi-Crew Portfolio Analysis (3 Parallel Crews)\n\n"
            f"### Crew 1: Risk Analysis\n{state.get('crew1_output', '')}\n\n"
            f"### Crew 2: Portfolio Analysis\n{state.get('crew2_output', '')}\n\n"
            f"### Crew 3: Summary & Escalation\n{state.get('crew3_output', '')}\n\n"
            f"### ML Pre-Screening\n{ml_summary}"
        ),
        "agents_used": 9,
        "crews_run": 3,
        "rate_limited": False,
    }
    return state


def choose_analysis_route(state: PortfolioAnalysisState) -> str:
    return state.get("route", "quick")
