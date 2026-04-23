"""Alert intake logic aligned to the legacy prompts."""

from __future__ import annotations

from datetime import datetime, timezone

from ai_system.app.analysis_utils import format_dict
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
