"""
risk_detection_agent.py

Responsible for:
  • Fraud pattern detection (ML-enhanced)
  • Market risk assessment
  • Concentration risk evaluation

Uses the hybrid ML scoring engine (Rules + GradientBoosting + IsolationForest)
as a first pass before sending context to the LLM for expert analysis.
"""

import json
import logging
from typing import Dict, Any, List

from agents.base_agent import FinancialBaseAgent

logger = logging.getLogger(__name__)

# Lazy-load ML engine
_risk_engine = None

def _get_risk_engine():
    global _risk_engine
    if _risk_engine is None:
        try:
            from ml.risk_scoring_engine import TransactionRiskEngine
            _risk_engine = TransactionRiskEngine()
            logger.info("RiskDetectionAgent: ML engine loaded")
        except Exception as e:
            logger.warning("RiskDetectionAgent: ML engine unavailable — %s", e)
    return _risk_engine


class RiskDetectionAgent(FinancialBaseAgent):
    """Detects financial risks, fraud indicators and anomalies using ML + LLM."""

    def __init__(self):
        super().__init__("RiskDetector")

    # ── fraud detection (ML-enhanced) ─────────────────────────────
    def detect_fraud_risk(
        self,
        transaction_history: List[Dict[str, Any]],
        portfolio_data: Dict[str, Any],
        ml_pre_scores: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Detect fraud risk in transactions.
        
        If ml_pre_scores are not provided, runs the ML engine internally.
        Then passes ML results + raw data to the LLM for expert interpretation.
        """
        # ── Run ML scoring if not already done ──
        engine = _get_risk_engine()
        ml_summary_lines = []

        if ml_pre_scores:
            # Use pre-computed scores (from orchestrator)
            for i, result in enumerate(ml_pre_scores):
                ml_summary_lines.append(
                    f"  Txn {i+1}: score={result.get('final_score', '?')}/100 "
                    f"label={result.get('risk_label', '?')} "
                    f"flags=[{', '.join(result.get('flags', []))}]"
                )
        elif engine:
            for i, txn in enumerate(transaction_history[:20]):
                try:
                    result = engine.score(txn)
                    ml_summary_lines.append(
                        f"  Txn {i+1}: score={result['final_score']}/100 "
                        f"label={result['risk_label']} method={result['method']} "
                        f"flags=[{', '.join(result['flags'])}]"
                    )
                except Exception:
                    ml_summary_lines.append(f"  Txn {i+1}: ML scoring failed")

        ml_section = ""
        if ml_summary_lines:
            ml_section = (
                "\n\n── ML Pre-Screening Results (Rules + GradientBoosting + IsolationForest) ──\n"
                + "\n".join(ml_summary_lines)
                + "\n\nUse these ML scores as your baseline. Add expert analysis on top."
            )

        prompt = (
            "You are a financial fraud detection expert. Analyse these transactions "
            "and portfolio for suspicious activity:\n\n"
            f"Transaction History:\n{json.dumps(transaction_history[:10], indent=2)}\n\n"
            f"Portfolio Data:\n{json.dumps(portfolio_data, indent=2)}"
            f"{ml_section}\n\n"
            "Identify:\n"
            "1. Unusual transaction patterns\n"
            "2. Potential fraud indicators\n"
            "3. Risk level (low/medium/high)\n"
            "4. Specific alerts needed\n"
            "5. Recommended actions"
        )
        response = self.chat(prompt)
        return self._stamp({"alert_type": "fraud_risk", "assessment": response})

    # ── market risk ───────────────────────────────────────────────
    def assess_market_risk(
        self,
        portfolio_data: Dict[str, Any],
        market_conditions: Dict[str, Any],
    ) -> Dict[str, Any]:
        prompt = (
            "You are a market risk analyst. Assess portfolio risk in current "
            "market conditions:\n\n"
            f"Portfolio:\n{json.dumps(portfolio_data, indent=2)}\n\n"
            f"Market Conditions:\n{json.dumps(market_conditions, indent=2)}\n\n"
            "Provide:\n"
            "1. Market risk exposure assessment\n"
            "2. Sector-specific risks\n"
            "3. Systemic risk analysis\n"
            "4. Hedging recommendations\n"
            "5. Protective measures"
        )
        response = self.chat(prompt)
        return self._stamp({"alert_type": "market_risk", "assessment": response})
