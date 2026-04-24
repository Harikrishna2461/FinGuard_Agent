"""Escalation logic aligned to the legacy prompts."""

from __future__ import annotations

from datetime import datetime, timezone

from ai_system.app.analysis_utils import format_dict, format_list
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


def generate_case_summary(case_data: dict, interactions: list, decisions: list) -> dict:
    prompt = f"""Generate a comprehensive case summary:

Case Information:
{format_dict(case_data)}

Timeline of Interactions:
{format_list(interactions)}

Decisions Made:
{format_list(decisions)}

Summary should include:
1. Case overview (1-2 sentences)
2. Customer context and history
3. Chronological timeline of events
4. Key findings and facts
5. Decisions made and rationale
6. Current status
7. Open items and next steps
8. Risk flags
9. Recommended follow-up actions

Format for easy handoff to specialist."""
    result = chat(prompt)
    return {
        "agent": "EscalationCaseSummary",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "case_id": case_data.get("id"),
        "summary": result or "Case summary unavailable.",
        "ready_for_handoff": True,
    }


def prepare_escalation_package(case: dict, target_team: str) -> dict:
    prompt = f"""Prepare escalation package for {target_team} team:

Case:
{format_dict(case)}

Target Team: {target_team}

Prepare package with:
1. Executive summary appropriate for {target_team}
2. Key facts and evidence
3. Timeline of events
4. AI analysis and conclusions
5. Recommendations for {target_team}
6. Questions requiring specialist input
7. Regulatory/policy references (if compliance/legal)
8. Customer communication recommendations
9. Risk assessment
10. Suggested next steps

Tailor content and emphasis for {target_team} needs."""
    result = chat(prompt)
    return {
        "agent": "EscalationCaseSummary",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "case_id": case.get("id"),
        "target_team": target_team,
        "escalation_package": result or "Escalation package unavailable.",
        "prepared": True,
    }


def summarize_case_resolution(case: dict, resolution: dict) -> dict:
    prompt = f"""Summarize the resolution of this case:

Case:
{format_dict(case)}

Resolution:
{format_dict(resolution)}

Document:
1. How the issue was resolved
2. Actions taken (by whom, when)
3. Outcomes achieved
4. Customer impact
5. Lessons learned
6. Preventive measures for future
7. Case closure status
8. Follow-up schedule (if any)

Format for case records/archive."""
    result = chat(prompt)
    return {
        "agent": "EscalationCaseSummary",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "case_id": case.get("id"),
        "resolution_summary": result or "Case resolution summary unavailable.",
        "summarized": True,
    }


def identify_escalation_pattern(cases: list) -> dict:
    prompt = f"""Analyze these cases for escalation patterns:

Cases:
{format_list(cases)}

Identify:
1. Common escalation triggers
2. Repeated customer or account patterns
3. Process bottlenecks
4. Policy gaps
5. Recommended preventive controls"""
    result = chat(prompt)
    return {
        "agent": "EscalationCaseSummary",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "patterns": result or "Escalation pattern analysis unavailable.",
        "case_count": len(cases),
    }


def draft_escalation_communication(case: dict, customer: dict, message_type: str) -> dict:
    prompt = f"""Draft {message_type} escalation communication.

Case:
{format_dict(case)}

Customer:
{format_dict(customer)}

Make the message clear, professional, and appropriate for the target audience."""
    result = chat(prompt)
    return {
        "agent": "EscalationCaseSummary",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "case_id": case.get("id"),
        "message_type": message_type,
        "draft": result or "Escalation communication unavailable.",
    }


class EscalationCaseSummaryAgent:
    AGENT_DOMAIN = "escalation"

    def evaluate_escalation_need(self, incident: dict, severity_factors: dict) -> dict:
        return evaluate_escalation_need(incident, severity_factors)

    def generate_case_summary(self, case_data: dict, interactions: list, decisions: list) -> dict:
        return generate_case_summary(case_data, interactions, decisions)

    def prepare_escalation_package(self, case: dict, target_team: str) -> dict:
        return prepare_escalation_package(case, target_team)

    def summarize_case_resolution(self, case: dict, resolution: dict) -> dict:
        return summarize_case_resolution(case, resolution)

    def identify_escalation_pattern(self, cases: list) -> dict:
        return identify_escalation_pattern(cases)

    def draft_escalation_communication(self, case: dict, customer: dict, message_type: str) -> dict:
        return draft_escalation_communication(case, customer, message_type)
