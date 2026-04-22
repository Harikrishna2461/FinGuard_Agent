# FinGuard — Explainable & Responsible AI Report

Satisfies Briefing p.12 (Explainable & Responsible AI report) and Presentation
Guideline §4. This report shows how each stage of the FinGuard lifecycle aligns
with the **IMDA Model AI Governance Framework 2.0 (2024)**, the four NIST AI
RMF functions (Govern, Map, Measure, Manage), and the OECD AI Principles.

---

## 1. Governance context — IMDA Model AI Governance Framework mapping

The IMDA Framework organises AI governance into **four pillars**. FinGuard's
implementation is mapped below.

### Pillar 1 — Internal Governance Structures & Measures

| IMDA control | FinGuard implementation | Evidence |
|---|---|---|
| Clear roles & responsibilities | RBAC with `analyst`, `supervisor`, `admin` roles; SAR filing requires supervisor+ | `backend/app/auth.py`, `backend/app/sar.py` |
| Risk-management & internal controls | AI Security Risk Register reviewed per release | `docs/ai_security_risk_register.md` |
| Staff training & awareness | Knowledge-base curated per domain (9 domains) | `backend/data/knowledge_base/` |
| Decision-review process | Every case has an event timeline (CaseEvent) + hash-chained audit log | `backend/app/audit.py`, `backend/app/cases.py` |

### Pillar 2 — Determining the Level of Human Involvement

FinGuard operates at **Human-over-the-loop** for the triage tier and
**Human-in-the-loop** for SAR filing and escalation:

| Decision | Automation tier | Why | Where enforced |
|---|---|---|---|
| Transaction risk score | Human-over-loop (automatic) | Rule + ML scoring is deterministic | `backend/ml/risk_scoring_engine.py` |
| Case state change → `escalated` | Human-in-loop (supervisor required) | High-impact | `backend/app/cases.py` + `require_role` |
| SAR filing | Human-in-loop (supervisor+ required) | Regulatory | `backend/app/sar.py` |
| LLM explanation | Human-over-loop + review | LLM output rendered as caveat text | `ExplanationAgent` |

### Pillar 3 — Operations Management

| IMDA control | FinGuard implementation |
|---|---|
| Good data accountability practices | Tenant-scoped SQL, audit trail, append-only logs |
| Minimising inherent bias | Synthetic training data, no protected-attribute features (no race/gender/religion); sector + country are **decision-relevant**, not protected |
| Robust model training & selection | 3-tier: rules → ML → LLM. LLM only invoked for 40-60 borderline scores. |
| Ongoing monitoring, review, tuning | Prometheus `/api/metrics`, structured JSON logs, guardrail block counter |

### Pillar 4 — Stakeholder Interaction & Communication

| IMDA control | FinGuard implementation |
|---|---|
| Transparency (tell users AI is used) | UI displays "AI analysis" badge; explanations rendered in plain text |
| Feedback channels | Case notes, analyst override → audit log |
| Explainability | `ExplanationAgent` produces stakeholder-appropriate rationales (customer / advisor / compliance / executive) |

---

## 2. Lifecycle alignment (Govern → Map → Measure → Manage)

| Stage | Responsible-AI practice | Artefact |
|---|---|---|
| **Data sourcing** | Only synthetic transactions used; no real PII enters the classifier | `backend/ml/data/transaction_risk_training_data.csv` |
| **Training** | Balanced-class target; no protected attributes in feature list | `backend/ml/train_risk_model.py` |
| **Evaluation** | Feature attribution (SHAP / permutation importance) + per-slice fairness check | `build/shap_feature_importance.csv`, `build/fairness_report.json` |
| **Packaging** | Model manifest with SHA-256 per release | `scripts/register_model.py`, CI job `model-versioning` |
| **Deployment** | Human-in-loop gates on supervisor actions; guardrails on every LLM call | `backend/agents/guardrails.py`, `backend/app/auth.py` |
| **Operation** | JSON logs, Prometheus metrics, append-only audit chain | `backend/app/observability.py`, `backend/app/audit.py` |
| **Retirement** | Model hashes allow rollback; audit trail preserved for 7-year retention (regulatory default) | Audit table schema |

---

## 3. Fairness analysis

