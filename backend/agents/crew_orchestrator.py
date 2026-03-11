"""
crew_orchestrator.py  –  CrewAI-based multi-agent orchestrator.

Assembles nine specialist CrewAI Agent objects and runs them as a Crew
to produce comprehensive financial analysis. Also exposes thin, direct
wrappers around each standalone agent for single-purpose API calls.

Agents:
  1. Alert Intake Agent - receives and processes alerts
  2. Customer Context Agent - maintains customer context
  3. Risk Assessment Agent - comprehensive risk evaluation
  4. Explanation Agent - explains findings to stakeholders
  5. Escalation & Case Summary Agent - manages escalations
  6. Portfolio Analysis Agent - asset allocation analysis
  7. Risk Detection Agent - fraud and risk detection
  8. Market Intelligence Agent - market sentiment and trends
  9. Compliance Agent - regulatory compliance review
"""

import os, json
from typing import Dict, Any, List
from datetime import datetime

from crewai import Agent, Task, Crew, Process, LLM

# ── 5 NEW specialist agent classes ────────────────────────────────
from agents.alert_intake_agent import AlertIntakeAgent
from agents.customer_context_agent import CustomerContextAgent
from agents.risk_assessment_agent import RiskAssessmentAgent
from agents.explanation_agent import ExplanationAgent
from agents.escalation_case_summary_agent import EscalationCaseSummaryAgent

# ── 4 existing agent classes ──────────────────────────────────────
from agents.portfolio_analysis_agent import PortfolioAnalysisAgent
from agents.risk_detection_agent import RiskDetectionAgent
from agents.market_intelligence_agent import MarketIntelligenceAgent
from agents.compliance_agent import ComplianceAgent

# ── CrewAI tool functions ─────────────────────────────────────────
from agents.tools.portfolio_tools import (
    analyze_allocation,
    calculate_diversification,
    recommend_rebalance,
)
from agents.tools.risk_tools import (
    detect_fraud_patterns,
    assess_market_risk,
    evaluate_concentration,
)
from agents.tools.market_tools import (
    analyze_sentiment,
    identify_trends,
    generate_recommendations,
)
from agents.tools.compliance_tools import (
    check_pdt_violations,
    identify_wash_sales,
    generate_tax_report,
)

# ── vector store (ChromaDB) ───────────────────────────────────────
import vector_store

# =====================================================================
#  Groq LLM helper (shared by every CrewAI Agent)
# =====================================================================
def _groq_llm() -> LLM:
    """Create a CrewAI-compatible Groq LLM instance."""
    return LLM(
        model="groq/" + os.getenv("GROQ_MODEL", "mixtral-8x7b-32768"),
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.7,
    )


# =====================================================================
#  CrewAI Agent definitions (9 total)
# =====================================================================
def _alert_intake_crew_agent() -> Agent:
    return Agent(
        role="Alert Intake Specialist",
        goal="Receive, categorize and prioritize financial alerts from all sources.",
        backstory=(
            "You are an alert management expert with experience at tier-1 "
            "financial institutions, skilled at rapid alert triage and routing."
        ),
        llm=_groq_llm(),
        verbose=False,
    )


def _customer_context_crew_agent() -> Agent:
    return Agent(
        role="Customer Context Manager",
        goal="Maintain and provide comprehensive customer context for all decisions.",
        backstory=(
            "You are a customer relationship specialist who understands "
            "customer profiles, history, preferences and behavioral patterns."
        ),
        llm=_groq_llm(),
        verbose=False,
    )


def _risk_assessment_crew_agent() -> Agent:
    return Agent(
        role="Risk Assessment Specialist",
        goal="Perform comprehensive risk evaluation and scoring across all dimensions.",
        backstory=(
            "You are a quantitative risk analyst with expertise in VaR, "
            "correlation analysis and systemic risk identification."
        ),
        llm=_groq_llm(),
        verbose=False,
    )


def _explanation_crew_agent() -> Agent:
    return Agent(
        role="Explanation Specialist",
        goal="Explain AI findings and recommendations in clear, stakeholder-appropriate language.",
        backstory=(
            "You are an expert communicator who translates complex financial "
            "analysis into clear explanations for diverse audiences."
        ),
        llm=_groq_llm(),
        verbose=False,
    )


