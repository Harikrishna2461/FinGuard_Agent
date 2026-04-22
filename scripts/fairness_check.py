"""Fairness check for the FinGuard risk classifier.

Slices the training/eval data by two sensitive-like attributes that exist in
the feature set (sector, receiver_country) and reports:

  * Selection rate (P[pred = high/critical]) per slice
  * Demographic-parity difference vs. the majority slice
  * False-positive rate per slice (where ground truth exists)

The goal is not perfect fairness — with 150 synthetic rows we can't learn
disparate impact reliably — but to **demonstrate the process** and produce an
artefact that the Responsible AI report can reference.

Writes:
  build/fairness_report.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

import joblib  # noqa: F401
import numpy as np
import pandas as pd

from scripts.shap_analysis import _load, _prepare  # reuse

TRAIN_CSV = ROOT / "backend" / "ml" / "data" / "transaction_risk_training_data.csv"
OUT = ROOT / "build"
OUT.mkdir(exist_ok=True)

HIGH_LABELS = {"high", "critical"}


def _slice_metrics(df: pd.DataFrame, preds: np.ndarray, truth: np.ndarray, col: str) -> dict:
    out: dict[str, dict] = {}
    overall_rate = float((np.isin(preds, list(HIGH_LABELS))).mean())
    for val, sub in df.groupby(col):
        idx = sub.index
        p = preds[idx]
        t = truth[idx]
        sel = float(np.isin(p, list(HIGH_LABELS)).mean()) if len(p) else 0.0
        fp = float(((np.isin(p, list(HIGH_LABELS))) & (~np.isin(t, list(HIGH_LABELS)))).mean()) if len(p) else 0.0
        out[str(val)] = {
            "n": int(len(sub)),
            "selection_rate": round(sel, 4),
            "demographic_parity_diff": round(sel - overall_rate, 4),
            "false_positive_rate": round(fp, 4),
        }
    return out


def main() -> None:
    clf, scaler, encoders, meta = _load()
    df_raw = pd.read_csv(TRAIN_CSV)
    df_raw = df_raw.reset_index(drop=True)
    X = _prepare(df_raw.copy(), scaler, encoders, meta)

    # Map integer predictions back to labels
    inv_label_map = {v: k for k, v in meta["risk_label_map"].items()}
    preds = np.array([inv_label_map.get(int(p), "unknown") for p in clf.predict(X)])
    truth = df_raw.get("risk_label", pd.Series(preds)).to_numpy()

    report = {
        "overall_selection_rate": float(np.isin(preds, list(HIGH_LABELS)).mean()),
        "slices": {},
    }

    for col in ("sector", "receiver_country", "transaction_type", "channel"):
        if col in df_raw.columns:
            report["slices"][col] = _slice_metrics(df_raw, preds, truth, col)

    out_path = OUT / "fairness_report.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(f"wrote {out_path}")
    print(json.dumps(report, indent=2)[:1200])


if __name__ == "__main__":
    main()
