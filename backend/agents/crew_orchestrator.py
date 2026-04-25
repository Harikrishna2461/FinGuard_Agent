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

import os, json, logging, time
from typing import Dict, Any, List
from datetime import datetime

from crewai import Agent, Task, Crew, Process, LLM
try:
    from litellm import RateLimitError
except ImportError:
    RateLimitError = Exception  # Fallback if litellm not available

logger = logging.getLogger(__name__)

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
#  RAG helper — injects knowledge-base context into CrewAI task descriptions
# =====================================================================
def _rag_context(query: str, domain: str, n: int = 3) -> str:
    """Return a knowledge-base context block for injection into a task description."""
    try:
        ctx = vector_store.get_rag_context(query, agent_domain=domain, n=n)
        if ctx:
            return (
                f"\n\n── Reference Knowledge (from knowledge base) ──\n{ctx}\n"
                f"── End Reference Knowledge ──\n"
            )
    except Exception:
        pass
    return ""

# =====================================================================
#  Groq LLM helper (shared by every CrewAI Agent)
# =====================================================================
def _groq_llm() -> LLM:  # sourcery skip: use-fstring-for-concatenation
    """Create a CrewAI-compatible Groq LLM instance."""
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    if not api_key:
        logger.error("GROQ_API_KEY not set in environment variables")
        raise ValueError("GROQ_API_KEY environment variable is required")
    
    logger.info(f"Initializing Groq LLM with model: {model}, API key length: {len(api_key)}")
    
    return LLM(
        model="groq/" + model,
        api_key=api_key,
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

    # ─── comprehensive review via CrewAI (SPLIT INTO 3 SMALLER CREWS) ──────────
    def comprehensive_portfolio_review(
        self,
        portfolio_data: Dict[str, Any],
        transactions: List[Dict[str, Any]],
        stream_id: str | None = None,
        emit_fn=None,
    ) -> Dict[str, Any]:
        """
        Run three smaller crews sequentially to work around Groq free tier (12k TPM).

        Crew 1 (Risk): Risk Assessment + Risk Detection + Compliance (~3.5k tokens)
        Crew 2 (Portfolio): Portfolio Analysis + Market Intelligence + Customer Context (~3.5k tokens)
        Crew 3 (Summary): Alert Intake + Explanation + Escalation (~3.5k tokens)

        Each crew runs independently to stay well under the rate limit.
        """
        import time

        def _emit(event_type: str, data: dict):
            if stream_id and emit_fn:
                try:
                    emit_fn(stream_id, event_type, data)
                except Exception:
                    pass
        
        # ── Create ultra-compact summaries ────
        portfolio_summary = (
            f"Portfolio '{portfolio_data.get('name')}': "
            f"${portfolio_data.get('total_value', 0):,.0f} total, "
            f"{len(portfolio_data.get('assets', []))} assets, "
            f"symbols: {', '.join(a['symbol'] for a in portfolio_data.get('assets', [])[:5])}"
        )
        
        txn_summary = (
            f"Recent {len(transactions[:10])} transactions; "
            f"types: {', '.join(set(t.get('type') or t.get('transaction_type', 'unknown') for t in transactions[:10]))}"
        )
        
        # ── Pre-score transactions via ML hybrid engine ──────────
        ml_summary = self._ml_score_transactions(transactions[:10])

        # ── CREW 1: RISK ANALYSIS (Risk Assessment + Risk Detection + Compliance) ────
        task_risk_assessment = Task(
            description=f"Risk assessment:\n{portfolio_summary}{txn_summary}{ml_summary}",
            expected_output="Risk scores.",
            agent=_risk_assessment_crew_agent(),
        )

        task_risk_detection = Task(
            description=f"Fraud detection:\n{portfolio_summary}{txn_summary}{ml_summary}",
            expected_output="Fraud flags.",
            agent=_risk_crew_agent(),
        )

        task_compliance = Task(
            description=f"Compliance review:\n{txn_summary}",
            expected_output="Compliance findings.",
            agent=_compliance_crew_agent(),
        )

        crew1_output = "✅ Risk Analysis: Skipped (rate limit protection)"
        rate_limit_hit = False
        try:
            logger.info("Crew 1/3: Risk Analysis (Risk Assessment + Detection + Compliance)")
            _emit("crew_start", {"crew": 1, "name": "Risk Analysis", "agents": ["Risk Assessment", "Risk Detection", "Compliance"]})
            _emit("agent_thinking", {"agent": "Risk Assessment Agent", "crew": 1, "thought": f"Step 1/3 in Crew 1.\n\nAnalyzing portfolio risk:\n{portfolio_summary}\n\nChecking transactions for AML flags, fraud patterns, and compliance violations...\n{ml_summary}\n\n→ Handing risk scores to Risk Detection Agent."})
            _emit("agent_thinking", {"agent": "Risk Detection Agent", "crew": 1, "thought": f"Step 2/3 in Crew 1.\n\nReceived risk scores from Risk Assessment Agent.\n\nScanning {txn_summary} for fraud patterns, anomalous behaviour, structuring, and velocity spikes.\n\n→ Forwarding flagged transactions to Compliance Agent."})
            _emit("agent_thinking", {"agent": "Compliance Agent", "crew": 1, "thought": f"Step 3/3 in Crew 1.\n\nReviewing flagged transactions from Risk Detection Agent against SEC, FINRA, AML, and PDT rules.\n\nProducing final compliance findings for Crew 1 output.\n\n→ Handing Crew 1 output (risk + fraud + compliance) to Crew 2: Portfolio Analysis."})
            crew1 = Crew(
                agents=[task_risk_assessment.agent, task_risk_detection.agent, task_compliance.agent],
                tasks=[task_risk_assessment, task_risk_detection, task_compliance],
                process=Process.sequential,
                verbose=False,
            )
            crew1_output = crew1.kickoff()
            _emit("crew_done", {"crew": 1, "name": "Risk Analysis", "output": str(crew1_output)[:500]})
            time.sleep(1)
        except RateLimitError as e:
            logger.warning(f"Crew 1: Rate limit hit. Skipping remaining crews.")
            rate_limit_hit = True
            crew1_output = f"⚠️ Rate limit exceeded. Please wait 30 seconds and try again."
        except Exception as e:
            error_str = str(e)
            if "rate_limit" in error_str.lower() or "429" in error_str or "12000" in error_str or "tokens per minute" in error_str.lower():
                logger.warning(f"Crew 1: Rate limit hit. Skipping remaining crews.")
                rate_limit_hit = True
                crew1_output = f"⚠️ Rate limit exceeded. Please wait 30 seconds and try again."
            else:
                logger.warning(f"Crew 1 error: {e}")
                crew1_output = f"⚠️ Risk Analysis failed: {str(e)[:200]}"

        # ── IF RATE LIMITED, STOP HERE ────
        if rate_limit_hit:
            crew_output = (
                f"## 📊 Portfolio Analysis - Rate Limited\n\n"
                f"⏰ **Groq API Rate Limit Reached (12,000 tokens/min)**\n\n"
                f"**What happened:**\n"
                f"The AI analysis system exceeded its token quota. This is a free tier limitation.\n\n"
                f"**Your options:**\n"
                f"1. **Wait 30-60 seconds** and retry your analysis\n"
                f"2. **Upgrade to Groq Dev Tier** at https://console.groq.com/settings/billing (100k+ TPM)\n"
                f"3. **Switch to a lighter endpoint** - try 'Quick Recommendation' instead\n\n"
                f"**Current Analysis Status:**\n{crew1_output}\n\n"
                f"### ML Pre-Screening (Always Available)\n{ml_summary}"
            )

            # NOTE: do not persist rate-limit messages — they poison search results.
            result = {
                "timestamp": datetime.utcnow().isoformat(),
                "portfolio_id": portfolio_data.get("id"),
                "crew_output": crew_output,
                "agents_used": 9,
                "crews_run": 1,
                "rate_limited": True,
            }
            return result

        # ── CREW 2: PORTFOLIO ANALYSIS (Portfolio + Market + Customer Context) ────
        task_portfolio = Task(
            description=f"Portfolio allocation:\n{portfolio_summary}",
            expected_output="Portfolio scores.",
            agent=_portfolio_crew_agent(),
        )

        task_market = Task(
            description=f"Market sentiment:\n{portfolio_summary}",
            expected_output="Market outlook.",
            agent=_market_crew_agent(),
        )

        task_customer_context = Task(
            description=f"Customer profile:\n{portfolio_summary}",
            expected_output="Customer insights.",
            agent=_customer_context_crew_agent(),
        )

        crew2_output = "✅ Portfolio Analysis: Skipped (rate limit protection)"
        try:
            logger.info("Crew 2/3: Portfolio Analysis (Portfolio + Market + Customer)")
            _emit("crew_start", {"crew": 2, "name": "Portfolio Analysis", "agents": ["Portfolio Analyst", "Market Intelligence", "Customer Context"]})
            _emit("agent_thinking", {"agent": "Portfolio Analyst", "crew": 2, "thought": f"Step 1/3 in Crew 2.\n\nReceived Crew 1 risk findings as context.\n\nAnalyzing portfolio allocation and diversification:\n{portfolio_summary}\n\nEvaluating asset weights, concentration risk, and rebalancing opportunities.\n\n→ Handing diversification metrics to Market Intelligence Agent."})
            _emit("agent_thinking", {"agent": "Market Intelligence Agent", "crew": 2, "thought": f"Step 2/3 in Crew 2.\n\nReceived diversification metrics from Portfolio Analyst.\n\nAssessing market sentiment and trends for assets in portfolio:\n{portfolio_summary}\n\nAnalyzing sentiment scores, trend signals, and investment recommendations.\n\n→ Forwarding outlook to Customer Context Agent."})
            _emit("agent_thinking", {"agent": "Customer Context Agent", "crew": 2, "thought": f"Step 3/3 in Crew 2.\n\nMerging portfolio metrics + market outlook with the customer's profile.\n\nDeriving suitability, risk-tolerance alignment, and personalised insights.\n\n→ Handing Crew 2 output to Crew 3: Summary & Escalation."})
            crew2 = Crew(
                agents=[task_portfolio.agent, task_market.agent, task_customer_context.agent],
                tasks=[task_portfolio, task_market, task_customer_context],
                process=Process.sequential,
                verbose=False,
            )
            crew2_output = crew2.kickoff()
            _emit("crew_done", {"crew": 2, "name": "Portfolio Analysis", "output": str(crew2_output)[:500]})
            time.sleep(1)
        except RateLimitError as e:
            logger.warning(f"Crew 2: Rate limit hit. Skipping Crew 3.")
            rate_limit_hit = True
            crew2_output = f"⚠️ Rate limit exceeded. Skipping remaining crews."
        except Exception as e:
            error_str = str(e)
            if "rate_limit" in error_str.lower() or "429" in error_str or "12000" in error_str or "tokens per minute" in error_str.lower():
                logger.warning(f"Crew 2: Rate limit hit. Skipping Crew 3.")
                rate_limit_hit = True
                crew2_output = f"⚠️ Rate limit exceeded. Skipping remaining crews."
            else:
                logger.warning(f"Crew 2 error: {e}")
                crew2_output = f"⚠️ Portfolio Analysis failed: {str(e)[:200]}"

        # ── IF RATE LIMITED, STOP HERE ────
        if rate_limit_hit:
            crew_output = (
                f"## 📊 Portfolio Analysis - Rate Limited (Crew 2)\n\n"
                f"⏰ **Groq API Rate Limit Reached (12,000 tokens/min)**\n\n"
                f"**What happened:**\n"
                f"The AI analysis system exceeded its token quota during Crew 2. This is a free tier limitation.\n\n"
                f"**Your options:**\n"
                f"1. **Wait 30-60 seconds** and retry your analysis\n"
                f"2. **Upgrade to Groq Dev Tier** at https://console.groq.com/settings/billing (100k+ TPM)\n"
                f"3. **Switch to a lighter endpoint** - try 'Quick Recommendation' instead\n\n"
                f"**Completed Analysis:**\n"
                f"- Crew 1 (Risk): {str(crew1_output)[:100]}...\n"
                f"- Crew 2 (Portfolio): {str(crew2_output)[:100]}...\n\n"
                f"### ML Pre-Screening (Always Available)\n{ml_summary}"
            )

            # NOTE: do not persist rate-limit messages — they poison search results.
            result = {
                "timestamp": datetime.utcnow().isoformat(),
                "portfolio_id": portfolio_data.get("id"),
                "crew_output": crew_output,
                "agents_used": 9,
                "crews_run": 2,
                "rate_limited": True,
            }
            return result

        # ── CREW 3: SUMMARY (Alert Intake + Explanation + Escalation) ────
        task_alert_intake = Task(
            description=f"Categorize portfolio alerts:\n{portfolio_summary}\nTransactions:{txn_summary}{ml_summary}",
            expected_output="Alert priorities.",
            agent=_alert_intake_crew_agent(),
        )

        task_explanation = Task(
            description="Summarize all findings clearly.",
            expected_output="Clear summary.",
            agent=_explanation_crew_agent(),
        )

        task_escalation = Task(
            description="Escalation needs and case summary.",
            expected_output="Escalation evaluation.",
            agent=_escalation_crew_agent(),
        )

        crew3_output = "✅ Summary Crew: Skipped (rate limit protection)"
        try:
            logger.info("Crew 3/3: Summary (Alert Intake + Explanation + Escalation)")
            _emit("crew_start", {"crew": 3, "name": "Summary & Escalation", "agents": ["Alert Intake", "Explanation", "Escalation"]})
            _emit("agent_thinking", {"agent": "Alert Intake Agent", "crew": 3, "thought": f"Step 1/3 in Crew 3.\n\nReceived combined Crew 1 + Crew 2 outputs.\n\nCategorizing and prioritizing alerts from those findings:\n{portfolio_summary}\n\nDetermining alert severity, routing, and escalation requirements.\n\n→ Handing prioritised alerts to Explanation Agent."})
            _emit("agent_thinking", {"agent": "Explanation Agent", "crew": 3, "thought": "Step 2/3 in Crew 3.\n\nReceived prioritised alerts from Alert Intake Agent.\n\nProducing a clear, human-readable narrative that explains the risk drivers, portfolio posture, and recommended actions.\n\n→ Forwarding narrative to Escalation Agent."})
            _emit("agent_thinking", {"agent": "Escalation Agent", "crew": 3, "thought": "Step 3/3 in Crew 3.\n\nReceived narrative from Explanation Agent.\n\nSynthesizing all crew outputs into final case summary. Determining if manual review is required based on risk scores, compliance flags, and portfolio risk level.\n\n→ Emitting final result for the UI."})
            crew3 = Crew(
                agents=[task_alert_intake.agent, task_explanation.agent, task_escalation.agent],
                tasks=[task_alert_intake, task_explanation, task_escalation],
                process=Process.sequential,
                verbose=False,
            )
            crew3_output = crew3.kickoff()
            _emit("crew_done", {"crew": 3, "name": "Summary & Escalation", "output": str(crew3_output)[:500]})
            time.sleep(1)
        except RateLimitError as e:
            logger.warning(f"Crew 3: Rate limit hit.")
            rate_limit_hit = True
            crew3_output = f"⚠️ Rate limit exceeded. Analysis incomplete."
        except Exception as e:
            error_str = str(e)
            if "rate_limit" in error_str.lower() or "429" in error_str or "12000" in error_str or "tokens per minute" in error_str.lower():
                logger.warning(f"Crew 3: Rate limit hit.")
                rate_limit_hit = True
                crew3_output = f"⚠️ Rate limit exceeded. Analysis incomplete."
            else:
                logger.warning(f"Crew 3 error: {e}")
                crew3_output = f"⚠️ Summary Crew failed: {str(e)[:200]}"

        # ── IF RATE LIMITED DURING CREW 3, RETURN GRACEFULLY ────
        if rate_limit_hit:
            crew_output = (
                f"## 📊 Portfolio Analysis - Partial (Rate Limited)\n\n"
                f"⏰ **Groq API Rate Limit Reached (12,000 tokens/min)**\n\n"
                f"**What happened:**\n"
                f"The AI analysis system exceeded its token quota. This is a free tier limitation.\n\n"
                f"**Your options:**\n"
                f"1. **Wait 30-60 seconds** and retry your analysis\n"
                f"2. **Upgrade to Groq Dev Tier** at https://console.groq.com/settings/billing (100k+ TPM)\n"
                f"3. **Switch to a lighter endpoint** - try 'Quick Recommendation' instead\n\n"
                f"**Partial Analysis (Completed):**\n"
                f"- Crew 1 (Risk): {str(crew1_output)[:100]}...\n"
                f"- Crew 2 (Portfolio): {str(crew2_output)[:100]}...\n"
                f"- Crew 3 (Summary): {str(crew3_output)[:100]}...\n\n"
                f"### ML Pre-Screening (Always Available)\n{ml_summary}"
            )

            # NOTE: do not persist rate-limit messages — they poison search results.
            result = {
                "timestamp": datetime.utcnow().isoformat(),
                "portfolio_id": portfolio_data.get("id"),
                "crew_output": crew_output,
                "agents_used": 9,
                "crews_run": 3,
                "rate_limited": True,
            }
            return result

        # ── COMBINE ALL THREE CREWS' OUTPUT ────
        crew_output = (
            f"## 📊 Multi-Crew Portfolio Analysis (3 Parallel Crews)\n\n"
            f"### Crew 1: Risk Analysis\n{str(crew1_output)}\n\n"
            f"### Crew 2: Portfolio Analysis\n{str(crew2_output)}\n\n"
            f"### Crew 3: Summary & Escalation\n{str(crew3_output)}\n\n"
            f"### ML Pre-Screening\n{ml_summary}"
        )

        # ── persist to ChromaDB ──────────────────────────────────
        pid = str(portfolio_data.get("id", "unknown"))
        full_text = str(crew_output)
        try:
            vector_store.store_portfolio_analysis(pid, full_text)
        except Exception as e:
            logger.warning(f"Failed to store analysis in ChromaDB: {e}")

        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "portfolio_id": portfolio_data.get("id"),
            "crew_output": full_text,
            "agents_used": 9,
            "crews_run": 3,
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

    def quick_market_sentiment(self, symbols, stream_id=None, emit_fn=None):
        def _emit(event_type, data):
            if stream_id and emit_fn:
                try:
                    emit_fn(stream_id, event_type, data)
                except Exception:
                    pass

        symbols_str = ', '.join(symbols)
        _emit("crew_start", {"crew": 1, "name": "Market Sentiment Analysis", "agents": ["Market Intelligence Agent"]})
        _emit("agent_thinking", {"agent": "Market Intelligence Agent", "crew": 1,
              "thought": f"Step 1/2 — Data gathering.\n\n"
                         f"Symbols requested: {symbols_str}\n\n"
                         f"Fetching latest sentiment scores, news headlines, analyst ratings, "
                         f"and recent price-action signals for each symbol from the market knowledge base."})
        _emit("agent_thinking", {"agent": "Market Intelligence Agent", "crew": 1,
              "thought": f"Step 2/2 — Synthesis.\n\n"
                         f"Combining bullish/bearish drivers, technical momentum, "
                         f"macro context and risk factors into a unified sentiment narrative for "
                         f"{symbols_str}.\n\n"
                         f"→ Emitting structured sentiment result to the UI."})

        res = self.market_agent.analyze_market_sentiment(symbols)

        _emit("crew_done", {"crew": 1, "name": "Market Sentiment Analysis",
              "output": str(res.get("sentiment_analysis", ""))[:300]})

        for sym in symbols:
            vector_store.store_market_analysis(sym, res.get("sentiment_analysis", ""))
        return res

    def quick_recommendation(self, symbol, portfolio_size, risk_profile, stream_id=None, emit_fn=None):
        def _emit(event_type, data):
            if stream_id and emit_fn:
                try:
                    emit_fn(stream_id, event_type, data)
                except Exception:
                    pass

        _emit("crew_start", {"crew": 1, "name": "Investment Recommendation", "agents": ["Market Intelligence Agent"]})
        _emit("agent_thinking", {"agent": "Market Intelligence Agent", "crew": 1,
              "thought": f"Generating investment recommendation for {symbol}\n"
                         f"Portfolio size: ${portfolio_size:,.0f}\n"
                         f"Risk profile: {risk_profile}\n\n"
                         f"Analyzing sector trends, valuation metrics, momentum signals, "
                         f"and risk-adjusted return potential for this position..."})

        res = self.market_agent.generate_investment_recommendation(symbol, portfolio_size, risk_profile)

        _emit("crew_done", {"crew": 1, "name": "Investment Recommendation",
              "output": str(res.get("recommendation", ""))[:300]})
        return res

    def quick_compliance_review(self, transactions):
        res = self.compliance_agent.review_transactions_compliance(transactions)
        vector_store.store_compliance_report("global", res.get("findings", ""))
        return res

    # ─── QUICK RECOMMENDATION (Single-Agent, ~1k tokens, always works on free tier) ────
    def quick_portfolio_recommendation(
        self,
        portfolio_data: Dict[str, Any],
        transactions: List[Dict[str, Any]],
        stream_id: str | None = None,
        emit_fn=None,
    ) -> Dict[str, Any]:
        """
        Ultra-lightweight portfolio assessment using single Risk Assessment agent.
        Token budget: ~1k tokens (well under 12k TPM free tier).

        Returns immediate actionable risk recommendations in seconds.
        Perfect fallback when comprehensive analysis hits rate limit.
        """
        def _emit(event_type, data):
            if stream_id and emit_fn:
                try:
                    emit_fn(stream_id, event_type, data)
                except Exception:
                    pass

        try:
            # ── Create ultra-compact summary ────
            portfolio_summary = (
                f"Portfolio '{portfolio_data.get('name')}': "
                f"${portfolio_data.get('total_value', 0):,.0f}, "
                f"{len(portfolio_data.get('assets', []))} assets"
            )

            # ── Pre-score transactions via ML ──────────────
            ml_summary = self._ml_score_transactions(transactions[:5])

            # ── SINGLE AGENT: Risk Assessment (Most Critical) ────
            task_quick_risk = Task(
                description=(
                    f"Quick risk assessment (2-3 sentences):\n"
                    f"{portfolio_summary}\n"
                    f"Key risks? Recommendation?\n"
                    f"{ml_summary}"
                ),
                expected_output="Concise risk assessment and top recommendation.",
                agent=_risk_assessment_crew_agent(),
            )

            logger.info("Quick Recommendation: Running single Risk Assessment agent")
            _emit("crew_start", {"crew": 1, "name": "Quick Risk Assessment", "agents": ["Risk Assessment Agent"]})
            _emit("agent_thinking", {"agent": "Risk Assessment Agent", "crew": 1,
                  "thought": f"Quick portfolio risk assessment:\n{portfolio_summary}\n\n"
                             f"Identifying top risk factors, evaluating asset concentration, "
                             f"and formulating priority recommendations...\n{ml_summary}"})
            quick_crew = Crew(
                agents=[task_quick_risk.agent],
                tasks=[task_quick_risk],
                process=Process.sequential,
                verbose=False,
            )

            recommendation = quick_crew.kickoff()
            _emit("crew_done", {"crew": 1, "name": "Quick Risk Assessment",
                  "output": str(recommendation)[:300]})

            # ── Format response ────
            crew_output = (
                f"## ⚡ Quick Recommendation\n\n"
                f"**Portfolio:** {portfolio_summary}\n\n"
                f"### AI Risk Assessment\n{str(recommendation)}\n\n"
                f"### ML Pre-Screening\n{ml_summary}\n\n"
                f"**Next Steps:**\n"
                f"• Run full analysis for comprehensive review\n"
                f"• Or upgrade to Groq Dev Tier for unlimited analysis"
            )
            
            # ── Persist to ChromaDB ────
            pid = str(portfolio_data.get("id", "unknown"))
            try:
                vector_store.store_portfolio_analysis(pid, crew_output)
            except Exception as e:
                logger.warning(f"Failed to store quick recommendation: {e}")
            
            result = {
                "timestamp": datetime.utcnow().isoformat(),
                "portfolio_id": portfolio_data.get("id"),
                "crew_output": crew_output,
                "agents_used": 1,
                "recommendation_type": "quick",
                "rate_limited": False,
            }
            return result
            
        except RateLimitError as e:
            # Even quick recommendation hit the limit (unlikely but possible)
            logger.warning(f"Quick recommendation: Rate limit hit")
            fallback = (
                f"⚠️ **Rate Limit Reached**\n\n"
                f"Even the quick recommendation exceeded the rate limit.\n"
                f"Please wait 30-60 seconds and try again, or upgrade to Groq Dev Tier.\n\n"
                f"{self._ml_score_transactions(transactions[:5])}"
            )
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "portfolio_id": portfolio_data.get("id"),
                "crew_output": fallback,
                "agents_used": 0,
                "recommendation_type": "quick",
                "rate_limited": True,
            }
        except Exception as e:
            logger.error(f"Quick recommendation error: {str(e)}", exc_info=True)
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "portfolio_id": portfolio_data.get("id"),
                "crew_output": f"❌ Quick recommendation failed: {str(e)[:200]}",
                "agents_used": 0,
                "recommendation_type": "quick",
                "error": str(e),
            }

    # ─── vector search helpers ────────────────────────────────────
    def search_past_analyses(self, query: str, portfolio_id: str = None):
        return vector_store.search_portfolio(query, portfolio_id)

    def search_past_risks(self, query: str, portfolio_id: str = None):
        return vector_store.search_risk(query, portfolio_id)

    def search_past_market(self, query: str, symbol: str = None):
        return vector_store.search_market(query, symbol)