def _escalation_crew_agent() -> Agent:
    return Agent(
        role="Escalation and Case Manager",
        goal="Manage escalations and generate comprehensive case summaries for handoff.",
        backstory=(
            "You are a case management expert skilled at documenting complex "
            "cases and preparing them for specialist review."
        ),
        llm=_groq_llm(),
        verbose=False,
    )


def _portfolio_crew_agent() -> Agent:
    return Agent(
        role="Portfolio Analyst",
        goal="Analyse asset allocation, diversification and rebalancing opportunities.",
        backstory=(
            "You are a CFA-certified portfolio analyst with 15 years of "
            "experience managing multi-asset portfolios worth over $500 M."
        ),
        tools=[analyze_allocation, calculate_diversification, recommend_rebalance],
        llm=_groq_llm(),
        verbose=False,
    )


def _risk_crew_agent() -> Agent:
    return Agent(
        role="Risk & Fraud Detective",
        goal="Detect fraud, market risk, and concentration risk in portfolios.",
        backstory=(
            "You are a risk management expert who previously led the fraud "
            "detection division at a top-tier investment bank."
        ),
        tools=[detect_fraud_patterns, assess_market_risk, evaluate_concentration],
        llm=_groq_llm(),
        verbose=False,
    )


def _market_crew_agent() -> Agent:
    return Agent(
        role="Market Intelligence Analyst",
        goal="Provide market sentiment, trend analysis and investment recommendations.",
        backstory=(
            "You are a senior sell-side equity strategist who publishes "
            "weekly market outlook reports read by institutional investors."
        ),
        tools=[analyze_sentiment, identify_trends, generate_recommendations],
        llm=_groq_llm(),
        verbose=False,
    )


def _compliance_crew_agent() -> Agent:
    return Agent(
        role="Compliance Officer",
        goal="Review transactions for PDT, wash-sale, AML violations and generate tax reports.",
        backstory=(
            "You are a licensed compliance officer specialising in SEC and "
            "FINRA regulations for retail brokerage accounts."
        ),
        tools=[check_pdt_violations, identify_wash_sales, generate_tax_report],
        llm=_groq_llm(),
        verbose=False,
    )


# =====================================================================
#  Orchestrator  –  public API consumed by Flask routes
# =====================================================================

