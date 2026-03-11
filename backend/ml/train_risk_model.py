"""
FinGuard Agent – Transaction Risk ML Model Training Pipeline
=============================================================

This script trains two ML models for transaction risk scoring:
  1. XGBoost Classifier  → predicts risk_label  (low / medium / high / critical)
  2. Isolation Forest     → unsupervised anomaly detection (fraud flag)

Usage:
    python train_risk_model.py                    # train + evaluate
    python train_risk_model.py --data <csv_path>  # custom training data

Models are saved to  backend/ml/models/  as joblib files and loaded at
runtime by the RiskAssessmentAgent's hybrid scoring pipeline.
"""

import os
import sys
import json
import argparse
import warnings
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    accuracy_score,
    f1_score,
)
from sklearn.ensemble import IsolationForest, GradientBoostingClassifier
import joblib

warnings.filterwarnings("ignore")

# ────────────────────────────── paths ──────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR     = os.path.join(SCRIPT_DIR, "data")
MODEL_DIR    = os.path.join(SCRIPT_DIR, "models")
DEFAULT_CSV  = os.path.join(DATA_DIR, "transaction_risk_training_data.csv")

os.makedirs(MODEL_DIR, exist_ok=True)


# ────────────────────────────── feature engineering ────────────────
NUMERIC_FEATURES = [
    "amount",
    "account_age_days",
    "customer_avg_txn_amount",
    "customer_txn_count_30d",
    "amount_deviation_from_avg",
    "time_of_day_hour",
    "num_txns_last_1h",
    "num_txns_last_24h",
    "days_since_last_txn",
    "receiver_account_age_days",
    "portfolio_concentration_pct",
    "market_volatility_index",
]

BINARY_FEATURES = [
    "is_new_payee",
    "is_weekend",
    "is_holiday",
    "ip_country_match",
    "is_high_risk_country",
    "is_sanctioned_country",
    "pep_flag",
]

CATEGORICAL_FEATURES = [
    "transaction_type",
    "currency",
    "channel",
    "device_type",
    "asset_type",
    "sector",
]


def load_and_prepare(csv_path: str) -> pd.DataFrame:
    """Load CSV, engineer additional features, return clean DataFrame."""
    df = pd.read_csv(csv_path)
    print(f"  Loaded {len(df)} rows from {csv_path}")

    # ── Derived features ──
    # Amount-to-average ratio (key anomaly signal)
    df["amount_to_avg_ratio"] = np.where(
        df["customer_avg_txn_amount"] > 0,
        df["amount"] / df["customer_avg_txn_amount"],
        0,
    )
    # Velocity: txns in last hour relative to 24h
    df["velocity_ratio"] = np.where(
        df["num_txns_last_24h"] > 0,
        df["num_txns_last_1h"] / df["num_txns_last_24h"],
        0,
    )
    # Account maturity bucket
    df["account_maturity"] = pd.cut(
        df["account_age_days"],
        bins=[0, 30, 90, 365, 730, 99999],
        labels=[0, 1, 2, 3, 4],
    ).astype(int)

    # Cross-border flag
    df["is_cross_border"] = (
        df["sender_country"] != df["receiver_country"]
    ).astype(int)

    # Login risk
    df["has_failed_logins"] = (df["failed_login_attempts_24h"] > 0).astype(int)

    return df


def encode_features(df: pd.DataFrame):
    """Encode categoricals, scale numerics.  Returns X, label_encoders, scaler."""
    label_encoders = {}
    for col in CATEGORICAL_FEATURES:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        label_encoders[col] = le

    all_features = (
        NUMERIC_FEATURES
        + BINARY_FEATURES
        + CATEGORICAL_FEATURES
        + [
            "amount_to_avg_ratio",
            "velocity_ratio",
            "account_maturity",
            "is_cross_border",
            "has_failed_logins",
            "failed_login_attempts_24h",
        ]
    )

    X = df[all_features].copy()
    scaler = StandardScaler()
    X[NUMERIC_FEATURES + ["amount_to_avg_ratio", "velocity_ratio", "failed_login_attempts_24h"]] = (
        scaler.fit_transform(
            X[NUMERIC_FEATURES + ["amount_to_avg_ratio", "velocity_ratio", "failed_login_attempts_24h"]]
        )
    )

    return X, all_features, label_encoders, scaler