See `scripts/fairness_check.py` → `build/fairness_report.json`.

### Method

The script groups the evaluation dataset by four decision-relevant slices and
computes:

* **Selection rate** — P(classifier predicts high/critical | slice)
* **Demographic-parity difference** — selection rate of slice minus overall
  selection rate
* **False-positive rate** — predicted high/critical but ground truth low/medium

### Key findings (current run)

| Slice axis | Widest demographic-parity gap | Interpretation |
|---|---:|---|
| `sector` | `Cryptocurrency` +0.61 vs. `Corporate` −0.39 | **Expected & domain-justified** — crypto is a high-risk sector by regulation; not a fairness concern |
| `receiver_country` | Sanctioned-country codes (IR, KP) → 1.0 | **Expected** — regulatory hard-block, not a model bias |
| `transaction_type` | Within ±0.15 | OK |
| `channel` | Within ±0.10 | OK |

### What we DO NOT do (by design)

* The model never receives **race, gender, age, religion, nationality** of the
  customer. Only the transaction's `receiver_country` (a regulatory attribute
  under FATF guidance) is used.
* FinGuard therefore **cannot** directly produce disparate-impact harm on
  protected classes. Any disparity found is a function of transaction
  characteristics.

### Mitigation backlog

If a future iteration adds customer attributes we would:
1. Remove any protected attribute from the feature set.
2. Apply `fairlearn.reductions.ExponentiatedGradient` to enforce demographic
   parity at training time.
3. Monitor post-deployment parity via the `/api/metrics` histogram (sliced
   counters).

---

## 4. Explainability

### Approach

| Audience | Mechanism | Where |
|---|---|---|
| Customer | Plain-language rationale ("why this was flagged") | `ExplanationAgent.explain_alert(audience="customer")` |
| Advisor | Top contributing rules + ML confidence | `score()` result includes `rule_details`, `ml_details` |
| Compliance | Full scoring breakdown + audit event | `CaseEvent` timeline |
| Model owner | Feature attribution + fairness report | `scripts/shap_analysis.py` + `scripts/fairness_check.py` |

### Feature-attribution snapshot (permutation importance on the current model)

```
portfolio_concentration_pct    0.2093
customer_avg_txn_amount        0.0480
time_of_day_hour               0.0200
market_volatility_index        0.0160
amount                         0.0027
```

The top-5 drivers are all **decision-relevant features** (concentration risk,
account spending baseline, timing, market regime, absolute amount). No
protected-attribute proxy appears in the top-20.

### Known limitation

The current classifier was trained on 150 synthetic rows; attribution values
are directionally correct but not statistically powered. Production roll-out
would retrain on at least 50k labelled transactions per regulator guidance.

---

## 5. Bias-mitigation strategy (already implemented)

1. **No protected attributes in the feature set** — verified in
   `backend/ml/train_risk_model.py::NUMERIC_FEATURES` and
   `CATEGORICAL_FEATURES`.
2. **Rules override ML** for regulatory hard blocks (sanctioned countries).
   This removes one class of ML-drift harm: an attacker cannot poison the
   model into ignoring OFAC.
3. **LLM only advisory** for borderline cases — never decisive.
4. **Audit log** captures every decision so disparate impact can be
   retro-audited per tenant, per slice.

---

## 6. Governance framework cross-reference

| IMDA Pillar | NIST AI RMF | OECD AI Principles |
|---|---|---|
| 1. Internal Governance | Govern | Accountability |
| 2. Human Involvement | Govern + Manage | Human-centred values |
| 3. Operations Management | Map + Measure | Robustness, security, safety |
| 4. Stakeholder Communication | Manage | Transparency, explainability |

FinGuard's mapping above satisfies **at least one control per pillar** in all
three frameworks.

---

## 7. Open items / backlog

| Item | Owner | Target release |
|---|---|---|
| Retrain on ≥50k real (anonymised) transactions | ML lead | v1.0 |
| Add `fairlearn` fairness-constrained training | ML lead | v1.1 |
| Stakeholder survey for explanation clarity | Product | v1.0 |
| Counterfactual "what-if" explanations in UI | Frontend | v1.1 |
| Third-party ethics audit | Compliance | v1.0 |