class AIAgentOrchestrator:
    """
    Wraps *both* the standalone Groq-powered agents (for quick, single-purpose
    calls) and the full CrewAI Crew (for comprehensive multi-agent review).
    
    9 agents total for complete financial analysis:
      - 5 NEW: Alert Intake, Customer Context, Risk Assessment, Explanation, Escalation
      - 4 EXISTING: Portfolio Analysis, Risk Detection, Market Intelligence, Compliance
    
    Transaction risk scoring uses the hybrid ML pipeline (Rules + ML models)
    automatically wherever transactions appear.
    """

    def __init__(self):
        # 5 NEW standalone agents (direct Groq calls)
        self.alert_intake_agent = AlertIntakeAgent()
        self.customer_context_agent = CustomerContextAgent()
        self.risk_assessment_agent = RiskAssessmentAgent()
        self.explanation_agent = ExplanationAgent()
        self.escalation_agent = EscalationCaseSummaryAgent()
        
        # 4 EXISTING standalone agents (direct Groq calls)
        self.portfolio_agent = PortfolioAnalysisAgent()
        self.risk_agent = RiskDetectionAgent()
        self.market_agent = MarketIntelligenceAgent()
        self.compliance_agent = ComplianceAgent()

        # ML risk engine (lazy-loaded)
        self._risk_engine = None

    def _get_risk_engine(self):
        """Lazy-load the hybrid ML risk scoring engine."""
        if self._risk_engine is None:
            try:
                from ml.risk_scoring_engine import TransactionRiskEngine
                self._risk_engine = TransactionRiskEngine()
            except Exception:
                pass
        return self._risk_engine

    def _ml_score_transactions(self, transactions: list) -> str:
        """
        Run ML scoring on a list of transactions and return a text summary
        that can be injected into CrewAI task descriptions.
        """
        engine = self._get_risk_engine()
        if not engine or not transactions:
            return ""

        lines = ["\n\n── ML Risk Pre-Screening Results ──"]
        high_risk_count = 0
        for i, txn in enumerate(transactions[:20]):
            try:
                result = engine.score(txn)
                label = result["risk_label"]
                flags = result["flags"]
                if label in ("high", "critical"):
                    high_risk_count += 1
                lines.append(
                    f"  Txn {i+1}: score={result['final_score']}/100 "
                    f"label={label} method={result['method']} "
                    f"hard_block={result['hard_block']} "
                    f"flags=[{', '.join(flags)}]"
                )
            except Exception:
                lines.append(f"  Txn {i+1}: ML scoring failed")

        lines.insert(1, f"  Total scanned: {len(transactions[:20])} | High/Critical: {high_risk_count}")
        return "\n".join(lines)

    # ─── comprehensive review via CrewAI (all 9 agents) ──────────
    def comprehensive_portfolio_review(
        self,
        portfolio_data: Dict[str, Any],
        transactions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Spin up a CrewAI Crew with nine specialist agents.
        Each agent is given a Task; the Crew runs them sequentially
        and returns the combined output.
        """
        portfolio_json = json.dumps(portfolio_data, indent=2)
        transactions_json = json.dumps(transactions[:20], indent=2)

        # ── Pre-score transactions via ML hybrid engine ──────────
        ml_summary = self._ml_score_transactions(transactions[:20])

        # ── build tasks (9 agents) ───────────────────────────────
        task_alert_intake = Task(
            description=(
                f"Process and categorize any alerts or anomalies from this portfolio "
                f"and transactions:\nPortfolio:\n{portfolio_json}\n"
                f"Transactions:\n{transactions_json}"
                f"{ml_summary}"
            ),
            expected_output="Alert categorization with priorities and routing recommendations.",
            agent=_alert_intake_crew_agent(),
        )

        task_customer_context = Task(
            description=(
                f"Build customer context profile for this portfolio owner. "
                f"Identify key aspects for personalized analysis:\n{portfolio_json}"
            ),
            expected_output="Customer context profile and behavioral insights.",
            agent=_customer_context_crew_agent(),
        )

        task_risk_assessment = Task(
            description=(
                f"Perform comprehensive risk assessment of portfolio and transactions:\n"
                f"Portfolio:\n{portfolio_json}\nTransactions:\n{transactions_json}"
                f"{ml_summary}\n\n"
                f"IMPORTANT: The ML Risk Pre-Screening above was generated by our "
                f"hybrid scoring engine (deterministic rules + GradientBoosting + "
                f"IsolationForest). Incorporate these ML scores into your analysis. "
                f"Focus your expertise on interpreting the results and recommending "
                f"mitigation strategies."
            ),
            expected_output="Risk scores, heat maps and mitigation strategies incorporating ML model results.",
            agent=_risk_assessment_crew_agent(),
        )

        task_portfolio = Task(
            description=(
                f"Analyse the following portfolio for allocation quality, "
                f"diversification and rebalancing needs:\n{portfolio_json}"
            ),
            expected_output="Structured portfolio analysis with scores and recommendations.",
            agent=_portfolio_crew_agent(),
        )

        task_risk = Task(
            description=(
                f"Detect fraud risk and market risk in this portfolio and its "
                f"recent transactions:\nPortfolio:\n{portfolio_json}\n"
                f"Transactions:\n{transactions_json}"
                f"{ml_summary}\n\n"
                f"The ML Pre-Screening above provides automated scores from our "
                f"hybrid engine (rules + ML models). Use these as your starting "
                f"point and add your expert fraud/risk assessment on top."
            ),
            expected_output="Risk report with fraud flags, risk level and mitigations.",
            agent=_risk_crew_agent(),
        )

        task_market = Task(
            description=(
                f"Provide market sentiment and trend outlook for the symbols "
                f"held in this portfolio:\n{portfolio_json}"
            ),
            expected_output="Sentiment scores and short/long-term outlook per symbol.",
            agent=_market_crew_agent(),
        )

        task_compliance = Task(
            description=(
                f"Review these transactions for regulatory compliance:\n{transactions_json}"
            ),
            expected_output="Compliance findings including PDT, wash-sale and AML flags.",
            agent=_compliance_crew_agent(),
        )

        # Explanation task uses results from above
        task_explanation = Task(
            description=(
                "Summarize and explain all findings from other agents in clear, "
                "customer-friendly language. Prepare explanations suitable for "
                "different audiences (customer, advisor, compliance)."
            ),
            expected_output="Clear explanations of all findings and recommendations.",
            agent=_explanation_crew_agent(),
        )

        # Escalation task prepares case if needed
        task_escalation = Task(
            description=(
                "Based on all analysis above, determine if escalation is needed. "
                "Prepare comprehensive case summary and escalation package if required."
            ),
            expected_output="Escalation evaluation and case summary if needed.",
            agent=_escalation_crew_agent(),
        )

        # ── run crew (sequential process) ────────────────────────
        agents_list = [
            task_alert_intake.agent,
            task_customer_context.agent,
            task_risk_assessment.agent,
            task_portfolio.agent,
            task_risk.agent,
            task_market.agent,
            task_compliance.agent,
            task_explanation.agent,
            task_escalation.agent,
        ]
        
        tasks_list = [
            task_alert_intake,
            task_customer_context,
            task_risk_assessment,
            task_portfolio,
            task_risk,
            task_market,
            task_compliance,
            task_explanation,
            task_escalation,
        ]

        crew = Crew(
            agents=agents_list,
            tasks=tasks_list,
            process=Process.sequential,
            verbose=False,
        )

        crew_output = crew.kickoff()

        # ── persist to ChromaDB ──────────────────────────────────
        pid = str(portfolio_data.get("id", "unknown"))
        full_text = str(crew_output)
        vector_store.store_portfolio_analysis(pid, full_text)

        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "portfolio_id": portfolio_data.get("id"),
            "crew_output": full_text,
            "agents_used": 9,
        }
        return result

    # ─── single-agent convenience methods ─────────────────────────
    def quick_portfolio_analysis(self, portfolio_data):
        res = self.portfolio_agent.analyze_portfolio(portfolio_data)
        vector_store.store_portfolio_analysis(
            str(portfolio_data.get("id", "?")), res.get("analysis", "")
        )
        return res

    def quick_risk_assessment(self, transactions, portfolio_data):
        # Pre-score transactions with ML before handing to LLM agent
        ml_results = []
        engine = self._get_risk_engine()
        if engine:
            for txn in transactions[:20]:
                try:
                    ml_results.append(engine.score(txn))
                except Exception:
                    pass

        res = self.risk_agent.detect_fraud_risk(transactions, portfolio_data, ml_results)
        vector_store.store_risk_assessment(
            str(portfolio_data.get("id", "?")), res.get("assessment", "")
        )
        return res

    def score_transaction(self, transaction: dict, customer_profile: dict = None) -> dict:
        """
        Score a single transaction using the RiskAssessmentAgent's hybrid pipeline.
        This is the primary entry point for transaction-level risk scoring.
        """
        profile = customer_profile or {}
        return self.risk_assessment_agent.score_transaction_risk(transaction, profile)

    def quick_market_sentiment(self, symbols):
        res = self.market_agent.analyze_market_sentiment(symbols)
        for sym in symbols:
            vector_store.store_market_analysis(sym, res.get("sentiment_analysis", ""))
        return res

    def quick_recommendation(self, symbol, portfolio_size, risk_profile):
        return self.market_agent.generate_investment_recommendation(
            symbol, portfolio_size, risk_profile
        )

    def quick_compliance_review(self, transactions):
        res = self.compliance_agent.review_transactions_compliance(transactions)
        vector_store.store_compliance_report("global", res.get("findings", ""))
        return res

    # ─── vector search helpers ────────────────────────────────────
    def search_past_analyses(self, query: str, portfolio_id: str = None):
        return vector_store.search_portfolio(query, portfolio_id)

    def search_past_risks(self, query: str, portfolio_id: str = None):
        return vector_store.search_risk(query, portfolio_id)

    def search_past_market(self, query: str, symbol: str = None):
        return vector_store.search_market(query, symbol)

