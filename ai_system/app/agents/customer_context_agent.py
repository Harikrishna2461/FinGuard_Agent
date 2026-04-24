"""Customer context logic aligned to the legacy prompts."""

from __future__ import annotations

from datetime import datetime, timezone

from ai_system.app.analysis_utils import format_dict, format_list
from ai_system.app.llm import chat


def build_customer_profile(customer_id: str, profile_data: dict) -> dict:
    prompt = f"""You are a customer context specialist. Build a comprehensive profile:

Customer ID: {customer_id}
Available Data:
{format_dict(profile_data)}

Create profile including:
1. Financial situation summary
2. Risk tolerance assessment
3. Investment goals and timeline
4. Behavioral patterns
5. Key constraints and preferences
6. Potential risk factors
7. Recommended service tiers

Provide structured profile for downstream agents."""
    result = chat(prompt)
    return {
        "agent": "CustomerContext",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "customer_id": customer_id,
        "profile": result or "Customer profile unavailable.",
        "profile_complete": True,
    }


def get_customer_history(customer_id: str, history_type: str) -> dict:
    prompt = f"""Retrieve and summarize {history_type} history for customer {customer_id}.

Focus on:
1. Recent patterns and trends
2. Frequency and magnitude of activities
3. Any anomalies or changes in behavior
4. Previous issues and resolutions
5. Customer interactions and outcomes

Provide concise but comprehensive historical context."""
    result = chat(prompt)
    return {
        "agent": "CustomerContext",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "customer_id": customer_id,
        "history_type": history_type,
        "context": result or "Customer history unavailable.",
    }


def assess_customer_needs(customer_id: str, current_situation: dict) -> dict:
    prompt = f"""Assess the current needs for customer {customer_id}:

Current Situation:
{format_dict(current_situation)}

Evaluate:
1. Immediate pain points
2. Strategic financial needs
3. Protection requirements
4. Growth opportunities
5. Compliance concerns
6. Service levels required

Return prioritized needs assessment."""
    result = chat(prompt)
    return {
        "agent": "CustomerContext",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "customer_id": customer_id,
        "needs": result or "Customer needs assessment unavailable.",
        "assessed_at": "now",
    }


def extract_customer_preferences(customer_id: str, interactions: list) -> dict:
    prompt = f"""Extract and summarize preferences from customer {customer_id}'s interactions:

Interactions:
{format_list(interactions)}

Identify:
1. Communication preferences
2. Decision-making style
3. Risk appetite indicators
4. Service channel preferences
5. Reporting and alert preferences
6. Escalation preferences

Return structured preferences profile."""
    result = chat(prompt)
    return {
        "agent": "CustomerContext",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "customer_id": customer_id,
        "preferences": result or "Customer preferences unavailable.",
        "extracted": True,
    }


def get_customer_segment(profile: dict) -> dict:
    prompt = f"""Determine customer segment based on profile:

{format_dict(profile)}

Classify as:
1. Segment type (e.g., premium, standard, high-risk)
2. Service tier
3. Monitoring level (standard, enhanced, intensive)
4. Priority level
5. Recommended products/services

Return segment classification and rationale."""
    result = chat(prompt)
    return {
        "agent": "CustomerContext",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "segment": result or "Customer segment unavailable.",
        "classified": True,
    }


class CustomerContextAgent:
    AGENT_DOMAIN = "customer_context"

    def build_customer_profile(self, customer_id: str, profile_data: dict) -> dict:
        return build_customer_profile(customer_id, profile_data)

    def get_customer_history(self, customer_id: str, history_type: str) -> dict:
        return get_customer_history(customer_id, history_type)

    def assess_customer_needs(self, customer_id: str, current_situation: dict) -> dict:
        return assess_customer_needs(customer_id, current_situation)

    def extract_customer_preferences(self, customer_id: str, interactions: list) -> dict:
        return extract_customer_preferences(customer_id, interactions)

    def get_customer_segment(self, profile: dict) -> dict:
        return get_customer_segment(profile)
