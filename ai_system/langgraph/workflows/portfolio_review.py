"""Portfolio review graph scaffold.

This intentionally does not need to be runnable yet. The purpose is to define
the graph shape and node boundaries before the in-process orchestrator is
replaced with LangGraph.
"""

from ai_system.langgraph.nodes import (
    choose_analysis_route,
    compile_response,
    ingest_request,
    run_compliance_review,
    run_explanation,
    run_portfolio_review,
    run_risk_screen,
)
from ai_system.langgraph.state import PortfolioAnalysisState

try:
    from langgraph.graph import END, StateGraph
except ImportError:  # pragma: no cover - scaffold only
    END = "__end__"
    StateGraph = None


def build_portfolio_review_graph():
    """Return a scaffolded LangGraph graph or raise if langgraph is unavailable."""
    if StateGraph is None:
        raise ImportError("langgraph is not installed yet")

    graph = StateGraph(PortfolioAnalysisState)
    graph.add_node("ingest_request", ingest_request)
    graph.add_node("run_risk_screen", run_risk_screen)
    graph.add_node("run_portfolio_review", run_portfolio_review)
    graph.add_node("run_compliance_review", run_compliance_review)
    graph.add_node("run_explanation", run_explanation)
    graph.add_node("compile_response", compile_response)

    graph.set_entry_point("ingest_request")
    graph.add_conditional_edges(
        "ingest_request",
        choose_analysis_route,
        {
            "quick": "run_risk_screen",
            "full": "run_risk_screen",
        },
    )
    graph.add_edge("run_risk_screen", "run_portfolio_review")
    graph.add_edge("run_portfolio_review", "run_compliance_review")
    graph.add_edge("run_compliance_review", "run_explanation")
    graph.add_edge("run_explanation", "compile_response")
    graph.add_edge("compile_response", END)

    return graph.compile()
