"""
portfolio_analysis_agent.py

Responsible for:
    • Asset allocation assessment
    • Diversification scoring
    • Rebalancing recommendations
"""

import json
from typing import Dict, Any

from agents.base_agent import FinancialBaseAgent


class PortfolioAnalysisAgent(FinancialBaseAgent):
    """Analyses portfolio composition and recommends optimisations."""

    AGENT_DOMAIN = "portfolio_analysis"

    AGENT_DOMAIN = "portfolio_analysis"

    def __init__(self):
        super().__init__("PortfolioAnalyzer")

    # ── analysis ──────────────────────────────────────────────────
    def analyze_portfolio(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = (
            "You are a professional portfolio analyst. Analyse this portfolio and provide:\n"
            "1. Asset allocation assessment\n"
            "2. Diversification score (0-100)\n"
            "3. Risk assessment\n"
            "4. Performance review\n"
            "5. Specific recommendations\n\n"
            f"Portfolio Data:\n{json.dumps(portfolio_data, indent=2)}\n\n"
            "Provide structured analysis with scores and specific actionable recommendations."
        )
        response = self.chat(prompt)
        return self._stamp({"analysis": response})
    
    
    # ── rebalancing ───────────────────────────────────────────────
    def rebalance_portfolio(
        self,
        portfolio_data: Dict[str, Any],
        target_allocation: Dict[str, float],
    ) -> Dict[str, Any]:
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
        response = self.chat(prompt)
        return self._stamp({"action": "rebalance", "plan": response})