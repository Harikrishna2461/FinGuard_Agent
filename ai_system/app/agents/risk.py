"""Risk agent service backed by the legacy hybrid scoring approach."""

from __future__ import annotations

from ai_system.app.llm import chat
from ai_system.app.ml import get_risk_engine


def _score_transaction_risk(transaction: dict) -> dict:
    engine = get_risk_engine()
    if engine is None:
        return {
            "available": False,
            "final_score": None,
            "risk_label": "unknown",
            "flags": [],
            "summary": "ML risk engine unavailable.",
        }

    txn = {
        "amount": float(transaction.get("quantity") or 0) * float(transaction.get("price") or 0),
        "transaction_type": transaction.get("type", "buy"),
        "asset_type": transaction.get("asset_type", "stock"),
        "sector": transaction.get("sector", "Technology"),
        "sender_country": transaction.get("sender_country", "US"),
        "receiver_country": transaction.get("receiver_country", "US"),
        "currency": transaction.get("currency", "USD"),
        "channel": transaction.get("channel", "web"),
        "device_type": transaction.get("device_type", "desktop"),
        "is_new_payee": transaction.get("is_new_payee", 0),
        "account_age_days": transaction.get("account_age_days", 365),
        "customer_avg_txn_amount": transaction.get("customer_avg_txn_amount", 1000),
        "customer_txn_count_30d": transaction.get("customer_txn_count_30d", 3),
        "amount_deviation_from_avg": transaction.get("amount_deviation_from_avg", 0),
        "time_of_day_hour": transaction.get("time_of_day_hour", 12),
        "is_weekend": transaction.get("is_weekend", 0),
        "ip_country_match": transaction.get("ip_country_match", 1),
        "failed_login_attempts_24h": transaction.get("failed_login_attempts_24h", 0),
        "num_txns_last_1h": transaction.get("num_txns_last_1h", 0),
        "num_txns_last_24h": transaction.get("num_txns_last_24h", 0),
        "days_since_last_txn": transaction.get("days_since_last_txn", 1),
        "receiver_account_age_days": transaction.get("receiver_account_age_days", 365),
        "is_high_risk_country": transaction.get("is_high_risk_country", 0),
        "is_sanctioned_country": transaction.get("is_sanctioned_country", 0),
        "pep_flag": transaction.get("pep_flag", 0),
        "portfolio_concentration_pct": transaction.get("portfolio_concentration_pct", 10),
        "market_volatility_index": transaction.get("market_volatility_index", 20),
    }
    result = engine.score(txn)

    llm_explanation = None
    if result.get("needs_llm_review"):
        llm_explanation = chat(
            (
                "Explain whether this borderline transaction risk score needs review.\n\n"
                f"Transaction: {txn}\n"
                f"Automated result: score={result['final_score']}, label={result['risk_label']}, "
                f"flags={result['flags']}"
            )
        )

    summary = (
        f"score={result['final_score']}/100 label={result['risk_label']} "
        f"method={result['method']} flags={', '.join(result['flags']) or 'none'}"
    )
    if llm_explanation:
        summary = f"{summary}. {llm_explanation}"

    return {
        "available": True,
        "final_score": result["final_score"],
        "risk_label": result["risk_label"],
        "flags": result["flags"],
        "summary": summary,
        "raw": result,
    }


def invoke(portfolio: dict, transactions: list[dict], mode: str = "quick") -> dict:
    findings = []
    scored = [_score_transaction_risk(txn) for txn in transactions[:10]]
    available_scores = [item for item in scored if item["available"] and item["final_score"] is not None]

    if available_scores:
        high = [item for item in available_scores if item["risk_label"] in {"high", "critical"}]
        medium = [item for item in available_scores if item["risk_label"] == "medium"]
        if high:
            findings.append(f"{len(high)} recent transactions scored high or critical risk.")
        elif medium:
            findings.append(f"{len(medium)} recent transactions scored medium risk and may need review.")
        else:
            findings.append("Hybrid scoring did not surface any high-risk recent transaction.")

        for item in high[:3]:
            findings.append(item["summary"])
    else:
        trade_count = len(transactions)
        unique_symbols = len({txn.get("symbol") for txn in transactions if txn.get("symbol")})
        notional = sum(float(txn.get("quantity") or 0) * float(txn.get("price") or 0) for txn in transactions)
        if trade_count >= 10:
            findings.append("Trading velocity is elevated relative to a lightweight portfolio review.")
        if unique_symbols <= 2 and trade_count > 0:
            findings.append("Transaction concentration is high because activity is focused in very few symbols.")
        if notional >= 50000:
            findings.append("Recent transaction notional is material and should be reviewed against policy limits.")
        if not findings:
            findings.append("Quick risk screen did not detect any strong operational risk signal.")

    return {
        "agent": "risk",
        "mode": mode,
        "summary": " ".join(findings),
        "findings": findings,
        "scored_transactions": scored,
    }
