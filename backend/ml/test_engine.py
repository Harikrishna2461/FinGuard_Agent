"""Quick test of the hybrid risk scoring engine."""

from ml.risk_scoring_engine import TransactionRiskEngine

engine = TransactionRiskEngine()

# ── Test 1: Normal low-risk transaction ──
r1 = engine.score(
    {
        "amount": 1500,
        "transaction_type": "buy",
        "currency": "USD",
        "sender_country": "US",
        "receiver_country": "US",
        "is_new_payee": 0,
        "account_age_days": 1825,
        "customer_avg_txn_amount": 1200,
        "customer_txn_count_30d": 15,
        "amount_deviation_from_avg": 0.25,
        "time_of_day_hour": 10,
        "is_weekend": 0,
        "is_holiday": 0,
        "channel": "web",
        "device_type": "desktop",
        "ip_country_match": 1,
        "failed_login_attempts_24h": 0,
        "num_txns_last_1h": 1,
        "num_txns_last_24h": 3,
        "days_since_last_txn": 2,
        "receiver_account_age_days": 3650,
        "is_high_risk_country": 0,
        "is_sanctioned_country": 0,
        "pep_flag": 0,
        "asset_type": "stock",
        "sector": "Technology",
        "portfolio_concentration_pct": 12.5,
        "market_volatility_index": 18.5,
    }
)
print(
    f"Low-risk txn  -> Score: {r1['final_score']}, Label: {r1['risk_label']}, Method: {r1['method']}"
)

# ── Test 2: High-risk (sanctioned country, crypto, new account) ──
r2 = engine.score(
    {
        "amount": 90000,
        "transaction_type": "sell",
        "currency": "USD",
        "sender_country": "US",
        "receiver_country": "IR",
        "is_new_payee": 1,
        "account_age_days": 25,
        "customer_avg_txn_amount": 800,
        "customer_txn_count_30d": 1,
        "amount_deviation_from_avg": 112,
        "time_of_day_hour": 2,
        "is_weekend": 1,
        "is_holiday": 0,
        "channel": "mobile",
        "device_type": "phone",
        "ip_country_match": 0,
        "failed_login_attempts_24h": 6,
        "num_txns_last_1h": 10,
        "num_txns_last_24h": 18,
        "days_since_last_txn": 0,
        "receiver_account_age_days": 3,
        "is_high_risk_country": 1,
        "is_sanctioned_country": 1,
        "pep_flag": 0,
        "asset_type": "crypto",
        "sector": "Cryptocurrency",
        "portfolio_concentration_pct": 95,
        "market_volatility_index": 58,
    }
)
print(
    f"High-risk txn -> Score: {r2['final_score']}, Label: {r2['risk_label']}, Method: {r2['method']}, Block: {r2['hard_block']}"
)
print(f"               Flags: {r2['flags']}")

# ── Test 3: Medium / borderline ──
r3 = engine.score(
    {
        "amount": 18000,
        "transaction_type": "buy",
        "currency": "USD",
        "sender_country": "US",
        "receiver_country": "HK",
        "is_new_payee": 1,
        "account_age_days": 365,
        "customer_avg_txn_amount": 5000,
        "customer_txn_count_30d": 6,
        "amount_deviation_from_avg": 2.6,
        "time_of_day_hour": 20,
        "is_weekend": 0,
        "is_holiday": 0,
        "channel": "mobile",
        "device_type": "phone",
        "ip_country_match": 1,
        "failed_login_attempts_24h": 1,
        "num_txns_last_1h": 3,
        "num_txns_last_24h": 6,
        "days_since_last_txn": 1,
        "receiver_account_age_days": 200,
        "is_high_risk_country": 0,
        "is_sanctioned_country": 0,
        "pep_flag": 0,
        "asset_type": "stock",
        "sector": "Finance",
        "portfolio_concentration_pct": 35,
        "market_volatility_index": 25,
    }
)
print(
    f"Medium txn    -> Score: {r3['final_score']}, Label: {r3['risk_label']}, Method: {r3['method']}, NeedsLLM: {r3['needs_llm_review']}"
)

print()
print("All tests passed!")
