"""Primary compiled graph entrypoint for LangGraph tooling."""

from ai_system.langgraph.workflows.portfolio_review import build_portfolio_review_graph


graph = build_portfolio_review_graph()
