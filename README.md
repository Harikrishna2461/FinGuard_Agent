# FinGuard

FinGuard is an AI-assisted fraud and portfolio risk investigation system.

```text
Frontend (React)
  -> Backend (FastAPI)
      -> AI System (FastAPI + LangGraph)
          -> Internal agent modules
```

## Services

- `frontend`: React analyst UI.
- `backend`: FastAPI business API, persistence, auth, cases, audit, SAR, and API compatibility.
- `ai_system`: FastAPI AI service with LangGraph orchestration, OpenAI adapter, ML/rules risk adapter, and internal agents.

## Current Features

- Portfolio APIs and AI analysis flow.
- AI Analysis UI with portfolio dropdown.
- LangGraph-backed multi-agent review.
- Returned `analysis_trace` with node, crew, agent, status, duration, and output.
- Market sentiment analysis.
- Case, audit, SAR, search, auth, transaction, alert, and recommendation APIs.
- Docker Compose local stack.
- Backend GitHub Actions deployment to Azure Container Apps.

## Internal Agents

- Alert Intake
- Customer Context
- Risk Assessment
- Risk Detection
- Explanation
- Escalation Summary
- Portfolio Analysis
- Market Intelligence
- Compliance

## Run Locally With Docker

Create `ai_system/.env`:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-5.4-mini
OPENAI_REASONING_EFFORT=medium
```

Start the stack:

```bash
docker compose up --build
```

URLs:

- Frontend: `http://localhost:13000`
- Backend: `http://localhost:15050`
- AI system: `http://localhost:18000`

The Docker frontend is built with:

```text
REACT_APP_API_BASE_URL=http://localhost:15050
```

Backend CORS is configured in Compose as:

```text
CORS_ORIGINS=http://localhost:13000,http://localhost:3000
```

## Main User Flow

1. Open `http://localhost:13000/ai-analysis`.
2. Select a portfolio.
3. Click `Run Analysis`.
4. Review progress and final real `analysis_trace`.

## Important API Docs

See [api.md](api.md) for the concise frontend/backend contract.

Common endpoints:

- `GET /health`
- `GET /api/portfolios`
- `GET /api/portfolios/{id}`
- `GET /api/portfolios/{id}/assets`
- `GET /api/portfolios/{id}/transactions`
- `POST /api/portfolios/{id}/analyze`
- `GET /api/symbols`
- `GET /api/sentiment?symbols=AAPL,MSFT`

## Azure Backend CI/CD

Workflow:

```text
.github/workflows/deploy-backend.yml
```

It builds `backend/Dockerfile` for `linux/amd64`, tags the image with `${{ github.sha }}`, pushes to:

```text
finguardacr.azurecr.io/finguard-backend:${{ github.sha }}
```

and updates Azure Container App:

```text
finguard-backend
```

Required GitHub secrets:

- `AZURE_CREDENTIALS`
- `AZURE_RESOURCE_GROUP`

## Current Gaps

- Several frontend pages still use static/local data instead of backend APIs.
- Agent trace is real after completion, but not streamed live yet.
- Frontend lockfile is out of sync, so Docker currently uses `npm install`.
- Frontend auth UI is not implemented.
- SQLite is suitable for demo, but cloud persistence needs hardening.
- CI/CD currently deploys backend only.

## Related Docs

- [PRD.md](PRD.md)
- [api.md](api.md)
- [FINGUARD_COMPREHENSIVE_GUIDE.md](FINGUARD_COMPREHENSIVE_GUIDE.md)
