"""Escalation logic aligned to the legacy prompts."""

from __future__ import annotations

from datetime import datetime, timezone

from ai_system.app.analysis_utils import format_dict
from ai_system.app.llm import chat


def evaluate_escalation_need(incident: dict, severity_factors: dict) -> dict:
    prompt = f"""Evaluate if this incident requires escalation:

Incident:
{format_dict(incident)}

Severity Factors:
{format_dict(severity_factors)}

Evaluate:
1. Severity level (critical, high, medium, low)
2. Complexity (AI can handle vs needs human)
3. Regulatory implications
4. Customer impact
5. Urgency (time-sensitive)
6. Escalation type (supervisor, compliance, legal, etc.)
7. Recommended escalation path

Return escalation recommendation with reasoning."""
    result = chat(prompt)
    return {
        "agent": "EscalationCaseSummary",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "incident_id": incident.get("id"),
        "needs_escalation": "yes" in (result or "").lower()
        or "escalat" in (result or "").lower(),
        "evaluation": result or "Escalation evaluation unavailable.",
    }
