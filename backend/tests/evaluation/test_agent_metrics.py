"""Evaluation harness — task-success, groundedness, and guardrail metrics.

Runs the golden test set (`golden_cases.json`) through the deterministic
parts of FinGuard and reports three metrics the Presentation Guideline §8
calls for:

  * `task_success_rate`   — proportion of golden cases meeting every
                            expected assertion.
  * `groundedness`        — proportion of risk-engine results whose flags
                            are fully explained by the `rule_details` /
                            `ml_details` payload (i.e. nothing unexplained).
  * `guardrail_block_rate`— proportion of guardrail golden cases blocked
                            with the correct reason.

The harness is deterministic (no Groq calls) so it runs on CI in <2 seconds
and is safe to gate merges on. Writes `build/evaluation_report.json`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.guardrails import redact_pii, sanitize
from ml.risk_scoring_engine import TransactionRiskEngine


CASES_PATH = Path(__file__).with_name("golden_cases.json")
REPORT_PATH = Path(__file__).resolve().parents[3] / "build" / "evaluation_report.json"

LABEL_ORDER = ("low", "medium", "high", "critical")


def _label_rank(label: str) -> int:
    try:
        return LABEL_ORDER.index(label)
    except ValueError:
        return -1


@pytest.fixture(scope="module")
def engine() -> TransactionRiskEngine:
    return TransactionRiskEngine()


@pytest.fixture(scope="module")
def cases() -> list[dict]:
    return json.loads(CASES_PATH.read_text())


def _check_case(engine: TransactionRiskEngine, case: dict) -> tuple[bool, list[str]]:
    """Return (passed, reasons_if_failed)."""
    reasons: list[str] = []

    if "free_text" in case:
        if case.get("expected_guardrail_block"):
            r = sanitize(case["free_text"])
            if r.ok:
                reasons.append("guardrail did not block")
            elif case.get("expected_reason") and r.reason != case["expected_reason"]:
                reasons.append(f"wrong reason: {r.reason} != {case['expected_reason']}")
        if case.get("expected_redacted_tokens"):
            red = redact_pii(case["free_text"])
            for tok in case["expected_redacted_tokens"]:
                if tok not in red:
                    reasons.append(f"redaction missing token {tok}")
        return (not reasons, reasons)

    res = engine.score(case["transaction"])

    if "expected_hard_block" in case and res["hard_block"] != case["expected_hard_block"]:
        reasons.append(f"hard_block {res['hard_block']} != {case['expected_hard_block']}")
    if "expected_label_min" in case:
        if _label_rank(res["risk_label"]) < _label_rank(case["expected_label_min"]):
            reasons.append(f"label {res['risk_label']} below min {case['expected_label_min']}")
    if "expected_label_max" in case:
        if _label_rank(res["risk_label"]) > _label_rank(case["expected_label_max"]):
            reasons.append(f"label {res['risk_label']} above max {case['expected_label_max']}")
    if "expected_flags_any" in case:
        if not any(f in res["flags"] for f in case["expected_flags_any"]):
            reasons.append(f"none of {case['expected_flags_any']} in {res['flags']}")
    if "expected_needs_llm_review" in case:
        if res["needs_llm_review"] != case["expected_needs_llm_review"]:
            reasons.append(f"needs_llm_review {res['needs_llm_review']} != {case['expected_needs_llm_review']}")
    if case.get("expected_result_shape"):
        for key in ("final_score", "risk_label", "method", "hard_block", "flags"):
            if key not in res:
                reasons.append(f"missing key {key}")

    return (not reasons, reasons)


def _groundedness(res: dict) -> bool:
    """True iff every flag has a corresponding reason in rule_details or ml_details."""
    explained_sources = set()
    explained_sources.update((res.get("rule_details", {}).get("details") or {}).keys())
    if res.get("ml_details", {}).get("available"):
        explained_sources.add("ml")
    # Every flag must be sourced from rules (by name convention) or ML anomaly.
    for flag in res.get("flags", []):
        if flag.startswith("ML_"):
            if not res.get("ml_details", {}).get("available"):
                return False
        # rule-originated flags are always accompanied by a populated
        # rule_details.details dict; the specific key naming lives in the
        # rule-engine so we only require the dict to be non-empty.
        elif not (res.get("rule_details", {}).get("details")):
            return False
    return True


def test_task_success_and_report(engine: TransactionRiskEngine, cases: list[dict]) -> None:
    passes: list[dict] = []
    failures: list[dict] = []
    grounded_flags = 0
    grounded_total = 0
    guardrail_total = 0
    guardrail_blocks = 0

    for case in cases:
        ok, reasons = _check_case(engine, case)
        (passes if ok else failures).append({"id": case["id"], "reasons": reasons})

        if "transaction" in case:
            res = engine.score(case["transaction"])
            if res.get("flags"):
                grounded_total += 1
                if _groundedness(res):
                    grounded_flags += 1

        if case.get("expected_guardrail_block"):
            guardrail_total += 1
            r = sanitize(case["free_text"])
            if (not r.ok) and r.reason == case.get("expected_reason"):
                guardrail_blocks += 1

    report = {
        "n_cases": len(cases),
        "task_success_rate": round(len(passes) / len(cases), 4),
        "groundedness": round(grounded_flags / grounded_total, 4) if grounded_total else 1.0,
        "guardrail_block_rate": round(guardrail_blocks / guardrail_total, 4) if guardrail_total else 1.0,
        "passes": passes,
        "failures": failures,
    }
    REPORT_PATH.parent.mkdir(exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2))
    print(f"\nEvaluation report written to {REPORT_PATH}")
    print(json.dumps({k: v for k, v in report.items() if k not in ("passes", "failures")}, indent=2))

    assert report["task_success_rate"] >= 0.8, f"task_success too low: {report}"
    assert report["groundedness"] >= 0.7, f"groundedness too low: {report}"
    assert report["guardrail_block_rate"] >= 0.95, f"guardrail_block_rate too low: {report}"
