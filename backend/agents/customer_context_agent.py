"""Customer Context Agent - Maintains and retrieves customer/user context for analysis."""

from agents.base_agent import FinancialBaseAgent


class CustomerContextAgent(FinancialBaseAgent):

    AGENT_DOMAIN = "customer_context"

    AGENT_DOMAIN = "customer_context"

    def __init__(self):
        super().__init__("CustomerContext")
    """
    Retrieves and maintains comprehensive customer context including profile,
    preferences, history, and behavioral patterns for personalized analysis.
    """

    def build_customer_profile(self, customer_id: str, profile_data: dict) -> dict:
        """
        Build comprehensive customer profile from available data.
        
        Args:
            customer_id: Unique customer identifier
            profile_data: Dict with customer details (age, risk profile, income, etc.)
            
        Returns:
            Enriched customer profile with context
        """
        prompt = f"""You are a customer context specialist. Build a comprehensive profile:

Customer ID: {customer_id}
Available Data:
{self._format_dict(profile_data)}

Create profile including:
1. Financial situation summary
2. Risk tolerance assessment
3. Investment goals and timeline
4. Behavioral patterns
5. Key constraints and preferences
6. Potential risk factors
7. Recommended service tiers

Provide structured profile for downstream agents."""
        
        result = self.chat(prompt)
        return self._stamp({
            "customer_id": customer_id,
            "profile": result,
            "profile_complete": True
        })

    def get_customer_history(self, customer_id: str, history_type: str) -> dict:
        """
        Retrieve relevant customer history for context.
        
        Args:
            customer_id: Customer identifier
            history_type: Type of history ('transactions', 'alerts', 'decisions', 'all')
            
        Returns:
            Relevant historical context
        """
        prompt = f"""Retrieve and summarize {history_type} history for customer {customer_id}.

Focus on:
1. Recent patterns and trends
2. Frequency and magnitude of activities
3. Any anomalies or changes in behavior
4. Previous issues and resolutions
5. Customer interactions and outcomes

Provide concise but comprehensive historical context."""
        
        result = self.chat(prompt)
        return self._stamp({
            "customer_id": customer_id,
            "history_type": history_type,
            "context": result
        })

    def assess_customer_needs(self, customer_id: str, current_situation: dict) -> dict:
        """Assess current customer needs based on situation."""
        prompt = f"""Assess the current needs for customer {customer_id}:

Current Situation:
{self._format_dict(current_situation)}

Evaluate:
1. Immediate pain points
2. Strategic financial needs
3. Protection requirements
4. Growth opportunities
5. Compliance concerns
6. Service levels required

Return prioritized needs assessment."""
        
        result = self.chat(prompt)
        return self._stamp({
            "customer_id": customer_id,
            "needs": result,
            "assessed_at": "now"
        })

    def extract_customer_preferences(self, customer_id: str, interactions: list) -> dict:
        """Extract customer preferences from interaction history."""
        prompt = f"""Extract and summarize preferences from customer {customer_id}'s interactions:

Interactions:
{self._format_list(interactions)}

Identify:
1. Communication preferences
2. Decision-making style
3. Risk appetite indicators
4. Service channel preferences
5. Reporting and alert preferences
6. Escalation preferences

Return structured preferences profile."""
        
        result = self.chat(prompt)
        return self._stamp({
            "customer_id": customer_id,
            "preferences": result,
            "extracted": True
        })

    def get_customer_segment(self, profile: dict) -> dict:
        """Determine customer segment for targeted analysis."""
        prompt = f"""Determine customer segment based on profile:

{self._format_dict(profile)}

Classify as:
1. Segment type (e.g., premium, standard, high-risk)
2. Service tier
3. Monitoring level (standard, enhanced, intensive)
4. Priority level
5. Recommended products/services

Return segment classification and rationale."""
        
        result = self.chat(prompt)
        return self._stamp({
            "segment": result,
            "classified": True
        })

    def _format_dict(self, d: dict) -> str:
        """Format dict for prompt."""
        return "\n".join(f"  {k}: {v}" for k, v in d.items())

    def _format_list(self, lst: list) -> str:
        """Format list for prompt."""
        return "\n".join(f"  {i+1}. {item}" for i, item in enumerate(lst))
