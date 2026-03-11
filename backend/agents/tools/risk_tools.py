"""
risk_tools.py  –  CrewAI @tool wrappers for risk & fraud detection

These tools use the hybrid ML scoring engine (Rules + GradientBoosting +
IsolationForest) so that CrewAI agents get *real* risk scores, not placeholders.
"""

import json
import logging
from crewai.tools import tool

logger = logging.getLogger(__name__)

# ── Lazy-load the ML risk engine ──────────────────────────────────
_risk_engine = None

def _get_engine():
    global _risk_engine
    if _risk_engine is None:
        try:
            from ml.risk_scoring_engine import TransactionRiskEngine
            _risk_engine = TransactionRiskEngine()
            logger.info("risk_tools: Hybrid ML engine loaded")
        except Exception as e:
            logger.warning("risk_tools: ML engine unavailable — %s", e)
    return _risk_engine


@tool("Detect Fraud Patterns")
def detect_fraud_patterns(transactions_json: str) -> str:
    """
    Scan a JSON list of transactions for unusual patterns that may
    indicate fraud, wash-trading, or market manipulation.
    Uses the hybrid ML scoring engine (Rules + ML models).
    """
    try:
        transactions = json.loads(transactions_json)
    except (json.JSONDecodeError, TypeError):
        return f"[Error] Could not parse transactions JSON: {transactions_json[:200]}"

    engine = _get_engine()
    if engine is None:
        return (
            f"[ML unavailable] Analysing {len(transactions)} transactions via heuristics only.\n"
            f"Transactions: {transactions_json[:500]}\n"
            "Recommend manual review for fraud patterns."
        )

    results = []
    flagged_count = 0
    critical_count = 0

    for i, txn in enumerate(transactions[:20]):  # cap at 20 for performance
        score_result = engine.score(txn)
        label = score_result["risk_label"]
        flags = score_result["flags"]

        if flags:
            flagged_count += 1
        if label in ("high", "critical"):
            critical_count += 1

        results.append(
            f"  Txn {i+1}: score={score_result['final_score']}/100 "
            f"label={label} method={score_result['method']} "
            f"block={score_result['hard_block']} "
            f"flags=[{', '.join(flags)}]"
        )

    summary = (
        f"ML Fraud Scan — {len(transactions)} transactions analysed.\n"
        f"  Flagged: {flagged_count} | Critical/High: {critical_count}\n\n"
        "Per-transaction breakdown:\n" + "\n".join(results)
    )
    return summary


@tool("Assess Market Risk")
def assess_market_risk(portfolio_json: str, market_conditions_json: str) -> str:
    """
    Evaluate market risk exposure given the portfolio holdings and
    current market conditions (both as JSON strings).
    Uses ML concentration and volatility analysis where applicable.
    """
    try:
        portfolio = json.loads(portfolio_json)
        conditions = json.loads(market_conditions_json)
    except (json.JSONDecodeError, TypeError):
        portfolio = {}
        conditions = {}

    engine = _get_engine()

    # Build a synthetic transaction-like dict from portfolio for ML scoring
    assets = portfolio.get("assets", [])
    asset_risks = []

    for asset in assets[:15]:
        synth_txn = {
            "amount": float(asset.get("current_price", 0)) * float(asset.get("quantity", 0)),
            "asset_type": asset.get("asset_type", "stock"),
            "sector": asset.get("sector", "Unknown"),
            "transaction_type": "hold",
            "portfolio_concentration_pct": (
                float(asset.get("current_price", 0)) * float(asset.get("quantity", 0))
                / max(float(portfolio.get("total_value", 1)), 1) * 100
            ),
            "market_volatility_index": float(conditions.get("vix", conditions.get("volatility", 20))),
            "sender_country": "US",
            "receiver_country": "US",
        }

        if engine:
            score_result = engine.score(synth_txn)
            asset_risks.append(
                f"  {asset.get('symbol', '?')}: "
                f"exposure=${synth_txn['amount']:,.0f} "
                f"concentration={synth_txn['portfolio_concentration_pct']:.1f}% "
                f"risk_score={score_result['final_score']}/100 "
                f"flags=[{', '.join(score_result['flags'])}]"
            )
        else:
            asset_risks.append(
                f"  {asset.get('symbol', '?')}: "
                f"exposure=${synth_txn['amount']:,.0f} "
                f"concentration={synth_txn['portfolio_concentration_pct']:.1f}%"
            )

    return (
        f"Market Risk Assessment ({len(assets)} assets):\n"
        + "\n".join(asset_risks)
        + f"\n\nMarket conditions: {json.dumps(conditions)}"
    )


@tool("Evaluate Concentration Risk")
def evaluate_concentration(portfolio_json: str) -> str:
    """
    Measure concentration risk across sectors, asset types
    and individual positions in the portfolio.
    Uses the ML rule engine's concentration thresholds.
    """
    try:
        portfolio = json.loads(portfolio_json)
    except (json.JSONDecodeError, TypeError):
        return f"[Error] Could not parse portfolio JSON: {portfolio_json[:200]}"

    assets = portfolio.get("assets", [])
    total_value = max(float(portfolio.get("total_value", 1)), 1)

    # Calculate real concentration metrics
    sector_totals = {}
    type_totals = {}
    position_risks = []

    for a in assets:
        value = float(a.get("current_price", 0)) * float(a.get("quantity", 0))
        pct = value / total_value * 100

        sector = a.get("sector", "Unknown")
        atype = a.get("asset_type", "stock")
        sector_totals[sector] = sector_totals.get(sector, 0) + pct
        type_totals[atype] = type_totals.get(atype, 0) + pct

        flag = " ⚠ HIGH" if pct >= 60 else (" ⚡ ELEVATED" if pct >= 30 else "")
        position_risks.append(f"  {a.get('symbol','?')}: {pct:.1f}%{flag}")

    # HHI (Herfindahl-Hirschman Index)
    hhi = sum(pct ** 2 for pct in [
        float(a.get("current_price", 0)) * float(a.get("quantity", 0)) / total_value * 100
        for a in assets
    ])
    hhi_rating = "HIGH" if hhi > 2500 else ("MODERATE" if hhi > 1500 else "LOW")

    sector_lines = [f"  {s}: {p:.1f}%" for s, p in sorted(sector_totals.items(), key=lambda x: -x[1])]
    type_lines = [f"  {t}: {p:.1f}%" for t, p in sorted(type_totals.items(), key=lambda x: -x[1])]

    return (
        f"Concentration Risk Report\n"
        f"  HHI Index: {hhi:.0f} ({hhi_rating})\n\n"
        f"Position Weights:\n" + "\n".join(position_risks) + "\n\n"
        f"Sector Breakdown:\n" + "\n".join(sector_lines) + "\n\n"
        f"Asset Type Breakdown:\n" + "\n".join(type_lines)
    )
