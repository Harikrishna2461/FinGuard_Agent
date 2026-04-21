#!/usr/bin/env python3
"""Quick verification that the knowledge base is loaded and RAG works."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import vector_store

print("Test 1: vector_store module")
print("  OK")

print("Test 2: knowledge_base collection count")
col = vector_store._col(vector_store.KNOWLEDGE)
count = col.count()
print(f"  {count} documents in knowledge_base collection")
assert count > 0, "No documents loaded!"

print("Test 3: get_rag_context")
ctx = vector_store.get_rag_context("What is Value at Risk?", "risk_assessment", n=2)
print(f"  Returned {len(ctx)} chars")
assert len(ctx) > 100, "RAG context too short"

print("Test 4: All 9 domains return results")
domains = [
    "alert_intake", "compliance", "customer_context", "escalation",
    "explanation", "market_intelligence", "portfolio_analysis",
    "risk_assessment", "risk_detection",
]
for d in domains:
    r = vector_store.search_knowledge("overview", agent_domain=d, n=1)
    assert len(r) > 0, f"No results for domain {d}"
    print(f"  {d:25s} -> OK")

print("Test 5: base_agent RAG integration")
from agents.base_agent import FinancialBaseAgent
assert hasattr(FinancialBaseAgent, "AGENT_DOMAIN")
assert hasattr(FinancialBaseAgent, "_get_rag_context")
print("  OK")

print("Test 6: All agents have AGENT_DOMAIN")
from agents.alert_intake_agent import AlertIntakeAgent
from agents.compliance_agent import ComplianceAgent
from agents.customer_context_agent import CustomerContextAgent
from agents.escalation_case_summary_agent import EscalationCaseSummaryAgent
from agents.explanation_agent import ExplanationAgent
from agents.market_intelligence_agent import MarketIntelligenceAgent
from agents.portfolio_analysis_agent import PortfolioAnalysisAgent
from agents.risk_assessment_agent import RiskAssessmentAgent
from agents.risk_detection_agent import RiskDetectionAgent

agent_classes = [
    AlertIntakeAgent, ComplianceAgent, CustomerContextAgent,
    EscalationCaseSummaryAgent, ExplanationAgent,
    MarketIntelligenceAgent, PortfolioAnalysisAgent,
    RiskAssessmentAgent, RiskDetectionAgent,
]
for cls in agent_classes:
    assert cls.AGENT_DOMAIN is not None, f"{cls.__name__} missing AGENT_DOMAIN"
    print(f"  {cls.__name__:35s} -> domain={cls.AGENT_DOMAIN}")

print()
print("=" * 50)
print("ALL CHECKS PASSED")
print("=" * 50)
