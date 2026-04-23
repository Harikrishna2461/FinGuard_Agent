# FinGuard Agent - Comprehensive System Documentation

**Date:** April 23, 2026  
**Language:** English  
**Version:** 1.1

## Product Overview

FinGuard Agent is an AI-powered financial portfolio monitoring and investigation system. It helps users track portfolios, record transactions, detect risky activity, review market sentiment, and generate AI-assisted recommendations.

Primary use cases:

- Portfolio and holdings management.
- Transaction risk screening.
- Fraud and anomaly detection.
- Market sentiment and recommendation generation.
- Compliance review.
- Case management, audit logging, and SAR export.

Primary users:

- Individual investors.
- Financial advisors.
- Compliance officers.
- Analysts reviewing risky transactions or alerts.

## Technology Stack

Backend:

- FastAPI for the business API.
- Uvicorn as the ASGI server.
- SQLite with direct `sqlite3` helpers.
- Docker and Docker Compose for local runtime.

AI system:

- FastAPI for the AI service.
- LangGraph for orchestration.
- OpenAI API for model calls.
- Default model: `gpt-5.4-mini`.
- Internal agent modules for risk, portfolio, compliance, explanation, market, alert intake, customer context, and escalation.

Machine learning:

- Legacy ML risk engine is reused through adapters.
- If trained model files are unavailable, scoring falls back to rules.

Frontend:

- React.
- React Router.
- Recharts.
- TailwindCSS.
- Axios.
- React Icons.

## System Architecture

```text
Frontend (React)
  -> Backend (FastAPI)
       -> AI System (FastAPI + LangGraph)
            -> Internal agent modules
            -> OpenAI model service
            -> Optional ML risk engine
```

Backend responsibilities:

- Own the public API surface.
- Preserve compatibility with the legacy backend routes.
- Store portfolios, assets, transactions, alerts, cases, audit logs, SAR data, and analysis records.
- Build normalized payloads for AI requests.
- Call `ai_system` over HTTP.

AI system responsibilities:

- Own AI strategy and orchestration.
- Run LangGraph workflows.
- Own prompt/model-facing agent logic.
- Keep agent implementations separate from backend business resources.

## Data Flow

1. The frontend sends an HTTP request to the backend.
2. The backend validates the request and reads/writes SQLite data.
3. If AI is needed, the backend builds a normalized payload.
4. The backend calls `ai_system`.
5. `ai_system` runs the LangGraph workflow or direct agent strategy.
6. The backend stores side effects when needed.
7. The backend returns a legacy-compatible JSON response.

## AI Agents

Agents are internal modules inside one `ai_system` service. They are not separate containers.

Current agent modules:

- `risk`: transaction risk scoring, portfolio risk, fraud/risk review, quick recommendation support.
- `portfolio`: portfolio analysis prompts and summary logic.
- `compliance`: transaction compliance review.
- `explanation`: risk explanation, transaction insight, and analysis summaries.
- `market`: sentiment analysis and investment recommendation prompts.
- `alert_intake`: alert categorization and priority assessment.
- `customer_context`: customer profile/context prompt strategy.
- `escalation`: escalation assessment.

Current LangGraph flow:

```text
ingest_request
  -> quick route: run_quick_recommendation
  -> full route: run_full_crew_one
  -> full route: run_full_crew_two
  -> full route: run_full_crew_three
  -> compile response
```

The previous CrewAI runtime has been removed. The current implementation is strategy-aligned with the legacy agent behavior, but it is not fully interface-identical because current agents are module functions while legacy agents were class methods.

## Backend API Surface

System and catalog:

- `GET /`
- `GET /health`
- `GET /api/health`
- `GET /api/symbols`
- `GET /api/symbols/sectors`

Auth:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

Portfolio, assets, transactions, alerts:

- `POST /api/portfolio`
- `POST /api/portfolios`
- `GET /api/portfolios`
- `GET /api/portfolio/{id}`
- `GET /api/portfolios/{id}`
- `POST /api/portfolio/{id}/asset`
- `GET /api/portfolio/{id}/assets`
- `POST /api/portfolio/{id}/transaction`
- `GET /api/portfolio/{id}/transactions`
- `POST /api/portfolio/{id}/alert`
- `GET /api/portfolio/{id}/alerts`

AI review, market, and search:

- `POST /api/portfolio/{id}/analyze`
- `POST /api/portfolio/{id}/quick-recommendation`
- `POST /api/portfolio/{id}/recommendation`
- `POST /api/transaction/score-risk`
- `POST /api/transaction/get-ai-insights`
- `GET /api/sentiment`
- `GET /api/sentiment/{symbol}`
- `POST /api/search/analyses`
- `POST /api/search/risks`
- `POST /api/search/market`

Cases, audit, and SAR:

