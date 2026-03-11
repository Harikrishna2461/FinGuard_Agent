"""
agents package  –  Each agent lives in its own file for independent development.

  base_agent.py                 →  FinancialBaseAgent  (shared Groq wrapper)
  portfolio_analysis_agent.py   →  PortfolioAnalysisAgent
  risk_detection_agent.py       →  RiskDetectionAgent
  market_intelligence_agent.py  →  MarketIntelligenceAgent
  compliance_agent.py           →  ComplianceAgent
  crew_orchestrator.py          →  AIAgentOrchestrator  (CrewAI-based)
  financial_agents.py           →  compatibility shim (re-exports all above)
"""
