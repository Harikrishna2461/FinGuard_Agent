"""Customer context logic aligned to the legacy prompts."""

from __future__ import annotations

from datetime import datetime, timezone

from ai_system.app.analysis_utils import format_dict
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