- `GET /api/cases`
- `GET /api/cases/{id}`
- `POST /api/cases`
- `POST /api/cases/{id}/assign`
- `POST /api/cases/{id}/notes`
- `POST /api/cases/{id}/transition`
- `POST /api/cases/{id}/analyze`
- `GET /api/cases/{id}/customer-360`
- `GET /api/audit/logs`
- `GET /api/audit/verify`
- `GET /api/sar/{case_id}.json`
- `GET /api/sar/{case_id}.pdf`

## AI System API Surface

Main route:

- `GET /health`
- `POST /orchestrate/portfolio-review`

Debug/direct routes:

- `POST /agents/risk/invoke`
- `POST /agents/portfolio/invoke`
- `POST /agents/compliance/invoke`
- `POST /market/sentiment`
- `POST /market/recommendation`
- `POST /risk/score-transaction`
- `POST /explanation/transaction-insights`

The production path should go through the backend and `POST /orchestrate/portfolio-review`. Direct agent routes are mainly for debugging and future extraction.

## Key Workflows

### Portfolio Creation

```text
Create portfolio request
  -> backend validates payload
  -> backend inserts portfolio row
  -> backend returns portfolio id and metadata
```

### Transaction Recording And Risk Scoring

```text
Add transaction request
  -> backend builds legacy-style risk payload
  -> backend calls ai_system risk scoring
  -> backend writes transaction atomically
  -> backend updates cash/assets where applicable
  -> backend creates alert/case side effects if risk is high
  -> backend returns transaction plus risk result
```

### Quick Portfolio Recommendation

```text
Quick recommendation request
  -> backend reads portfolio, assets, and recent transactions
  -> backend calls ai_system LangGraph quick route
  -> backend persists analysis/search record
  -> backend returns legacy-shaped recommendation output
```

### Full Portfolio Analysis

```text
Full analysis request
  -> backend reads portfolio, assets, and recent transactions
  -> backend calls ai_system LangGraph full route
  -> ai_system runs staged risk, portfolio, and summary nodes
  -> backend persists analysis/search record
  -> backend returns legacy-shaped crew_output response
```

### Case Workflow

```text
Case created manually or from high-risk transaction
  -> analyst reviews case
  -> analyst adds notes or assigns case
  -> analyst transitions case state
  -> audit log records mutations
  -> SAR JSON/PDF can be exported
```

### Audit Workflow

```text
Audited action occurs
  -> audit row is appended
  -> row hash is computed from previous hash plus canonical payload
  -> /api/audit/verify checks chain integrity
```

## Database Model Summary

Current SQLite schema includes:

- `tenants`
- `users`
- `portfolios`
- `assets`
- `transactions`
- `alerts`
- `risk_assessments`
- `market_trends`
- `analyses`
- `cases`
- `case_events`
- `audit_logs`

Important compatibility notes:

- Cases support tenant scoping, state, priority, assignee, SLA, AI analysis, notes, and timeline events.
- Audit logs use `prev_hash` and `entry_hash` for tamper-evident verification.
- SAR exports are generated from case, transaction, portfolio, timeline, and AI analysis data.

## Agent Interface Status

Current agents are module-function based for LangGraph. Legacy agents were class-based.

Closest strategy parity:

- `risk`
- `market`
- `portfolio`
- `compliance` core review

Partial parity:

- `alert_intake` has `process_alert`, but not all old helper methods.
- `customer_context` has profile-building strategy, but not all old history/preference helpers.
- `escalation` has escalation evaluation, but not all old case package/resolution helpers.
- `explanation` has risk explanation and summary helpers, but not all old alert/recommendation/performance/compliance explanation helpers.

## Runtime

Create `ai_system/.env`:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-5.4-mini
OPENAI_REASONING_EFFORT=medium
```

Run:

```bash
docker compose up --build
```

Service URLs:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:15050`
- AI System: `http://localhost:18000`

## Verified Smoke Tests

The Docker stack has been rebuilt and tested through the Compose network.

Passed:

- Backend health.
- AI system health.
- Auth register/login.
- Portfolio creation.
- Manual case creation.
- Case note and detail.
- Audit chain verification.
- SAR JSON export.
- Transaction creation.
- Quick recommendation through `backend -> ai_system`.

Known runtime note:

- If trained ML model files are not present under `backend/ml/models`, risk scoring falls back to rules and logs a non-blocking warning.

## Current Caveats

- The old Flask HTML console at `/` is not restored; current `/` returns JSON status.
- Agent strategy parity is close for core paths, but full class-method interface parity is not complete.
- SQLite is suitable for the current demo and compatibility work, but production deployment should move durable business data to a managed database.

## Summary

FinGuard is now a split backend and AI system:

- FastAPI backend for business APIs and legacy compatibility.
- FastAPI `ai_system` for OpenAI-backed agent strategy.
- LangGraph for orchestration.
- SQLite for current persistence.
- Docker Compose for local runtime.
- Case, audit, and SAR workflows restored at the backend API level.
