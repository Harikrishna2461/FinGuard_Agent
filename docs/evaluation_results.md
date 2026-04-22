# FinGuard — Evaluation Results

Satisfies Presentation Guideline §8 (Evaluation and Testing Summary).

## 1. Harness

`backend/tests/evaluation/test_agent_metrics.py` runs seven golden cases
defined in `backend/tests/evaluation/golden_cases.json`. Each case asserts
one of:

* expected risk-label bound (min / max)
* expected `hard_block` outcome
* expected flag present in `flags`
* expected guardrail block with specific reason
* expected PII redaction tokens

Three metrics are computed:

| Metric | What it measures | Gate |
|---|---|---|
| `task_success_rate` | fraction of golden cases meeting every assertion | ≥ 0.80 |
| `groundedness` | fraction of risk-engine outputs where every flag is explained by `rule_details` or `ml_details` | ≥ 0.70 |
| `guardrail_block_rate` | fraction of guardrail cases blocked with the correct reason | ≥ 0.95 |

The CI job `ai-security-tests` runs both `tests/ai_security/` and
`tests/evaluation/`. A red result blocks merge.

## 2. Results (latest run)

| Metric | Target | Achieved |
|---|---:|---:|
| `task_success_rate` | ≥ 0.80 | **1.00** (7/7) |
| `groundedness` | ≥ 0.70 | **1.00** |
| `guardrail_block_rate` | ≥ 0.95 | **1.00** |

Full JSON: `build/evaluation_report.json`.

### Per-case breakdown

| Case | What it covers | Outcome |
|---|---|---|
| GC-01 | routine domestic purchase — label ≤ medium | ✅ |
| GC-02 | sanctioned country hard-block | ✅ |
| GC-03 | extreme deviation from customer average | ✅ |
| GC-04 | velocity-burst detection | ✅ |
| GC-05 | borderline case → valid result shape | ✅ |
| GC-06 | guardrail blocks "ignore previous instructions" | ✅ |
| GC-07 | PII redaction (phone / email / account) | ✅ |

## 3. Other test layers (for completeness)

| Layer | Location | Count |
|---|---|---:|
| Unit — ML engine | `backend/ml/test_engine.py` | 3 |
| Integration — crew + API | `backend/test_integration.py` | 7 |
| Knowledge base | `backend/test_knowledge_base.py` | 1 |
| **AI security** | `backend/tests/ai_security/` | 31 |
| **Evaluation harness** | `backend/tests/evaluation/` | 1 (parametrised across 7 cases) |
| **Total (gated)** | | **42+** |

## 4. Operating the harness

```bash
cd backend && python -m pytest tests/evaluation/ -q -s
```

To add a new golden case, append a JSON block to
`backend/tests/evaluation/golden_cases.json`. No code change required.

## 5. Known limitations

* The harness is deterministic — it does NOT call Groq. Groundedness of
  LLM narratives is currently asserted indirectly (by checking that every
  flag has a structured rule / ML source). A future iteration can add an
  LLM-as-judge step for narrative groundedness.
* Seven golden cases is a demonstration baseline, not a full production
  regression set. Expanding to ≥50 cases is in the backlog.
