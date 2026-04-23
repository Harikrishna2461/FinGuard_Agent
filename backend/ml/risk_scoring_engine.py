"""
FinGuard – Hybrid Transaction Risk Scoring Engine
===================================================

Three-tier scoring:
    Tier 1  ─  Rules Engine       (deterministic, instant)
    Tier 2  ─  ML Model           (GBClassifier + IsolationForest, ~2 ms)
    Tier 3  ─  LLM Explanation    (only for borderline scores 40-60)

Usage:
    from ml.risk_scoring_engine import TransactionRiskEngine
    engine = TransactionRiskEngine()
    result = engine.score(transaction_dict)
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional

import pandas as pd
import joblib

logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(SCRIPT_DIR, "models")


# ══════════════════════════════════════════════════════════════════
#  TIER 1 — Deterministic Rule Engine
# ══════════════════════════════════════════════════════════════════

# OFAC / Sanctions list (subset for demo — production: load from API)
SANCTIONED_COUNTRIES = {
    "KP",
    "IR",
    "SY",
    "CU",
    "RU",
    "BY",
    "AF",
    "YE",
    "SS",
    "SD",
    "SO",
    "LY",
    "CF",
    "CD",
    "ER",
    "MM",
    "ZW",
}

HIGH_RISK_COUNTRIES = SANCTIONED_COUNTRIES | {
    "KY",
    "PA",
    "VG",
    "BS",
    "BZ",
    "SC",
    "AG",
    "GI",
    "JE",
    "MV",
    "MT",
    "LI",
    "CY",
    "LB",
    "NG",
    "PK",
    "VE",
    "KH",
    "GN",
    "GW",
    "NI",
    "SB",
    "TD",
    "LA",
}


class RuleEngine:
    """Deterministic rule-based checks — returns hard flags and a base score."""

    # AML amount thresholds (USD)
    AML_REPORTING_THRESHOLD = 10_000
    LARGE_TXN_THRESHOLD = 50_000
    VELOCITY_LIMIT_1H = 5
    VELOCITY_LIMIT_24H = 15
    MAX_FAILED_LOGINS = 3
    HIGH_CONCENTRATION_PCT = 60.0
    NEW_ACCOUNT_DAYS = 30

    def evaluate(self, txn: dict) -> dict:
        """
        Run rules against a transaction.

        Returns:
            {
              "rule_score":    int 0-100,
              "flags":         [str, ...],
              "hard_block":    bool,
              "details":       {rule_name: finding}
            }
        """
        score = 0
        flags = []
        details = {}
        hard_block = False

        # ── R1: Sanctioned country ──
        receiver = txn.get("receiver_country", "")
        if receiver in SANCTIONED_COUNTRIES:
            score += 40
            flags.append("SANCTIONED_COUNTRY")
            details["sanctioned_country"] = (
                f"Receiver in sanctioned country: {receiver}"
            )
            hard_block = True

        # ── R2: High-risk country ──
        elif receiver in HIGH_RISK_COUNTRIES:
            score += 20
            flags.append("HIGH_RISK_COUNTRY")
            details["high_risk_country"] = (
                f"Receiver in high-risk jurisdiction: {receiver}"
            )

        # ── R3: AML reporting threshold ──
        amount = float(txn.get("amount", 0))
        if amount >= self.AML_REPORTING_THRESHOLD:
            score += 10
            flags.append("AML_REPORTING")
            details["aml_threshold"] = (
                f"Amount ${amount:,.2f} >= ${self.AML_REPORTING_THRESHOLD:,}"
            )

        # ── R4: Large transaction ──
        if amount >= self.LARGE_TXN_THRESHOLD:
            score += 10
            flags.append("LARGE_TXN")
            details["large_txn"] = f"Amount ${amount:,.2f} exceeds large-txn limit"

        # ── R5: Amount deviation from customer average ──
        avg = float(txn.get("customer_avg_txn_amount", 1))
        deviation = amount / avg if avg > 0 else 0
        if deviation > 10:
            score += 15
            flags.append("EXTREME_DEVIATION")
            details["deviation"] = f"{deviation:.1f}x customer average"
        elif deviation > 5:
            score += 8
            flags.append("HIGH_DEVIATION")
            details["deviation"] = f"{deviation:.1f}x customer average"

        # ── R6: Transaction velocity ──
        txns_1h = int(txn.get("num_txns_last_1h", 0))
        txns_24h = int(txn.get("num_txns_last_24h", 0))
        if txns_1h >= self.VELOCITY_LIMIT_1H:
            score += 12
            flags.append("HIGH_VELOCITY_1H")
            details["velocity_1h"] = f"{txns_1h} txns in last hour"
        if txns_24h >= self.VELOCITY_LIMIT_24H:
            score += 8
            flags.append("HIGH_VELOCITY_24H")
            details["velocity_24h"] = f"{txns_24h} txns in last 24h"

        # ── R7: Failed login attempts ──
        failed = int(txn.get("failed_login_attempts_24h", 0))
        if failed >= self.MAX_FAILED_LOGINS:
            score += 10
            flags.append("FAILED_LOGINS")
            details["failed_logins"] = f"{failed} failed login attempts in 24h"

        # ── R8: New payee + new account ──
        if (
            txn.get("is_new_payee")
            and int(txn.get("account_age_days", 9999)) <= self.NEW_ACCOUNT_DAYS
        ):
            score += 15
            flags.append("NEW_PAYEE_NEW_ACCOUNT")
            details["new_combo"] = "New payee from a recently opened account"

        # ── R9: IP country mismatch ──
        if not txn.get("ip_country_match", True):
            score += 8
            flags.append("IP_MISMATCH")
            details["ip_mismatch"] = "Transaction IP doesn't match customer country"

        # ── R10: PEP flag ──
        if txn.get("pep_flag"):
            score += 10
            flags.append("PEP")
            details["pep"] = "Politically Exposed Person flagged"

        # ── R11: High portfolio concentration ──
        conc = float(txn.get("portfolio_concentration_pct", 0))
        if conc >= self.HIGH_CONCENTRATION_PCT:
            score += 8
            flags.append("HIGH_CONCENTRATION")
            details["concentration"] = f"Portfolio concentration {conc:.1f}%"

        # ── R12: Off-hours + weekend ──
        hour = int(txn.get("time_of_day_hour", 12))
        is_weekend = bool(txn.get("is_weekend", False))
        if (hour < 6 or hour > 22) and is_weekend:
            score += 5
            flags.append("OFF_HOURS_WEEKEND")
            details["timing"] = f"Transaction at hour {hour} on weekend"

        # ── R13: Crypto + high risk ──
        if txn.get("asset_type") == "crypto" and receiver in HIGH_RISK_COUNTRIES:
            score += 15
            flags.append("CRYPTO_HIGH_RISK")
            details["crypto_risk"] = (
                "Cryptocurrency transaction to high-risk jurisdiction"
            )

        # Cap at 100
        score = min(score, 100)

        return {
            "rule_score": score,
            "flags": flags,
            "hard_block": hard_block,
            "details": details,
        }


# ══════════════════════════════════════════════════════════════════
#  TIER 2 — ML Model Scoring
# ══════════════════════════════════════════════════════════════════


class MLScorer:
    """Loads trained models and returns ML-based risk scores."""

    def __init__(self):
        self.loaded = False
        self.risk_clf = None
        self.fraud_det = None
        self.scaler = None
        self.label_encoders = None
        self.metadata = None
        self._load_models()

    def _load_models(self):
        meta_path = os.path.join(MODEL_DIR, "model_metadata.json")
        if not os.path.exists(meta_path):
            logger.warning(
                "ML models not found at %s — run train_risk_model.py first", MODEL_DIR
            )
            return

        try:
            with open(meta_path) as f:
                self.metadata = json.load(f)

            try:
                self.risk_clf = joblib.load(
                    os.path.join(MODEL_DIR, "risk_classifier.joblib")
                )
                self.fraud_det = joblib.load(
                    os.path.join(MODEL_DIR, "fraud_detector.joblib")
                )
                self.scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.joblib"))
                self.label_encoders = joblib.load(
                    os.path.join(MODEL_DIR, "label_encoders.joblib")
                )
                self.loaded = True
                logger.info("ML models loaded successfully from %s", MODEL_DIR)
            except (ImportError, AttributeError, ValueError) as e:
                logger.warning(
                    "Failed to load ML models due to version incompatibility: %s\n"
                    "This typically means the models were trained with a different scikit-learn/numpy version.\n"
                    "Falling back to rules-based scoring only.\n"
                    "To fix: pip install --upgrade scikit-learn numpy, then run: python backend/ml/train_risk_model.py",
                    e,
                )
                self.loaded = False
                return
        except Exception as e:
            logger.error("Error loading model metadata: %s", e)
            self.loaded = False

    def _prepare_features(self, txn: dict) -> Optional[pd.DataFrame]:
        """Build feature vector from transaction dict — mirrors training pipeline."""
        if not self.loaded:
            return None

        row = {
            "amount": float(txn.get("amount", 0)),
            "account_age_days": int(txn.get("account_age_days", 365)),
            "customer_avg_txn_amount": float(txn.get("customer_avg_txn_amount", 1)),
            "customer_txn_count_30d": int(txn.get("customer_txn_count_30d", 0)),
            "amount_deviation_from_avg": float(txn.get("amount_deviation_from_avg", 0)),
            "time_of_day_hour": int(txn.get("time_of_day_hour", 12)),
            "num_txns_last_1h": int(txn.get("num_txns_last_1h", 0)),
            "num_txns_last_24h": int(txn.get("num_txns_last_24h", 0)),
            "days_since_last_txn": int(txn.get("days_since_last_txn", 1)),
            "receiver_account_age_days": int(txn.get("receiver_account_age_days", 365)),
            "portfolio_concentration_pct": float(
                txn.get("portfolio_concentration_pct", 10)
            ),
            "market_volatility_index": float(txn.get("market_volatility_index", 20)),
            # binary
            "is_new_payee": int(txn.get("is_new_payee", 0)),
            "is_weekend": int(txn.get("is_weekend", 0)),
            "is_holiday": int(txn.get("is_holiday", 0)),
            "ip_country_match": int(txn.get("ip_country_match", 1)),
            "is_high_risk_country": int(txn.get("is_high_risk_country", 0)),
            "is_sanctioned_country": int(txn.get("is_sanctioned_country", 0)),
            "pep_flag": int(txn.get("pep_flag", 0)),
            # categorical (raw strings)
            "transaction_type": txn.get("transaction_type", "buy"),
            "currency": txn.get("currency", "USD"),
            "channel": txn.get("channel", "web"),
            "device_type": txn.get("device_type", "desktop"),
            "asset_type": txn.get("asset_type", "stock"),
            "sector": txn.get("sector", "Technology"),
            # derived
            "failed_login_attempts_24h": int(txn.get("failed_login_attempts_24h", 0)),
        }

        # Derived features (same as training)
        avg = row["customer_avg_txn_amount"]
        row["amount_to_avg_ratio"] = row["amount"] / avg if avg > 0 else 0
        row["velocity_ratio"] = (
            row["num_txns_last_1h"] / row["num_txns_last_24h"]
            if row["num_txns_last_24h"] > 0
            else 0
        )
        age = row["account_age_days"]
        if age <= 30:
            row["account_maturity"] = 0
        elif age <= 90:
            row["account_maturity"] = 1
        elif age <= 365:
            row["account_maturity"] = 2
        elif age <= 730:
            row["account_maturity"] = 3
        else:
            row["account_maturity"] = 4

        row["is_cross_border"] = int(
            txn.get("sender_country", "US") != txn.get("receiver_country", "US")
        )
        row["has_failed_logins"] = int(row["failed_login_attempts_24h"] > 0)

        df = pd.DataFrame([row])

        # Encode categoricals
        for col in self.metadata["categorical_features"]:
            le = self.label_encoders[col]
            val = df[col].iloc[0]
            if val in le.classes_:
                df[col] = le.transform(df[col].astype(str))
            else:
                # Unseen category → use most frequent
                df[col] = 0

        # Scale numerics
        from ml.train_risk_model import NUMERIC_FEATURES

        scale_cols = NUMERIC_FEATURES + [
            "amount_to_avg_ratio",
            "velocity_ratio",
            "failed_login_attempts_24h",
        ]
        df[scale_cols] = self.scaler.transform(df[scale_cols])

        # Reorder to match training features
        df = df[self.metadata["feature_names"]]
        return df

    def predict(self, txn: dict) -> dict:
        """
        Returns:
            {
              "ml_risk_label":  str,
              "ml_risk_score":  int 0-100,
              "ml_fraud_flag":  bool,
              "ml_anomaly_score": float,
              "ml_confidence":  float,
              "available":      bool
            }
        """
        if not self.loaded:
            return {"available": False, "reason": "ML models not trained yet"}

        try:
            X = self._prepare_features(txn)
            if X is None:
                return {"available": False, "reason": "Feature preparation failed"}

            # Risk classification
            risk_proba = self.risk_clf.predict_proba(X)[0]
            risk_class = int(self.risk_clf.predict(X)[0])
            inv_map = {v: k for k, v in self.metadata["risk_label_map"].items()}
            risk_label = inv_map.get(risk_class, "medium")
            confidence = float(risk_proba.max())

            # Map class to 0-100 score
            # weighted sum of probabilities × class severity
            severity_weights = {0: 10, 1: 40, 2: 70, 3: 95}
            ml_score = sum(
                risk_proba[i] * severity_weights.get(i, 50)
                for i in range(len(risk_proba))
            )
            ml_score = min(max(int(round(ml_score)), 0), 100)

            # Fraud detection (Isolation Forest)
            raw = self.fraud_det.predict(X)[0]
            fraud_flag = bool(raw == -1)
            anomaly_score = float(-self.fraud_det.decision_function(X)[0])

            return {
                "available": True,
                "ml_risk_label": risk_label,
                "ml_risk_score": ml_score,
                "ml_fraud_flag": fraud_flag,
                "ml_anomaly_score": round(anomaly_score, 4),
                "ml_confidence": round(confidence, 4),
                "ml_probabilities": {
                    inv_map.get(i, str(i)): round(float(p), 4)
                    for i, p in enumerate(risk_proba)
                },
            }
        except Exception as e:
            logger.error("ML scoring failed: %s", e, exc_info=True)
            return {"available": False, "reason": str(e)}


# ══════════════════════════════════════════════════════════════════
#  COMBINED ENGINE
# ══════════════════════════════════════════════════════════════════


class TransactionRiskEngine:
    """
    Hybrid risk scoring:  Rules + ML + (optional) LLM explanation.

    Usage:
        engine = TransactionRiskEngine()
        result = engine.score(transaction_dict)
    """

    def __init__(self):
        self.rules = RuleEngine()
        self.ml = MLScorer()

    def score(self, txn: dict) -> dict:
        """
        Score a single transaction.

        Returns:
            {
              "final_score":       int 0-100,
              "risk_label":        str,
              "method":            str,        # "rules" / "ml" / "hybrid"
              "hard_block":        bool,
              "flags":             [str, ...],
              "needs_llm_review":  bool,       # True if score in 40-60 range
              "rule_details":      {...},
              "ml_details":        {...},
              "timestamp":         str,
            }
        """
        timestamp = datetime.utcnow().isoformat()

        # ── Tier 1: Rules ──
        rule_result = self.rules.evaluate(txn)

        # ── Tier 2: ML ──
        ml_result = self.ml.predict(txn)

        # ── Combine scores ──
        rule_score = rule_result["rule_score"]
        hard_block = rule_result["hard_block"]

        if hard_block:
            # Rules override: sanctioned country = instant block
            final_score = max(rule_score, 90)
            method = "rules"
        elif ml_result.get("available"):
            ml_score = ml_result["ml_risk_score"]
            # Weighted combination: 40% rules + 60% ML
            final_score = int(round(0.4 * rule_score + 0.6 * ml_score))
            method = "hybrid"

            # ── Anomaly-based adjustment ─────────────────────────────
            # IsolationForest's fraud_flag (-1) fires whenever a txn falls
            # outside its training distribution — it does NOT mean fraud.
            # Applying a hard `max(score, 80)` on that signal alone was
            # producing false criticals for routine transactions. Instead,
            # scale the adjustment by the actual anomaly magnitude and only
            # treat it as critical when the anomaly is genuinely strong.
            if ml_result.get("ml_fraud_flag"):
                anomaly = float(ml_result.get("ml_anomaly_score") or 0.0)
                if anomaly >= 0.20:
                    # Strong outlier — treat as probable fraud.
                    final_score = max(final_score, 80)
                    rule_result["flags"].append("ML_FRAUD_DETECTED")
                elif anomaly >= 0.10:
                    # Meaningful anomaly — bump a bit but cap below critical.
                    final_score = min(max(final_score + 15, final_score), 70)
                    rule_result["flags"].append("ML_ANOMALY")
                # Otherwise (anomaly < 0.10) the outlier signal is too weak
                # to change the verdict — ignore it.
        else:
            # ML unavailable — use rules only
            final_score = rule_score
            method = "rules"

        final_score = min(max(final_score, 0), 100)

        # Map score → label
        if final_score >= 80:
            risk_label = "critical"
        elif final_score >= 55:
            risk_label = "high"
        elif final_score >= 30:
            risk_label = "medium"
        else:
            risk_label = "low"

        # Flag borderline for LLM deep-dive
        needs_llm = 40 <= final_score <= 60

        return {
            "final_score": final_score,
            "risk_label": risk_label,
            "method": method,
            "hard_block": hard_block,
            "flags": rule_result["flags"],
            "needs_llm_review": needs_llm,
            "rule_details": rule_result,
            "ml_details": ml_result,
            "timestamp": timestamp,
        }
