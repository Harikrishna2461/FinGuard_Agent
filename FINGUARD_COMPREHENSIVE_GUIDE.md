# FinGuard Comprehensive Guide

Last updated: 2026-04-25

## 1. What FinGuard Is

FinGuard is a fraud and portfolio risk investigation tool. It combines the `frontendv2` analyst UI, a FastAPI backend, and a LangGraph-based AI system with internal agents.

The product is designed for:

- portfolio and transaction review
- fraud and risk analysis
- market sentiment checks
- case workflow
- audit and SAR export
- explainable multi-agent AI output

## 2. Architecture

```text
frontendv2 Static SPA
  -> FastAPI Backend
      -> SQLite persistence
      -> AI System over HTTP
          -> LangGraph workflow
          -> Internal agents
          -> OpenAI model adapter
          -> ML/rules risk adapter
```

Service responsibilities:

- `frontend`: Docker service name for the active analyst UI, built from `frontendv2/`.
- `frontendv2`: primary analyst UI, portfolio selection, AI trace display, sentiment UI, cases, and search.
- `frontend/`: legacy React prototype retained for reference.
- `backend`: stable API, persistence, auth, cases, audit, SAR, and AI proxying.
- `ai_system`: model calls, LangGraph orchestration, agent strategy, and trace metadata.

## 3. Main Workflow

1. User opens the frontend.
2. User selects a portfolio in AI Analysis.
3. Frontend calls backend portfolio endpoints.
4. Frontend calls `POST /api/portfolios/{id}/analyze`.
5. Backend builds a normalized payload and calls `ai_system`.
6. AI system runs LangGraph and internal agents.
7. AI system returns final output plus `analysis_trace`.
8. Frontend renders the real trace and final analysis.

## 4. Internal Agents

Current agent list:

- Alert Intake
- Customer Context
- Risk Assessment
- Risk Detection
- Explanation
- Escalation Summary
- Portfolio Analysis
- Market Intelligence
- Compliance

The agents are code-level modules inside `ai_system`, not separate services.

## 5. LangGraph Flow

Current portfolio review graph:

```text
ingest_request
  -> quick: run_quick_recommendation
  -> full: run_full_crew_one
       -> run_full_crew_two
       -> run_full_crew_three
       -> compile_full_response
```

Returned trace events include:

- `sequence`
- `type`
- `node`
- `crew`
- `name`
- `status`
- `duration_ms`
- `body`

The trace is real after completion. It is not yet streamed live while the request is running.

## 6. Running Locally

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

Open:

```text
http://localhost:13000
```

Service URLs:

- Frontend: `http://localhost:13000`
- Backend: `http://localhost:15050`
- AI system: `http://localhost:18000`

## 7. Frontend Configuration

`frontendv2` calls the backend through same-origin `/api` requests and nginx proxies them to:

```text
BACKEND_URL=http://backend:5000
```

For cloud deployment, set `BACKEND_URL` to the deployed backend origin visible from the frontend container or host.

## 8. Backend Configuration

Important environment variables:

```text
AI_SYSTEM_URL=http://ai_system:8000
AI_SYSTEM_TIMEOUT_SECONDS=90
CORS_ORIGINS=http://localhost:13000,http://localhost:3000
AUTH_ENFORCED=false
JWT_SECRET=<set-in-production>
BACKEND_DB_PATH=./data/backend.db
```

Production notes:

- Set `AUTH_ENFORCED=true`.
- Set a strong `JWT_SECRET`.
- Configure `CORS_ORIGINS` to the deployed frontend origin.
- Use durable storage or a managed database for cloud persistence.

## 9. AI System Configuration

Important environment variables:

```text
OPENAI_API_KEY=<required>
OPENAI_MODEL=gpt-5.4-mini
OPENAI_REASONING_EFFORT=medium
```

If trained ML model files are unavailable, risk scoring falls back to rule-based behavior where supported.

## 10. Key API Groups

See `api.md` for the concise contract.

Main frontend-used endpoints:

- `GET /api/portfolios`
- `GET /api/portfolios/{id}`
- `GET /api/portfolios/{id}/assets`
- `GET /api/portfolios/{id}/transactions`
- `POST /api/portfolios/{id}/analyze`
- `GET /api/symbols`
- `GET /api/sentiment?symbols=AAPL,MSFT`

Other backend capabilities:

- auth
- alerts
- transaction risk scoring
- recommendations
- cases
- audit verification
- SAR JSON/PDF export
- search

## 11. Deployment

Current GitHub Actions workflow:

```text
.github/workflows/deploy-backend.yml
```

It:

- triggers on push to `main`
- builds `backend/Dockerfile`
- uses `linux/amd64`
- tags with `${{ github.sha }}`
- pushes to `finguardacr.azurecr.io/finguard-backend`
- updates Azure Container App `finguard-backend`

Required GitHub secrets:

- `AZURE_CREDENTIALS`
- `AZURE_RESOURCE_GROUP`

Current deployment gap:

- frontend and `ai_system` do not yet have matching CI/CD workflows.

## 12. Current Limitations

- Some `frontendv2` flows currently wait for direct JSON responses because backend SSE endpoints are not implemented yet.
- The legacy `frontend/` React app is still present, but it is no longer the primary served UI.
- Agent trace is returned after completion, not streamed live.
- SQLite is demo-friendly but needs a durable production plan.
- Backend-only CI/CD is not enough for full cloud deployment.

## 13. Recommended Next Steps

1. Add SSE streaming endpoints so `frontendv2` can show live thinking instead of final-only responses.
2. Complete a first-class auth flow for cases instead of manual bearer token pasting.
3. Decide whether to retire or modernize the legacy `frontend/` React app.
4. Add CI/CD for frontend and `ai_system`.
5. Move cloud persistence to durable storage.