# ────────────────────────────── training ──────────────────────────
def train_risk_classifier(X_train, y_train, X_test, y_test, label_map):
    """Train GradientBoosting for risk label classification."""
    print("\n══════════════════════════════════════════════")
    print("  Training Risk Classifier (Gradient Boosting)")
    print("══════════════════════════════════════════════")

    clf = GradientBoostingClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
    )
    clf.fit(X_train, y_train)

    # ── Evaluation ──
    y_pred = clf.predict(X_test)
    acc    = accuracy_score(y_test, y_pred)
    f1_w   = f1_score(y_test, y_pred, average="weighted")

    inv_map = {v: k for k, v in label_map.items()}
    target_names = [inv_map[i] for i in sorted(inv_map)]

    print(f"\n  Accuracy : {acc:.4f}")
    print(f"  F1 (wtd) : {f1_w:.4f}")
    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=target_names))

    # ── Cross-validation ──
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(clf, X_train, y_train, cv=cv, scoring="f1_weighted")
    print(f"  5-Fold CV F1: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    # ── Feature importance ──
    importance = clf.feature_importances_
    top_10_idx = np.argsort(importance)[::-1][:10]
    print("\n  Top-10 Features:")
    for rank, idx in enumerate(top_10_idx, 1):
        print(f"    {rank:2d}. {X_train.columns[idx]:35s}  {importance[idx]:.4f}")

    return clf


def train_fraud_detector(X_train, y_fraud_train, X_test, y_fraud_test):
    """Train Isolation Forest for fraud/anomaly detection."""
    print("\n══════════════════════════════════════════════")
    print("  Training Fraud Detector  (Isolation Forest)")
    print("══════════════════════════════════════════════")

    # Only train on non-fraud data (Isolation Forest is unsupervised)
    X_normal = X_train[y_fraud_train == 0]

    iso = IsolationForest(
        n_estimators=200,
        contamination=0.1,   # expect ~10% anomalies
        max_features=0.8,
        random_state=42,
    )
    iso.fit(X_normal)

    # Predict on test set:  1 = normal, -1 = anomaly
    raw_pred = iso.predict(X_test)
    y_pred   = (raw_pred == -1).astype(int)     # 1 = fraud
    anomaly_scores = -iso.decision_function(X_test)  # higher = more anomalous

    acc = accuracy_score(y_fraud_test, y_pred)
    f1  = f1_score(y_fraud_test, y_pred, zero_division=0)

    print(f"\n  Accuracy        : {acc:.4f}")
    print(f"  F1 (fraud class): {f1:.4f}")
    print(f"  Frauds detected : {y_pred.sum()} / {y_fraud_test.sum()} actual")
    print("\n  Classification Report:")
    print(classification_report(
        y_fraud_test, y_pred, target_names=["legitimate", "fraud"], zero_division=0
    ))

    return iso


# ────────────────────────────── main ──────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Train FinGuard Risk ML Models")
    parser.add_argument("--data", default=DEFAULT_CSV, help="Path to training CSV")
    args = parser.parse_args()

    print("=" * 60)
    print("  FinGuard – ML Risk Model Training Pipeline")
    print("=" * 60)
    print(f"  Date     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Data     : {args.data}")
    print(f"  Models → : {MODEL_DIR}")
    print()

    # 1 ── Load & prepare ──
    df = load_and_prepare(args.data)

    # 2 ── Encode ──
    X, feature_names, label_encoders, scaler = encode_features(df)

    # Encode risk_label target
    risk_label_map = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    y_risk  = df["risk_label"].map(risk_label_map)
    y_fraud = df["is_fraud"].astype(int)

    # 3 ── Train/test split ──
    X_train, X_test, y_risk_train, y_risk_test, y_fraud_train, y_fraud_test = (
        train_test_split(X, y_risk, y_fraud, test_size=0.2, random_state=42, stratify=y_risk)
    )
    print(f"  Train: {len(X_train)} | Test: {len(X_test)}")

    # 4 ── Train models ──
    risk_clf = train_risk_classifier(X_train, y_risk_train, X_test, y_risk_test, risk_label_map)
    fraud_det = train_fraud_detector(X_train, y_fraud_train, X_test, y_fraud_test)

    # 5 ── Save artifacts ──
    artifacts = {
        "risk_classifier.joblib": risk_clf,
        "fraud_detector.joblib":  fraud_det,
        "scaler.joblib":          scaler,
        "label_encoders.joblib":  label_encoders,
    }
    for fname, obj in artifacts.items():
        path = os.path.join(MODEL_DIR, fname)
        joblib.dump(obj, path)
        print(f"  ✔ Saved {fname}")

    # Save metadata
    metadata = {
        "trained_at":      datetime.now().isoformat(),
        "data_source":     args.data,
        "num_samples":     len(df),
        "feature_names":   feature_names,
        "risk_label_map":  risk_label_map,
        "numeric_features":    NUMERIC_FEATURES,
        "binary_features":     BINARY_FEATURES,
        "categorical_features":CATEGORICAL_FEATURES,
    }
    meta_path = os.path.join(MODEL_DIR, "model_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"  ✔ Saved model_metadata.json")

    print("\n" + "=" * 60)
    print("  Training complete!  Models ready at:")
    print(f"    {MODEL_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
