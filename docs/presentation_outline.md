# FinGuard — Presentation Outline

Follows the 8-section Presentation Guideline. Suggested 20-slide deck,
~25 minutes incl. demo. Each bullet below ≈ one slide.

## 1. Introduction & Solution Overview (2 slides)
* Slide 1 — Problem: triage/investigation in financial crime is manual,
  repetitive, and compliance-sensitive. One-sentence solution.
* Slide 2 — What FinGuard does: 9 agents, hybrid rule+ML+LLM, end-to-end
  from alert → SAR. High-level workflow diagram
  (`docs/architecture.md §3 data-flow`).

## 2. System Architecture (3 slides)
* Slide 3 — Logical diagram (`docs/architecture.md §1`). Call out the
  three tiers (client, API, agent, ML, data).
* Slide 4 — Physical diagram (`docs/architecture.md §2`). Containers,
  volumes, Prometheus scrape path.
* Slide 5 — Tech-stack table (`§4`) + architectural-style justification:
  layered + hybrid-ensemble + RAG.

## 3. Agent Design (4 slides)
* Slide 6 — Shared base: `FinancialBaseAgent`, guardrail, retry, RAG.
* Slide 7 — Spotlight 3 key agents: RiskAssessment, Explanation, Escalation
  (purpose / I/O / reasoning / memory / tools).
* Slide 8 — Coordination: `AIAgentOrchestrator` runs 3 sub-crews to stay
  under Groq TPM limits (`docs/agent_design.md §Coordination protocol`).
* Slide 9 — Prompt patterns + fallback strategies table.

## 4. Explainable & Responsible AI (2 slides)
* Slide 10 — IMDA Model AI Governance Framework 2.0 — 4-pillar mapping
  (`docs/responsible_ai.md §1`).
* Slide 11 — Fairness slice table + top-5 SHAP drivers
  (`docs/responsible_ai.md §3–4`).

## 5. AI Security Risk Register (2 slides)
* Slide 12 — Risk register highlights: R01 prompt injection, R04
  hallucination, R05 adversarial ML (table with inherent/residual
  severity).
* Slide 13 — Regression-tested: 31 AI-security tests all green on CI.

## 6. Application Demo (3 slides = live demo)
1. Login as analyst → open an alert on the dashboard.
2. Trigger comprehensive portfolio review → see 3 crews execute
   sequentially.
3. Escalate a case as supervisor → export SAR PDF.
4. Show the audit timeline with hash-chain integrity check.

## 7. MLSecOps / LLMSecOps Pipeline + Demo (3 slides)
* Slide 14 — Pipeline diagram (`docs/mlsecops_pipeline.md §1`).
* Slide 15 — Show a real CI run: lint → tests → AI-security → Trivy →
  model-manifest → staging-deploy.
* Slide 16 — `/api/metrics` in Prometheus; guardrail-block counter
  incrementing live when we paste a prompt-injection payload.

## 8. Evaluation & Testing Summary (1 slide)
* Slide 17 — Table of test counts + metric targets vs. achieved
  (from `docs/evaluation_results.md`).

## Closing (2 slides)
* Slide 18 — Reflection: what worked, what didn't, what's next.
* Slide 19 — Q & A / architecture recap.

---

## Demo pre-flight checklist

- [ ] `docker compose up --build` works on a fresh clone
- [ ] Frontend reachable on `http://localhost:8080`
- [ ] Backend `/api/health` green
- [ ] `/api/metrics` returns Prometheus text
- [ ] A seeded portfolio + 3 alerts + 1 borderline case exist
- [ ] CI run from the last commit is green (show the tab)
- [ ] Have a stored screen recording as backup in case demo network fails
