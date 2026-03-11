"""Explanation Agent - Explains AI decisions and findings to stakeholders."""

from agents.base_agent import FinancialBaseAgent


class ExplanationAgent(FinancialBaseAgent):

    def __init__(self):
        super().__init__("Explanation")
    """
    Explains AI-driven decisions, findings, and recommendations in plain language
    tailored to different stakeholders (customers, advisors, compliance, executives).
    """

    def explain_alert(self, alert: dict, audience: str = "customer") -> dict:
        """
        Explain an alert in language appropriate for the audience.
        
        Args:
            alert: The alert object with details
            audience: 'customer', 'advisor', 'compliance', 'executive'
            
        Returns:
            Explanation in appropriate language and detail level
        """
        prompt = f"""Explain this financial alert for a {audience} audience:

Alert:
{self._format_dict(alert)}

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
        
        result = self.chat(prompt)
        return self._stamp({
            "alert_id": alert.get("id"),
            "audience": audience,
            "explanation": result
        })

    def explain_recommendation(self, recommendation: dict, customer_profile: dict) -> dict:
        """Explain a recommendation and why it's suitable for this customer."""
        prompt = f"""Explain why this recommendation is suitable:

Recommendation:
{self._format_dict(recommendation)}

Customer Profile:
{self._format_dict(customer_profile)}

Explain:
1. Why this recommendation was made
2. How it addresses customer goals
3. Risk implications
4. Expected outcomes
5. Alternatives considered and why not recommended
6. Next steps

Return detailed but accessible explanation."""
        
        result = self.chat(prompt)
        return self._stamp({
            "recommendation_id": recommendation.get("id"),
            "explained": True,
            "explanation": result
        })

    def explain_risk_score(self, transaction: dict, score: float, factors: dict) -> dict:
        """Explain a risk score and the factors that contributed to it."""
        prompt = f"""Explain this transaction risk score:

Transaction:
{self._format_dict(transaction)}

Risk Score: {score}/100

Contributing Factors:
{self._format_dict(factors)}

Explain:
1. What the score means
2. Which factors drove the score
3. Any concerning patterns
4. Context (is this unusual for this customer?)
5. What can be done about it
6. When it might be reviewed

Return clear, non-alarming explanation."""
        
        result = self.chat(prompt)
        return self._stamp({
            "transaction_id": transaction.get("id"),
            "score_explained": score,
            "explanation": result
        })

    def explain_portfolio_performance(self, portfolio: dict, performance: dict) -> dict:
        """Explain portfolio performance in accessible terms."""
        prompt = f"""Explain this portfolio's performance to the customer:

Portfolio:
{self._format_dict(portfolio)}

Performance:
{self._format_dict(performance)}

Explain:
1. Overall performance summary
2. Which holdings performed well/poorly
3. Why performance occurred (market factors)
4. Comparison to relevant benchmarks
5. Forward outlook
6. Any adjustments needed

Balance honesty with reassurance when appropriate."""
        
        result = self.chat(prompt)
        return self._stamp({
            "portfolio_id": portfolio.get("id"),
            "explained": True,
            "explanation": result
        })

    def explain_compliance_finding(self, finding: dict, customer_context: dict) -> dict:
        """Explain a compliance issue to the customer."""
        prompt = f"""Explain this compliance issue to the customer:

Finding:
{self._format_dict(finding)}

Customer Context:
{self._format_dict(customer_context)}

Explain:
1. What the issue is
2. Why it matters
3. What needs to happen next
4. Timeline for resolution
5. What the customer needs to do (if anything)
6. Reassurance appropriately

Tone: Professional but not threatening."""
        
        result = self.chat(prompt)
        return self._stamp({
            "finding_id": finding.get("id"),
            "explained": True,
            "explanation": result
        })

    def summarize_analysis(self, analysis_results: dict, detail_level: str = "medium") -> dict:
        """
        Summarize complex analysis in a concise format.
        
        Args:
            analysis_results: Dict of analysis outputs
            detail_level: 'brief', 'medium', 'detailed'
        """
        prompt = f"""Summarize this analysis at {detail_level} detail level:

Analysis Results:
{self._format_dict(analysis_results)}

Provide:
1. Executive summary (2-3 sentences)
2. Key findings (bullet points)
3. Implications
4. Recommended actions
5. Follow-up items

Detail level: {detail_level}"""
        
        result = self.chat(prompt)
        return self._stamp({
            "summary": result,
            "detail_level": detail_level
        })

    def _format_dict(self, d: dict) -> str:
        """Format dict for prompt."""
        return "\n".join(f"  {k}: {v}" for k, v in d.items())
