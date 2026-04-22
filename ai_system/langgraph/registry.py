"""Registry for LangGraph workflow builders."""

from ai_system.langgraph.workflows.portfolio_review import build_portfolio_review_graph


LANGGRAPH_WORKFLOWS = {
    "portfolio_review": build_portfolio_review_graph,
}
