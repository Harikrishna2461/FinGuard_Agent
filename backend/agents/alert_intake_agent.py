"""Alert Intake Agent - Receives and processes financial alerts and anomalies.

For transaction-type alerts, the ML hybrid scoring engine (Rules + ML models)
is used automatically to provide quantitative risk scores alongside the
LLM-based categorization.
"""

import logging
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
            logger.info("AlertIntakeAgent: ML engine loaded")
        except Exception as e:
            logger.warning("AlertIntakeAgent: ML engine unavailable — %s", e)
    return _risk_engine


class AlertIntakeAgent(FinancialBaseAgent):
    """
    Processes incoming alerts from various sources (transactions, portfolio changes,
    market events) and categorizes them for downstream analysis.
    
    Transaction alerts are automatically enriched with ML risk scores.
    """

    def __init__(self):
        super().__init__("AlertIntake")

    def process_alert(self, alert_source: str, alert_data: dict) -> dict:
        """
        Process and categorize an incoming alert.
        
        For transaction-type alerts, runs the ML hybrid scoring engine first
        and includes the quantitative risk score in the LLM prompt.
        
        Args:
            alert_source: Source of alert (e.g., 'transaction', 'market', 'portfolio')
            alert_data: Dict containing alert details
            
        Returns:
            Processed alert with categorization, priority, and ML risk score (if applicable)
        """
        # ── ML pre-screening for transaction alerts ──
        ml_section = ""
        ml_risk_info = None
        if alert_source in ("transaction", "payment", "transfer", "withdrawal"):
            engine = _get_risk_engine()
            if engine:
                try:
                    ml_result = engine.score(alert_data)
                    ml_risk_info = {
                        "risk_score":  ml_result["final_score"],
                        "risk_label":  ml_result["risk_label"],
                        "method":      ml_result["method"],
                        "hard_block":  ml_result["hard_block"],
                        "flags":       ml_result["flags"],
                    }
                    ml_section = (
                        f"\n\nML Risk Pre-Screening (hybrid engine):"
                        f"\n  Score: {ml_result['final_score']}/100"
                        f"\n  Label: {ml_result['risk_label']}"
                        f"\n  Method: {ml_result['method']}"
                        f"\n  Hard Block: {ml_result['hard_block']}"
                        f"\n  Flags: {', '.join(ml_result['flags']) or 'None'}"
                        f"\n\nConsider this ML score when assigning priority."
                    )
                except Exception as e:
                    logger.warning("ML scoring in alert intake failed: %s", e)

        prompt = f"""You are an alert intake specialist. Analyze this incoming financial alert and categorize it.

Alert Source: {alert_source}
Alert Details:
{self._format_dict(alert_data)}{ml_section}

Categorize by:
1. Type (e.g., anomaly, compliance, risk, market)
2. Priority (critical, high, medium, low)
3. Affected areas (portfolio, account, transactions)
4. Recommended next action

Provide structured analysis for routing to appropriate agents."""
        
        result = self.chat(prompt)
        response = {
            "alert_type": alert_source,
            "analysis": result,
            "categorized": True
        }
        if ml_risk_info:
            response["ml_risk"] = ml_risk_info
        return self._stamp(response)

    def filter_alerts(self, alerts: list) -> dict:
        """Filter and prioritize a batch of alerts."""
        prompt = f"""You are reviewing {len(alerts)} financial alerts. 
        
Alerts:
{self._format_list(alerts)}

For each alert:
1. Assess severity
2. Check if it requires immediate escalation
3. Identify any patterns or clusters

Provide prioritized list and escalation recommendations."""
        
        result = self.chat(prompt)
        return self._stamp({
            "original_count": len(alerts),
            "prioritized_analysis": result,
            "requires_escalation": "escalat" in result.lower()
        })

    def validate_alert_integrity(self, alert: dict) -> dict:
        """Validate that an alert contains all required information."""
        prompt = f"""Validate the completeness and consistency of this financial alert:

{self._format_dict(alert)}

Check:
1. All required fields present
2. Data types are correct
3. Values are within expected ranges
4. No conflicting information
5. Timestamp validity

Return validation status and any issues found."""
        
        result = self.chat(prompt)
        return self._stamp({
            "alert_id": alert.get("id"),
            "validation": result,
            "is_valid": "valid" in result.lower()
        })

    def _format_dict(self, d: dict) -> str:
        """Format dict for prompt."""
        return "\n".join(f"  {k}: {v}" for k, v in d.items())

    def _format_list(self, lst: list) -> str:
        """Format list for prompt."""
        return "\n".join(f"  {i+1}. {item}" for i, item in enumerate(lst))
