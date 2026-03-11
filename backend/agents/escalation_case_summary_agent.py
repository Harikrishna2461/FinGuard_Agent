"""Escalation and Case Summary Agent - Handles escalations and generates case summaries."""

from agents.base_agent import FinancialBaseAgent


class EscalationCaseSummaryAgent(FinancialBaseAgent):

    def __init__(self):
        super().__init__("EscalationCaseSummary")
    """
    Manages escalation workflows and generates comprehensive case summaries
    for handoff to human specialists or higher-level review.
    """

    def evaluate_escalation_need(self, incident: dict, severity_factors: dict) -> dict:
        """
        Evaluate whether an incident requires escalation.
        
        Args:
            incident: Incident details
            severity_factors: Dict of factors affecting severity
            
        Returns:
            Escalation evaluation and recommendation
        """
        prompt = f"""Evaluate if this incident requires escalation:

Incident:
{self._format_dict(incident)}

Severity Factors:
{self._format_dict(severity_factors)}

Evaluate:
1. Severity level (critical, high, medium, low)
2. Complexity (AI can handle vs needs human)
3. Regulatory implications
4. Customer impact
5. Urgency (time-sensitive)
6. Escalation type (supervisor, compliance, legal, etc.)
7. Recommended escalation path

Return escalation recommendation with reasoning."""
        
        result = self.chat(prompt)
        return self._stamp({
            "incident_id": incident.get("id"),
            "needs_escalation": "yes" in result.lower() or "escalat" in result.lower(),
            "evaluation": result
        })

    def generate_case_summary(self, case_data: dict, interactions: list, decisions: list) -> dict:
        """
        Generate comprehensive case summary for handoff.
        
        Args:
            case_data: Basic case information
            interactions: List of interactions/events
            decisions: List of decisions made
            
        Returns:
            Formatted case summary
        """
        prompt = f"""Generate a comprehensive case summary:

Case Information:
{self._format_dict(case_data)}

Timeline of Interactions:
{self._format_list(interactions)}

Decisions Made:
{self._format_list(decisions)}

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
        
        result = self.chat(prompt)
        return self._stamp({
            "case_id": case_data.get("id"),
            "summary": result,
            "ready_for_handoff": True
        })

    def prepare_escalation_package(self, case: dict, target_team: str) -> dict:
        """
        Prepare case documentation for escalation to specific team.
        
        Args:
            case: Complete case information
            target_team: Team receiving escalation ('compliance', 'legal', 'supervisor')
            
        Returns:
            Escalation package with team-specific content
        """
        prompt = f"""Prepare escalation package for {target_team} team:

Case:
{self._format_dict(case)}

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
        
        result = self.chat(prompt)
        return self._stamp({
            "case_id": case.get("id"),
            "target_team": target_team,
            "escalation_package": result,
            "prepared": True
        })

    def summarize_case_resolution(self, case: dict, resolution: dict) -> dict:
        """Summarize how a case was resolved for documentation."""
        prompt = f"""Summarize the resolution of this case:

Case:
{self._format_dict(case)}

Resolution:
{self._format_dict(resolution)}

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
        
        result = self.chat(prompt)
        return self._stamp({
            "case_id": case.get("id"),
            "resolution_summary": result,
            "closed": True
        })

    def identify_escalation_pattern(self, cases: list) -> dict:
        """Identify patterns in escalated cases for process improvement."""
        prompt = f"""Analyze patterns in these escalated cases:

Cases:
{self._format_list(cases)}

Identify:
1. Common root causes
2. Most frequent issue types
3. Teams most involved in escalations
4. Resolution timeframes
5. Success rates by type
6. Customer segments most likely to escalate
7. Preventable escalations
8. Process improvements needed

Return pattern analysis and recommendations."""
        
        result = self.chat(prompt)
        return self._stamp({
            "cases_analyzed": len(cases),
            "pattern_analysis": result,
            "process_improvements": True
        })

    def draft_escalation_communication(self, case: dict, customer: dict, message_type: str) -> dict:
        """
        Draft communication to customer about escalation.
        
        Args:
            case: Case details
            customer: Customer info
            message_type: 'notification', 'update', 'resolution'
            
        Returns:
            Draft communication
        """
        prompt = f"""Draft {message_type} communication to customer:

Case:
{self._format_dict(case)}

Customer:
{self._format_dict(customer)}

Message Type: {message_type}

Draft:
1. Professional greeting
2. Clear explanation of status (if notification/update)
3. What we're doing about it
4. Timeline and next steps
5. Customer action items (if any)
6. Support/contact information
7. Reassurance and confidence in resolution

Tone: Professional, empathetic, clear."""
        
        result = self.chat(prompt)
        return self._stamp({
            "case_id": case.get("id"),
            "communication_type": message_type,
            "draft": result,
            "ready_to_send": True
        })

    def _format_dict(self, d: dict) -> str:
        """Format dict for prompt."""
        return "\n".join(f"  {k}: {v}" for k, v in d.items())

    def _format_list(self, lst: list) -> str:
        """Format list for prompt."""
        return "\n".join(f"  {i+1}. {item}" for i, item in enumerate(lst))
