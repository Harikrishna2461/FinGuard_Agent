"""Explanation logic aligned to the legacy prompts."""

from __future__ import annotations

from datetime import datetime, timezone

from ai_system.app.analysis_utils import format_dict
from ai_system.app.llm import chat


def invoke(portfolio: dict, transactions: list[dict], findings: list[str]) -> dict:
    if findings:
        narrative = (
            f"Portfolio '{portfolio.get('name', 'Unnamed Portfolio')}' was reviewed across "
            f"{len(transactions)} recent transactions. " + " ".join(findings)
        )
    else:
        narrative = (
            f"Portfolio '{portfolio.get('name', 'Unnamed Portfolio')}' was reviewed and "
            "no material finding was surfaced in the quick path."
        )

    return {
        "agent": "Explanation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": narrative,
    }


def explain_alert(alert: dict, audience: str = "customer") -> dict:
    prompt = f"""Explain this financial alert for a {audience} audience:

Alert:
{format_dict(alert)}

Provide explanation that:
1. Is clear and accessible
2. Avoids unnecessary jargon (adjust for audience)
3. Explains why this matters
4. Lists recommended actions
5. Provides reassurance where appropriate
6. Includes relevant context

Tone: {'conversational' if audience == 'customer' else 'professional'}
Detail level: {'simplified' if audience == 'customer' else 'comprehensive'}

Return well-structured explanation."""
    result = chat(prompt)
    return {
        "agent": "Explanation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alert_id": alert.get("id"),
        "audience": audience,
        "explanation": result or "Alert explanation unavailable.",
    }


def explain_recommendation(recommendation: dict, customer_profile: dict) -> dict:
    prompt = f"""Explain why this recommendation is suitable:

Recommendation:
{format_dict(recommendation)}

Customer Profile:
{format_dict(customer_profile)}

Explain:
1. Why this recommendation was made
2. How it addresses customer goals
3. Risk implications
4. Expected outcomes
5. Alternatives considered and why not recommended
6. Next steps

Return detailed but accessible explanation."""
    result = chat(prompt)
    return {
        "agent": "Explanation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "recommendation_id": recommendation.get("id"),
        "explained": True,
        "explanation": result or "Recommendation explanation unavailable.",
    }


def explain_risk_score(transaction: dict, score: float, factors: dict) -> dict:
    prompt = f"""Explain this transaction risk score:

Transaction:
{format_dict(transaction)}

Risk Score: {score}/100

Contributing Factors:
{format_dict(factors)}

Explain:
1. What the score means
2. Which factors drove the score
3. Any concerning patterns
4. Context (is this unusual for this customer?)
5. What can be done about it
6. When it might be reviewed

Return clear, non-alarming explanation."""
    result = chat(prompt)
    return {
        "transaction_id": transaction.get("id"),
        "score_explained": score,
        "explanation": result,
        "agent": "Explanation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def explain_portfolio_performance(portfolio: dict, performance: dict) -> dict:
    prompt = f"""Explain this portfolio's performance to the customer:

Portfolio:
{format_dict(portfolio)}

Performance:
{format_dict(performance)}

Explain:
1. Overall performance summary
2. Which holdings performed well/poorly
3. Why performance occurred (market factors)
4. Comparison to relevant benchmarks
5. Forward outlook
6. Any adjustments needed

Balance honesty with reassurance when appropriate."""
    result = chat(prompt)
    return {
        "agent": "Explanation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "portfolio_id": portfolio.get("id"),
        "explained": True,
        "explanation": result or "Portfolio performance explanation unavailable.",
    }


def explain_compliance_finding(finding: dict, customer_context: dict) -> dict:
    prompt = f"""Explain this compliance issue to the customer:

Finding:
{format_dict(finding)}

Customer Context:
{format_dict(customer_context)}

Explain:
1. What the issue is
2. Why it matters
3. What needs to happen next
4. Timeline for resolution
5. What the customer needs to do (if anything)
6. Reassurance appropriately

Tone: Professional but not threatening."""
    result = chat(prompt)
    return {
        "agent": "Explanation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "finding_id": finding.get("id"),
        "explained": True,
        "explanation": result or "Compliance finding explanation unavailable.",
    }


def explain_transaction_risk(transaction: dict, score: float, factors: dict) -> dict:
    try:
        result = explain_risk_score(transaction, score, factors)
        return {
            "insights": result.get("explanation", ""),
            "agent": "Explanation",
            "timestamp": result.get(
                "timestamp", datetime.now(timezone.utc).isoformat()
            ),
            "success": True,
        }
    except Exception as exc:
        error_msg = str(exc)

    risk_level = (
        "CRITICAL"
        if score >= 80
        else "HIGH"
        if score >= 55
        else "MEDIUM"
        if score >= 30
        else "LOW"
    )
    fallback_insights = (
        f"**Risk Assessment Summary**\n"
        f"Risk Score: {score}/100\n"
        f"Risk Level: {risk_level}\n\n"
        f"**Contributing Factors**\n"
    )
    for key, value in factors.items():
        fallback_insights += f"- {key}: {value}\n"
    fallback_insights += f"\n**Analysis**\nThe combination of these factors indicates {risk_level.lower()} risk. "
    if score >= 80:
        fallback_insights += (
            "Immediate action is recommended:\n"
            "- Review transaction details carefully\n"
            "- Consider blocking the transaction\n"
            "- Contact the customer if appropriate"
        )
    elif score >= 55:
        fallback_insights += (
            "Further investigation recommended:\n"
            "- Gather additional context\n"
            "- Monitor for related activity\n"
            "- Escalate if patterns emerge"
        )
    else:
        fallback_insights += "Continue routine monitoring."
    fallback_insights += f"\n\n**Error Details**\n{error_msg}"
    return {
        "insights": fallback_insights,
        "agent": "Explanation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "success": False,
        "error_reason": error_msg,
    }


def summarize_analysis(analysis_results: dict, detail_level: str = "medium") -> dict:
    prompt = f"""Summarize this analysis at {detail_level} detail level:

Analysis Results:
{format_dict(analysis_results)}

Provide:
1. Executive summary (2-3 sentences)
2. Key findings (bullet points)
3. Implications
4. Recommended actions
5. Follow-up items

Detail level: {detail_level}"""
    result = chat(prompt)
    return {
        "agent": "Explanation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": result or "Summary unavailable.",
        "detail_level": detail_level,
    }


class ExplanationAgent:
    AGENT_DOMAIN = "explanation"

    def explain_alert(self, alert: dict, audience: str = "customer") -> dict:
        return explain_alert(alert, audience)

    def explain_recommendation(self, recommendation: dict, customer_profile: dict) -> dict:
        return explain_recommendation(recommendation, customer_profile)

    def explain_risk_score(self, transaction: dict, score: float, factors: dict) -> dict:
        return explain_risk_score(transaction, score, factors)

    def explain_portfolio_performance(self, portfolio: dict, performance: dict) -> dict:
        return explain_portfolio_performance(portfolio, performance)

    def explain_compliance_finding(self, finding: dict, customer_context: dict) -> dict:
        return explain_compliance_finding(finding, customer_context)

    def summarize_analysis(self, analysis_results: dict, detail_level: str = "medium") -> dict:
        return summarize_analysis(analysis_results, detail_level)
