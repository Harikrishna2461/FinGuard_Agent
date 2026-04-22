"""Adversarial-ML tests for the fraud / risk classifier (risk R05).

Strategy: craft transactions an attacker would use to evade detection, then
assert the deterministic rule layer still produces the correct verdict
regardless of ML-model weights.

Field names mirror the real `RuleEngine.evaluate()` contract in
`backend/ml/risk_scoring_engine.py`.
"""
import pytest

from ml.risk_scoring_engine import TransactionRiskEngine


@pytest.fixture(scope="module")
def engine() -> TransactionRiskEngine:
    return TransactionRiskEngine()


def _base_txn(**overrides):
    txn = {
        "amount": 100.0,
        "currency": "USD",
        "transaction_type": "buy",
        "channel": "web",
        "device_type": "desktop",
        "asset_type": "stock",
        "sector": "Technology",
        "is_new_payee": 0,
        "is_weekend": 0,
        "is_holiday": 0,
        "ip_country_match": 1,
        "pep_flag": 0,
        "receiver_country": "US",
        "sender_country": "US",
        "account_age_days": 1500,
        "customer_avg_txn_amount": 100.0,
        "customer_txn_count_30d": 20,
        "num_txns_last_1h": 1,
        "num_txns_last_24h": 3,
        "failed_login_attempts_24h": 0,
        "portfolio_concentration_pct": 10.0,
        "time_of_day_hour": 12,
    }
    txn.update(overrides)
    return txn


def test_sanctioned_country_cannot_be_evaded(engine):
    """Even a $1 transaction to a sanctioned country must hard-block."""
    r = engine.score(_base_txn(amount=1.00, receiver_country="IR"))
    assert r["hard_block"] is True, f"sanctioned bypass: {r}"
    assert r["final_score"] >= 80
    assert "SANCTIONED_COUNTRY" in r["flags"]


def test_aml_threshold_flag_fires(engine):
    """$12k transaction must trip the AML reporting flag."""
    r = engine.score(_base_txn(amount=12_000.00))
    assert "AML_REPORTING" in r["flags"], f"no AML flag: {r['flags']}"


def test_extreme_deviation_flag_fires(engine):
    """$9,999 on a $100-average customer must raise EXTREME_DEVIATION."""
    r = engine.score(_base_txn(amount=9999.00))
    assert "EXTREME_DEVIATION" in r["flags"] or "HIGH_DEVIATION" in r["flags"]


def test_feature_micro_perturbation_stable(engine):
    base = engine.score(_base_txn(amount=100.0))
    perturbed = engine.score(_base_txn(amount=100.01))
    assert base["risk_label"] == perturbed["risk_label"]


def test_high_velocity_always_flagged(engine):
    """Adversary cannot hide a velocity attack by setting amount=1."""
    r = engine.score(_base_txn(amount=1.00, num_txns_last_1h=50, num_txns_last_24h=200))
    assert "HIGH_VELOCITY_1H" in r["flags"] or "HIGH_VELOCITY_24H" in r["flags"]


def test_high_risk_country_adds_score(engine):
    """Non-sanctioned but high-risk jurisdiction should bump the score."""
    base = engine.score(_base_txn(amount=500.0, receiver_country="US"))
    risky = engine.score(_base_txn(amount=500.0, receiver_country="KY"))
    assert risky["rule_details"]["rule_score"] >= base["rule_details"]["rule_score"]
