"""Quick integration test — verify ML models are wired into all components."""

import sys
import os

# Ensure backend is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env (needed for Groq API key when instantiating agents)
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

print("=" * 60)
print("  FinGuard ML Integration Tests")
print("=" * 60)

# ── Test 1: Direct engine scoring ─────────────────────────────
print("\n[1] TransactionRiskEngine — direct scoring")
from ml.risk_scoring_engine import TransactionRiskEngine
engine = TransactionRiskEngine()

# Low-risk: typical domestic stock buy with full features
r1 = engine.score({
    "amount": 500, "transaction_type": "buy", "sender_country": "US",
    "receiver_country": "US", "asset_type": "stock", "sector": "Technology",
    "currency": "USD", "channel": "web", "device_type": "desktop",
    "is_new_payee": 0, "account_age_days": 730, "customer_avg_txn_amount": 450,
    "customer_txn_count_30d": 5, "amount_deviation_from_avg": 0.1,
    "time_of_day_hour": 14, "is_weekend": 0, "ip_country_match": 1,
    "failed_login_attempts_24h": 0, "num_txns_last_1h": 0, "num_txns_last_24h": 1,
    "days_since_last_txn": 3, "receiver_account_age_days": 365,
    "is_high_risk_country": 0, "is_sanctioned_country": 0, "pep_flag": 0,
    "portfolio_concentration_pct": 15, "market_volatility_index": 18,
})
print(f"    Low-risk txn:  score={r1['final_score']}, label={r1['risk_label']}, method={r1['method']}")

r2 = engine.score({"amount": 75000, "transaction_type": "wire_transfer", "sender_country": "US", "receiver_country": "KP", "asset_type": "crypto", "is_sanctioned_country": 1, "is_high_risk_country": 1})
print(f"    Sanctioned txn: score={r2['final_score']}, label={r2['risk_label']}, method={r2['method']}, block={r2['hard_block']}")
assert r2["hard_block"] is True, "Sanctioned country should be hard-blocked"
assert r2["final_score"] >= 80, "Sanctioned should score >= 80"
# Verify scoring is working (exact values depend on model state)
assert r1["final_score"] < r2["final_score"], "Low risk should score lower than sanctioned"
print("    ✅ PASSED")

# ── Test 2: risk_tools.py (CrewAI tools) ─────────────────────
print("\n[2] risk_tools.py — CrewAI tool wrappers")
from agents.tools.risk_tools import _get_engine
e = _get_engine()
print(f"    ML engine loaded in risk_tools: {e is not None}")
assert e is not None, "risk_tools should load ML engine"

import json
from agents.tools.risk_tools import detect_fraud_patterns
txns = [
    {"amount": 500, "transaction_type": "buy", "sender_country": "US", "receiver_country": "US",
     "account_age_days": 730, "customer_avg_txn_amount": 450, "is_new_payee": 0},
    {"amount": 75000, "transaction_type": "wire_transfer", "receiver_country": "KP", "is_sanctioned_country": 1},
]
result_text = detect_fraud_patterns.run(json.dumps(txns))
print(f"    detect_fraud_patterns output (first 200 chars): {result_text[:200]}")
assert "ML Fraud Scan" in result_text, "Should contain ML scan header"
assert "score=" in result_text, "Should contain scores"
print("    ✅ PASSED")

# ── Test 3: Orchestrator ML pre-scoring ──────────────────────
print("\n[3] AIAgentOrchestrator — ML pre-scoring")
from agents.crew_orchestrator import AIAgentOrchestrator
orch = AIAgentOrchestrator()
summary = orch._ml_score_transactions([
    {"amount": 50, "transaction_type": "buy", "sender_country": "US", "receiver_country": "US"},
    {"amount": 75000, "transaction_type": "wire_transfer", "receiver_country": "KP", "is_sanctioned_country": 1},
])
print(f"    ML summary (first 300 chars): {summary[:300]}")
assert "ML Risk Pre-Screening" in summary, "Should contain pre-screening header"
assert "score=" in summary, "Should contain scores"
print("    ✅ PASSED")

# ── Test 4: RiskAssessmentAgent hybrid scoring ───────────────
print("\n[4] RiskAssessmentAgent — hybrid score_transaction_risk()")
from agents.risk_assessment_agent import RiskAssessmentAgent, _get_risk_engine
ra_engine = _get_risk_engine()
print(f"    ML engine loaded in RiskAssessmentAgent: {ra_engine is not None}")
assert ra_engine is not None, "RiskAssessmentAgent should load ML engine"
print("    ✅ PASSED (engine loads; full scoring requires LLM for borderline)")

# ── Test 5: RiskDetectionAgent ML integration ────────────────
print("\n[5] RiskDetectionAgent — ML engine loading")
from agents.risk_detection_agent import _get_risk_engine as rd_get_engine
rd_engine = rd_get_engine()
print(f"    ML engine loaded in RiskDetectionAgent: {rd_engine is not None}")
assert rd_engine is not None, "RiskDetectionAgent should load ML engine"
print("    ✅ PASSED")

# ── Test 6: AlertIntakeAgent ML integration ──────────────────
print("\n[6] AlertIntakeAgent — ML engine loading")
from agents.alert_intake_agent import _get_risk_engine as ai_get_engine
ai_engine = ai_get_engine()
print(f"    ML engine loaded in AlertIntakeAgent: {ai_engine is not None}")
assert ai_engine is not None, "AlertIntakeAgent should load ML engine"
print("    ✅ PASSED")

# ── Test 7: API route functions (import check) ──────────────
print("\n[7] API routes — ML functions importable")
# We can't fully test Flask routes without app context, but verify imports work
from app.routes import _get_risk_engine as api_get_engine
print("    _get_risk_engine importable from routes: True")
print("    ✅ PASSED")

print("\n" + "=" * 60)
print("  All 7 integration tests PASSED ✅")
print("=" * 60)
