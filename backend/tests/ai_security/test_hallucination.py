"""Hallucination-guard tests (risk R04)."""
from ml.risk_scoring_engine import TransactionRiskEngine


def test_non_borderline_does_not_need_llm():
    engine = TransactionRiskEngine()
    txn = {
        "amount": 50.0, "currency": "USD", "transaction_type": "purchase",
        "channel": "web", "device_type": "desktop", "asset_type": "stock",
        "sector": "tech", "is_new_payee": False, "ip_country_match": True,
        "high_risk_country": "US", "account_age_days": 2000,
        "avg_transaction_amount": 50.0, "transaction_velocity_1h": 1,
        "transaction_velocity_24h": 1,
    }
    r = engine.score(txn)
    assert r["needs_llm_review"] is False


def test_result_shape_stable():
    engine = TransactionRiskEngine()
    r = engine.score({"amount": 500.0, "currency": "USD",
                      "transaction_type": "wire", "channel": "web",
                      "device_type": "mobile", "asset_type": "cash",
                      "sector": "finance"})
    for key in ("final_score", "risk_label", "method", "hard_block",
                "flags", "needs_llm_review"):
        assert key in r
