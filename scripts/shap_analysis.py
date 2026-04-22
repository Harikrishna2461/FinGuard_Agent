"""Generate SHAP feature-attribution for the FinGuard risk classifier.

Produces:
  build/shap_feature_importance.csv  — mean |SHAP value| per feature
  build/shap_summary.png             — bar plot of top-20 drivers (if matplotlib)

Usage:
  python scripts/shap_analysis.py

If `shap` / `matplotlib` are not installed, the script degrades gracefully to
permutation-importance from scikit-learn so the CI step still produces
explainability artefacts without adding heavyweight deps to requirements.txt.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

import joblib
import numpy as np
import pandas as pd

MODEL_DIR = ROOT / "backend" / "ml" / "models"
TRAIN_CSV = ROOT / "backend" / "ml" / "data" / "transaction_risk_training_data.csv"
OUT = ROOT / "build"
OUT.mkdir(exist_ok=True)


def _load():
    clf = joblib.load(MODEL_DIR / "risk_classifier.joblib")
    scaler = joblib.load(MODEL_DIR / "scaler.joblib")
    encoders = joblib.load(MODEL_DIR / "label_encoders.joblib")
    meta = json.loads((MODEL_DIR / "model_metadata.json").read_text())
    return clf, scaler, encoders, meta


def _prepare(df: pd.DataFrame, scaler, encoders, meta) -> pd.DataFrame:
    from ml.train_risk_model import NUMERIC_FEATURES  # reuse training contract
    for col in meta["categorical_features"]:
        le = encoders[col]
        df[col] = df[col].astype(str).map(lambda v: v if v in le.classes_ else le.classes_[0])
        df[col] = le.transform(df[col])
    # Derived features
    avg = df["customer_avg_txn_amount"].replace(0, 1)
    df["amount_to_avg_ratio"] = df["amount"] / avg
    df["velocity_ratio"] = np.where(
        df["num_txns_last_24h"] > 0,
        df["num_txns_last_1h"] / df["num_txns_last_24h"].replace(0, 1),
        0,
    )
    bins = [-1, 30, 90, 365, 730, 10**9]
    df["account_maturity"] = pd.cut(df["account_age_days"], bins, labels=[0, 1, 2, 3, 4]).astype(int)
    df["is_cross_border"] = (df.get("sender_country", "US") != df.get("receiver_country", "US")).astype(int)
    df["has_failed_logins"] = (df["failed_login_attempts_24h"] > 0).astype(int)
    scale_cols = NUMERIC_FEATURES + ["amount_to_avg_ratio", "velocity_ratio", "failed_login_attempts_24h"]
    df[scale_cols] = scaler.transform(df[scale_cols])
    return df[meta["feature_names"]]


def _shap_importance(clf, X: pd.DataFrame) -> pd.Series:
    try:
        import shap  # type: ignore
    except ImportError:
        print("[info] `shap` not installed — falling back to permutation importance.")
        from sklearn.inspection import permutation_importance
        perm = permutation_importance(clf, X, clf.predict(X), n_repeats=5, random_state=0)
        return pd.Series(perm.importances_mean, index=X.columns).sort_values(ascending=False)
    expl = shap.TreeExplainer(clf)
    sv = expl.shap_values(X)
    arr = np.asarray(sv)
    if arr.ndim == 3:  # multi-class
        arr = np.abs(arr).mean(axis=0)
    return pd.Series(np.abs(arr).mean(axis=0), index=X.columns).sort_values(ascending=False)


def main() -> None:
    if not TRAIN_CSV.exists():
        print(f"[error] training CSV missing: {TRAIN_CSV}", file=sys.stderr)
        sys.exit(1)
    clf, scaler, encoders, meta = _load()
    df = pd.read_csv(TRAIN_CSV)
    X = _prepare(df.copy(), scaler, encoders, meta)
    imp = _shap_importance(clf, X)
    csv_path = OUT / "shap_feature_importance.csv"
    imp.to_csv(csv_path, header=["mean_abs_shap"])
    print(f"wrote {csv_path}")
    print("\nTop-10 drivers of risk classification:")
    print(imp.head(10).to_string())

    try:
        import matplotlib.pyplot as plt  # type: ignore
        top = imp.head(20)[::-1]
        plt.figure(figsize=(8, 7))
        plt.barh(top.index, top.values)
        plt.title("Top-20 SHAP drivers — FinGuard risk classifier")
        plt.xlabel("mean |SHAP value|")
        plt.tight_layout()
        fig = OUT / "shap_summary.png"
        plt.savefig(fig, dpi=120)
        print(f"wrote {fig}")
    except ImportError:
        pass


if __name__ == "__main__":
    main()
