"""
market_intelligence_agent.py

Responsible for:
    • Market sentiment analysis
    • Investment recommendations
    • Trend identification
"""

import json
from typing import Dict, Any, List

from agents.base_agent import FinancialBaseAgent


class MarketIntelligenceAgent(FinancialBaseAgent):
    """Provides market research, sentiment and recommendations."""

    AGENT_DOMAIN = "market_intelligence"

    AGENT_DOMAIN = "market_intelligence"

    def __init__(self):
        super().__init__("MarketIntelligence")

    # ── sentiment ─────────────────────────────────────────────────
    def analyze_market_sentiment(
        self,
        symbols: List[str],
        news_context: str | None = None,
    ) -> Dict[str, Any]:
        symbols_str = ", ".join(symbols)
        ctx = f"\nContext: {news_context}" if news_context else ""
        prompt = (
            f"You are a market sentiment analyst. Provide sentiment analysis for: {symbols_str}\n"
            f"{ctx}\n\n"
            "Provide:\n"
            "1. Sentiment score for each symbol (-1 to 1)\n"
            "2. Key sentiment drivers\n"
            "3. Confidence level\n"
            "4. Short-term outlook (1-4 weeks)\n"
            "5. Long-term outlook (3-6 months)"
        )
        response = self.chat(prompt)
        return self._stamp({"symbols": symbols, "sentiment_analysis": response})

    # ── recommendation ────────────────────────────────────────────
    def generate_investment_recommendation(
        self,
        symbol: str,
        portfolio_size: float,
        risk_profile: str,
    ) -> Dict[str, Any]:
        prompt = (
            f"You are a professional investment advisor. Provide a recommendation for {symbol}:\n\n"
            f"Portfolio Size: ${portfolio_size:,.2f}\n"
            f"Risk Profile: {risk_profile}\n\n"
            "Provide:\n"
            "1. Buy/Hold/Sell recommendation\n"
            "2. Target entry/exit prices\n"
            "3. Position sizing (% of portfolio)\n"
            "4. Risk-reward ratio\n"
            "5. Key catalysts to watch\n"
            "6. Alternative positions to consider"
        )
        response = self.chat(prompt)
        return self._stamp({"symbol": symbol, "recommendation": response})
