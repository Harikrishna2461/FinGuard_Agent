"""
financial_agents.py  –  COMPATIBILITY SHIM

All agent classes have been moved to individual files for team collaboration:

NEW (5 agents):
  • agents/alert_intake_agent.py          →  AlertIntakeAgent
  • agents/customer_context_agent.py      →  CustomerContextAgent
  • agents/risk_assessment_agent.py       →  RiskAssessmentAgent
  • agents/explanation_agent.py           →  ExplanationAgent
  • agents/escalation_case_summary_agent.py  →  EscalationCaseSummaryAgent

EXISTING (4 agents):
  • agents/portfolio_analysis_agent.py    →  PortfolioAnalysisAgent
  • agents/risk_detection_agent.py        →  RiskDetectionAgent
  • agents/market_intelligence_agent.py   →  MarketIntelligenceAgent
  • agents/compliance_agent.py            →  ComplianceAgent

INFRASTRUCTURE:
  • agents/base_agent.py                  →  FinancialBaseAgent
  • agents/crew_orchestrator.py           →  AIAgentOrchestrator (CrewAI)

This file re-exports all 9 agents + infrastructure so existing imports still work.
"""

# Base class
from agents.base_agent import FinancialBaseAgent as FinancialAIAgent   # noqa

# 5 NEW agents
from agents.alert_intake_agent import AlertIntakeAgent                 # noqa
from agents.customer_context_agent import CustomerContextAgent         # noqa
from agents.risk_assessment_agent import RiskAssessmentAgent           # noqa
from agents.explanation_agent import ExplanationAgent                  # noqa
from agents.escalation_case_summary_agent import EscalationCaseSummaryAgent  # noqa

# 4 EXISTING agents
from agents.portfolio_analysis_agent import PortfolioAnalysisAgent     # noqa
from agents.risk_detection_agent import RiskDetectionAgent             # noqa
from agents.market_intelligence_agent import MarketIntelligenceAgent   # noqa
from agents.compliance_agent import ComplianceAgent                    # noqa

# Orchestrator
from agents.crew_orchestrator import AIAgentOrchestrator               # noqa

