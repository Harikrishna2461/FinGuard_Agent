"""LangGraph nodes for portfolio review."""

from ai_system.app.agents import compliance, explanation, portfolio, risk
from ai_system.langgraph.state import PortfolioAnalysisState


def ingest_request(state: PortfolioAnalysisState) -> PortfolioAnalysisState:
    state.setdefault("findings", [])
    state.setdefault("errors", [])
    state["route"] = state.get("route") or ("quick" if len(state.get("transactions", [])) < 10 else "full")
    return state


def run_risk_screen(state: PortfolioAnalysisState) -> PortfolioAnalysisState:
    result = risk.invoke(
        state.get("portfolio") or {},
        state.get("transactions") or [],
        state.get("route", "quick"),
    )
    state["risk_summary"] = result["summary"]
    state["findings"].extend(result["findings"])
    return state


def run_portfolio_review(state: PortfolioAnalysisState) -> PortfolioAnalysisState:
    result = portfolio.invoke(
        state.get("portfolio") or {},
        state.get("transactions") or [],
        state.get("route", "quick"),
    )
    state["portfolio_summary"] = result["summary"]
    state["findings"].extend(result["findings"])
    return state


def run_compliance_review(state: PortfolioAnalysisState) -> PortfolioAnalysisState:
    result = compliance.invoke(
        state.get("portfolio") or {},
        state.get("transactions") or [],
        state.get("route", "quick"),
    )
    state["compliance_summary"] = result["summary"]
    state["findings"].extend(result["findings"])
    return state


def run_explanation(state: PortfolioAnalysisState) -> PortfolioAnalysisState:
    result = explanation.invoke(
        state.get("portfolio") or {},
        state.get("transactions") or [],
        state.get("findings") or [],
    )
    state["explanation_summary"] = result["summary"]
    return state


def compile_response(state: PortfolioAnalysisState) -> PortfolioAnalysisState:
    state["response"] = {
        "timestamp": state.get("request_id"),
        "request_id": state.get("request_id"),
        "portfolio_id": (state.get("portfolio") or {}).get("id"),
        "mode": state.get("route"),
        "crew_output": (
            "## Portfolio Review\n\n"
            f"### Risk\n- {state.get('risk_summary', '')}\n\n"
            f"### Portfolio\n- {state.get('portfolio_summary', '')}\n\n"
            f"### Compliance\n- {state.get('compliance_summary', '')}\n\n"
            f"### Explanation\n{state.get('explanation_summary', '')}"
        ),
        "agents_used": 4,
        "recommendation_type": state.get("route"),
        "rate_limited": False,
        "findings": state.get("findings", []),
        "errors": state.get("errors", []),
    }
    return state


def choose_analysis_route(state: PortfolioAnalysisState) -> str:
    return state.get("route", "quick")
