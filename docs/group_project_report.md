# FinGuard — Group Project Report

**Project Title**: FinGuard — Multi-Agent Financial Risk Analysis Platform
**Team Number**: _<fill in>_
**Members**: _<name 1>, <name 2>, <name 3>, <name 4>, <name 5>_
**Course**: GC Architecting AI Systems (NUS-ISS) — Practice Module

---

## 1. Executive Summary

* **Objective** — Build a multi-agent AI system that triages suspicious
  financial activity end-to-end: ingest alert → enrich with customer
  context → score risk (rules + ML + LLM) → explain → escalate → file SAR.
* **Scope** — 9 specialised agents on CrewAI, a hybrid three-tier risk
  engine, append-only audit trail, RBAC'd case management, SAR export.
* **Key highlights**
  1. Hybrid deterministic + ML + LLM scoring with rule-layer hard blocks.
  2. Prompt-injection guardrail + AI Security Risk Register mapped to OWASP
     LLM Top-10 and MITRE ATLAS.
  3. Full MLSecOps / LLMSecOps CI/CD pipeline with SAST, dependency CVE
     scan, Trivy image scan, AI-security regression tests, and a SHA-256
     model manifest.
  4. Responsible-AI report aligned to IMDA Model AI Governance Framework
     2.0; SHAP attribution + fairness slicing.
* **Constraints / assumptions** — 150-row synthetic training set; Groq free
  tier (12k TPM rate limit — handled by orchestrator); SQLite for demo,
  PostgreSQL-ready for production.

## 2. System Overview

See [`docs/architecture.md`](architecture.md) for full diagrams. High-level:

* **Client** — React SPA (Dashboard, Portfolio, Alerts, Sentiment, Settings).
* **API** — Flask with 5 blueprints (api, auth, audit, cases, sar).
* **Agents** — CrewAI orchestrator sequences 3 sub-crews (Risk, Portfolio,
  Summary) to stay under the Groq free-tier TPM limit.
* **ML** — `backend/ml/risk_scoring_engine.py` combines a deterministic
  `RuleEngine` (13 rules) with a scikit-learn `GradientBoostingClassifier`
  and `IsolationForest`, and escalates to Groq `llama-3.3-70b` for
  borderline narratives.
* **Data** — SQLite (11 tables) + ChromaDB (9 domain collections) + curated
  knowledge-base markdown.

## 3. System Architecture

See [`docs/architecture.md`](architecture.md):

* Logical architecture diagram (§1)
* Physical / infrastructure diagram (§2)
* Data-flow sequence for a single scoring call (§3)
* Tech-stack table with justification (§4)

## 4. Agent Roles and Design

See [`docs/agent_design.md`](agent_design.md) — one section per agent
covering:

* Purpose and responsibilities
* Input / output schema
* Reasoning pattern + planning
* Memory (short-term / long-term / none)
* Tools integrated
* Communication protocols with other agents
* Prompt patterns and fallback strategies

## 5. Explainable and Responsible AI Practices

See [`docs/responsible_ai.md`](responsible_ai.md) — covers:

* IMDA Model AI Governance Framework 2.0 mapping across all four pillars
* NIST AI RMF and OECD AI Principles cross-reference
* Lifecycle alignment (Govern → Map → Measure → Manage)
* Fairness analysis per slice (`build/fairness_report.json`)
* Feature attribution (`build/shap_feature_importance.csv`)
* Bias-mitigation strategy (no protected attributes + rule overrides)

## 6. AI Security Risk Register

See [`docs/ai_security_risk_register.md`](ai_security_risk_register.md) —
15 risks mapped to OWASP LLM Top-10 and MITRE ATLAS, each with:

* Inherent severity (likelihood × impact)
* Mitigation control and where it is implemented
* Evidence / test reference
* Residual severity

Regression-tested by `backend/tests/ai_security/` (31 tests, green on CI).

## 7. MLSecOps / LLMSecOps Pipeline

See [`docs/mlsecops_pipeline.md`](mlsecops_pipeline.md) for the pipeline
diagram and stage table. Summary:

* **Automated testing** — unit, integration, AI-security (`tests/ai_security/`).
* **Static analysis** — Ruff (lint), Bandit (SAST), pip-audit (dep CVEs).
* **Image security** — Trivy scan on every backend image, SARIF → GitHub
  code-scanning.
* **Model versioning** — `scripts/register_model.py` emits a SHA-256
  manifest of every `.joblib` artefact on every CI run.
* **Deployment** — `docker-compose.yml` for local / staging; manual-approval
  gate before production.
* **Monitoring & alerting** — `backend/app/observability.py` exposes
  `/api/metrics` (Prometheus text), incl. a guardrail-block counter useful
  for anomaly alerting.
* **Logging & auditability** — structured JSON logs per request; append-only
  hash-chained audit log (`backend/app/audit.py`).

## 8. Testing Summary

| Test type | Location | Count | Status |
|---|---|---|---|
| Unit — ML engine | `backend/ml/test_engine.py` | 3 | green |
| Integration — crew + API | `backend/test_integration.py` | 7 | green |
| Knowledge base | `backend/test_knowledge_base.py` | — | green |
| **AI security (NEW)** | `backend/tests/ai_security/` | 31 | green |
| Evaluation harness | `backend/tests/evaluation/` | see §9 | green |

Total: 40+ automated tests, all enforced on CI.

## 9. Evaluation Results

See [`docs/evaluation_results.md`](evaluation_results.md) and
`backend/tests/evaluation/test_agent_metrics.py`:

| Metric | Target | Achieved |
|---|---|---|
| Rule-engine precision (hard-block on sanctioned country) | 100% | 100% |
| Feature perturbation stability (label unchanged for <0.1% numeric change) | 100% | 100% |
| Guardrail prompt-injection block rate | ≥95% | 100% (17/17 payloads) |
| Groundedness of `ExplanationAgent` | ≥0.7 | see harness output |
| Task-success on golden test set | ≥0.8 | see harness output |

## 10. Reflection

**What went well**

* Splitting the risk engine into deterministic rules + ML + LLM turned
  out to be the single most defensive design choice — the rule layer
  absorbs the adversarial-ML attacks (R05) without touching the ML model.
* CrewAI's task-sequencing abstraction kept the orchestrator simple enough
  to add rate-limit graceful degradation in one place.

**What we would do differently**

* Start the knowledge base earlier — RAG quality dominated agent-answer
  quality more than prompt wording did.
* Move to PostgreSQL during development, not at the end; SQLite's
  forward-only ALTER limitations cost two debugging sessions.

**Next release targets**

* Retrain the classifier on ≥50k real transactions.
* Add fairness-constrained training via `fairlearn`.
* Wire the staging-deploy CI job to a real cloud target.
