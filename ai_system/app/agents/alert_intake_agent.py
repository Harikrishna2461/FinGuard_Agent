"""Alert intake logic aligned to the legacy prompts."""

from __future__ import annotations

from datetime import datetime, timezone

from ai_system.app.analysis_utils import format_dict, format_list
from ai_system.app.ml import get_risk_engine
from ai_system.app.llm import chat


def process_alert(alert_source: str, alert_data: dict) -> dict:
    ml_section = ""
    ml_risk_info = None
    if alert_source in ("transaction", "payment", "transfer", "withdrawal"):
        engine = get_risk_engine()
        if engine:
            try:
                ml_result = engine.score(alert_data)
                ml_risk_info = {
                    "risk_score": ml_result["final_score"],
                    "risk_label": ml_result["risk_label"],
                    "method": ml_result["method"],
                    "hard_block": ml_result["hard_block"],
                    "flags": ml_result["flags"],
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
            except Exception:
                pass

    prompt = f"""You are an alert intake specialist. Analyze this incoming financial alert and categorize it.

Alert Source: {alert_source}
Alert Details:
{format_dict(alert_data)}{ml_section}

Categorize by:
1. Type (e.g., anomaly, compliance, risk, market)
2. Priority (critical, high, medium, low)
3. Affected areas (portfolio, account, transactions)
4. Recommended next action

Provide structured analysis for routing to appropriate agents."""
    result = chat(prompt)
    response = {
        "agent": "AlertIntake",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alert_type": alert_source,
        "analysis": result or "Alert categorization unavailable.",
        "categorized": True,
    }
    if ml_risk_info:
        response["ml_risk"] = ml_risk_info
    return response


def filter_alerts(alerts: list) -> dict:
    prompt = f"""You are reviewing {len(alerts)} financial alerts.

Alerts:
{format_list(alerts)}

For each alert:
1. Assess severity
2. Check if it requires immediate escalation
3. Identify any patterns or clusters

Provide prioritized list and escalation recommendations."""
    result = chat(prompt)
    return {
        "agent": "AlertIntake",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "original_count": len(alerts),
        "prioritized_analysis": result or "Alert prioritization unavailable.",
        "requires_escalation": "escalat" in (result or "").lower(),
    }


def validate_alert_integrity(alert: dict) -> dict:
    prompt = f"""Validate the completeness and consistency of this financial alert:

{format_dict(alert)}

Check:
1. All required fields present
2. Data types are correct
3. Values are within expected ranges
4. No conflicting information
5. Timestamp validity

Return validation status and any issues found."""
    result = chat(prompt)
    return {
        "agent": "AlertIntake",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alert_id": alert.get("id"),
        "validation": result or "Alert validation unavailable.",
        "is_valid": "valid" in (result or "").lower(),
    }


class AlertIntakeAgent:
    AGENT_DOMAIN = "alert_intake"

    def process_alert(self, alert_source: str, alert_data: dict) -> dict:
        return process_alert(alert_source, alert_data)

    def filter_alerts(self, alerts: list) -> dict:
        return filter_alerts(alerts)

    def validate_alert_integrity(self, alert: dict) -> dict:
        return validate_alert_integrity(alert)
