"""Legacy-named agent modules for the ai_system runtime."""

from ai_system.app.agents.alert_intake_agent import AlertIntakeAgent
from ai_system.app.agents.compliance_agent import ComplianceAgent
from ai_system.app.agents.customer_context_agent import CustomerContextAgent
from ai_system.app.agents.escalation_case_summary_agent import EscalationCaseSummaryAgent
from ai_system.app.agents.explanation_agent import ExplanationAgent
from ai_system.app.agents.market_intelligence_agent import MarketIntelligenceAgent
from ai_system.app.agents.portfolio_analysis_agent import PortfolioAnalysisAgent
from ai_system.app.agents.risk_assessment_agent import RiskAssessmentAgent, RiskDetectionAgent


__all__ = [
    "AlertIntakeAgent",
    "ComplianceAgent",
    "CustomerContextAgent",
    "EscalationCaseSummaryAgent",
    "ExplanationAgent",
    "MarketIntelligenceAgent",
    "PortfolioAnalysisAgent",
    "RiskAssessmentAgent",
    "RiskDetectionAgent",
]
