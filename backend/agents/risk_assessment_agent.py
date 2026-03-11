"""Risk Assessment Agent - Comprehensive risk evaluation and scoring.

Uses a hybrid three-tier approach:
  Tier 1 – Deterministic rules (OFAC, thresholds, velocity)
  Tier 2 – ML models (GradientBoosting classifier + Isolation Forest)
  Tier 3 – LLM deep-dive (only for borderline 40-60 scores)
"""

import logging
from agents.base_agent import FinancialBaseAgent

logger = logging.getLogger(__name__)

# Lazy-load the ML risk engine (avoids import at module level if models missing)
_risk_engine = None

def _get_risk_engine():
    global _risk_engine
    if _risk_engine is None:
        try:
            from ml.risk_scoring_engine import TransactionRiskEngine
            _risk_engine = TransactionRiskEngine()
            logger.info("Hybrid risk engine loaded (rules + ML)")
        except Exception as e:
            logger.warning("Could not load ML risk engine: %s — falling back to LLM only", e)
    return _risk_engine


class RiskAssessmentAgent(FinancialBaseAgent):
    """
    Performs comprehensive risk assessment across portfolios, transactions,
    and customers. Generates risk scores, heat maps, and remediation strategies.

    Transaction scoring uses a HYBRID pipeline:
      1. Rule engine  – deterministic flags (sanctioned countries, AML, velocity)
      2. ML models    – GradientBoosting risk classifier + Isolation Forest anomaly detector
      3. LLM fallback – only invoked for borderline scores (40-60) or when ML unavailable
    """

    def __init__(self):
        super().__init__("RiskAssessment")

    def assess_portfolio_risk(self, portfolio_data: dict, market_conditions: dict) -> dict:
        """
        Comprehensive risk assessment of a portfolio.
        
        Args:
            portfolio_data: Portfolio holdings and allocation
            market_conditions: Current market conditions and volatility
            
        Returns:
            Risk assessment with scores and strategies
        """
        prompt = f"""You are a risk assessment expert. Perform comprehensive portfolio risk assessment:

Portfolio:
{self._format_dict(portfolio_data)}

Market Conditions:
{self._format_dict(market_conditions)}

Assess:
1. Market risk (Beta, Volatility, correlation)
2. Concentration risk (sector, asset class, single stock)
3. Liquidity risk
4. Counterparty risk
5. Currency risk (if applicable)
6. Interest rate risk
7. Overall portfolio score (0-100)

Return detailed risk breakdown with heat map and recommendations."""
        
        result = self.chat(prompt)
        return self._stamp({
            "assessment_type": "portfolio",
            "risk_analysis": result,
            "complete": True
        })

    def score_transaction_risk(self, transaction: dict, customer_profile: dict) -> dict:
        """
        Hybrid transaction risk scoring (Rules + ML + LLM).

        Pipeline:
          1. Merge transaction + customer_profile into a single feature dict.
          2. Run the deterministic rule engine  → flags & base score.
          3. Run the ML models (GBClassifier + Isolation Forest) → ML score.
          4. Combine: 40 % rules + 60 % ML.  Hard-blocks override.
          5. If score is borderline (40-60) OR ML unavailable, invoke LLM
             for a contextual explanation.

        Args:
            transaction:      Transaction details (amount, type, country, …)
            customer_profile: Customer baseline (avg amount, account age, …)

        Returns:
            dict with final_score, risk_label, flags, method, llm_explanation, …
        """
        # ── Merge inputs into feature dict expected by the engine ──
        txn = {**transaction, **customer_profile}

        engine = _get_risk_engine()

        if engine is not None:
            # ── Tier 1 + 2: Rules + ML ──
            hybrid = engine.score(txn)

            # ── Tier 3: LLM only when needed ──
            llm_explanation = None
            if hybrid.get("needs_llm_review") or not hybrid["ml_details"].get("available"):
                llm_explanation = self._llm_deep_dive(txn, hybrid)

            return self._stamp({
                "transaction_id":   transaction.get("id"),
                "final_score":      hybrid["final_score"],
                "risk_label":       hybrid["risk_label"],
                "method":           hybrid["method"],
                "hard_block":       hybrid["hard_block"],
                "flags":            hybrid["flags"],
                "rule_score":       hybrid["rule_details"]["rule_score"],
                "rule_flags":       hybrid["rule_details"]["flags"],
                "rule_details":     hybrid["rule_details"]["details"],
                "ml_risk_score":    hybrid["ml_details"].get("ml_risk_score"),
                "ml_risk_label":    hybrid["ml_details"].get("ml_risk_label"),
                "ml_fraud_flag":    hybrid["ml_details"].get("ml_fraud_flag"),
                "ml_anomaly_score": hybrid["ml_details"].get("ml_anomaly_score"),
                "ml_confidence":    hybrid["ml_details"].get("ml_confidence"),
                "needs_llm_review": hybrid["needs_llm_review"],
                "llm_explanation":  llm_explanation,
            })
        else:
            # ── Fallback: pure LLM (original behaviour) ──
            return self._score_via_llm(transaction, customer_profile)

    # ── private helpers ───────────────────────────────────────────

    def _llm_deep_dive(self, txn: dict, hybrid_result: dict) -> str:
        """Ask the LLM to explain a borderline or ambiguous score."""
        prompt = f"""You are a senior financial risk analyst.

A transaction was scored by our automated system with a BORDERLINE result.
Provide a concise, actionable explanation of why this transaction may or
may not be risky, and recommend next steps.

Transaction Summary:
  Amount:             ${txn.get('amount', 'N/A'):,.2f}
  Type:               {txn.get('transaction_type', 'N/A')}
  Sender Country:     {txn.get('sender_country', 'N/A')}
  Receiver Country:   {txn.get('receiver_country', 'N/A')}
  Asset Type:         {txn.get('asset_type', 'N/A')}
  Channel:            {txn.get('channel', 'N/A')}
  Account Age (days): {txn.get('account_age_days', 'N/A')}
  Is New Payee:       {txn.get('is_new_payee', 'N/A')}

Automated Scoring:
  Combined Score:     {hybrid_result['final_score']}/100
  Rule Flags:         {', '.join(hybrid_result['flags']) or 'None'}
  ML Risk Label:      {hybrid_result['ml_details'].get('ml_risk_label', 'N/A')}
  ML Fraud Flag:      {hybrid_result['ml_details'].get('ml_fraud_flag', 'N/A')}

Provide:
1. Plain-language risk explanation (2-3 sentences)
2. Recommended action: APPROVE / HOLD_FOR_REVIEW / ESCALATE / BLOCK
3. Key factors driving the score"""
        return self.chat(prompt)

    def _score_via_llm(self, transaction: dict, customer_profile: dict) -> dict:
        """Legacy pure-LLM scoring (fallback when ML unavailable)."""
        prompt = f"""Score the risk level of this transaction:

Transaction:
{self._format_dict(transaction)}

Customer Profile:
{self._format_dict(customer_profile)}

Evaluate:
1. Deviation from customer norm
2. Fraud indicators
3. AML/KYC concerns
4. Regulatory red flags
5. Risk score (1-100)
6. Action recommendations

Return risk score and required actions."""

        result = self.chat(prompt)
        return self._stamp({
            "transaction_id": transaction.get("id"),
            "final_score":    None,
            "risk_label":     "unknown",
            "method":         "llm_only",
            "hard_block":     False,
            "flags":          [],
            "llm_explanation": result,
            "needs_llm_review": False,
            "flagged": "high" in result.lower(),
        })

    def identify_systemic_risks(self, market_data: dict, portfolio_exposures: list) -> dict:
        """Identify systemic and correlated risks across customer base."""
        prompt = f"""Identify systemic risks affecting our customers:

Market Data:
{self._format_dict(market_data)}

Customer Exposures:
{self._format_list(portfolio_exposures)}

Analyze:
1. Market-wide risks
2. Sector correlation risks
3. Geographic concentration risks
4. Counterparty concentration
5. Liquidity shocks
6. Black swan scenarios
7. Customer impact assessment

Return systemic risk report with mitigation strategies."""
        
        result = self.chat(prompt)
        return self._stamp({
            "analysis": "systemic",
            "risks_identified": result,
            "requires_action": True
        })

    def calculate_risk_metrics(self, portfolio: dict) -> dict:
        """Calculate key risk metrics (VaR, Sharpe, etc.)."""
        prompt = f"""Calculate key risk metrics for this portfolio:

{self._format_dict(portfolio)}

Calculate:
1. Value at Risk (VaR) at 95% and 99%
2. Sharpe Ratio
3. Sortino Ratio
4. Maximum Drawdown
5. Correlation matrix key findings
6. Beta vs benchmark
7. Duration (if fixed income)

Return metrics with interpretations."""
        
        result = self.chat(prompt)
        return self._stamp({
            "metrics": result,
            "calculated": True
        })

    def recommend_hedging_strategies(self, risks: dict, constraints: dict) -> dict:
        """Recommend hedging strategies to mitigate identified risks."""
        prompt = f"""Recommend hedging strategies for identified risks:

Identified Risks:
{self._format_dict(risks)}

Constraints:
{self._format_dict(constraints)}

Recommend:
1. Hedging instruments
2. Allocation amounts
3. Cost-benefit analysis
4. Implementation timeline
5. Monitoring approach
6. Alternatives if primary not available

Return prioritized hedging strategy."""
        
        result = self.chat(prompt)
        return self._stamp({
            "strategies": result,
            "recommended": True
        })

    def _format_dict(self, d: dict) -> str:
        """Format dict for prompt."""
        return "\n".join(f"  {k}: {v}" for k, v in d.items())

    def _format_list(self, lst: list) -> str:
        """Format list for prompt."""
        return "\n".join(f"  {i+1}. {item}" for i, item in enumerate(lst))
