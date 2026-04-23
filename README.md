# FinGuard

FinGuard is now a two-service backend system:

- `backend`: FastAPI service for business resources, persistence, and legacy-compatible API routes.
- `ai_system`: FastAPI service for OpenAI-backed AI strategy and LangGraph orchestration.
- `frontend`: React UI, run separately from the backend services.

The old Flask + CrewAI runtime has been removed. The current direction is:

```text
frontend -> backend -> ai_system -> LangGraph/internal agents
```

## Current Status

The backend has been refactored to preserve the old backend route surface while separating AI behavior into `ai_system`.

Implemented backend areas:

- Portfolio, assets, transactions, alerts, sentiment, recommendation, and search APIs.
- Auth compatibility: register, login, and me.
- Case workflow: list, detail, create, assign, notes, transition, analyze, and customer-360.
- Hash-chained audit log and verification endpoint.
- SAR JSON/PDF export.
- SQLite schema compatibility tables for tenants, users, audit logs, risk assessments, market trends, cases, and case events.

Implemented AI areas:

- LangGraph-backed portfolio review flow.
- Internal agent modules for risk, portfolio, compliance, explanation, market, alert intake, customer context, and escalation.
- OpenAI model service via `OPENAI_API_KEY`.
- Legacy hybrid risk engine adapter. If trained ML model files are missing, risk scoring falls back to rules.

## Architecture

```text
FinGuard_Agent/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routers
│   │   ├── main.py           # app setup and router registration
│   │   ├── db.py             # SQLite schema + helpers
│   │   ├── auth.py           # legacy-compatible auth helpers
│   │   ├── audit.py          # hash-chain audit helpers
│   │   ├── ai_client.py      # HTTP client to ai_system
│   │   └── schemas.py
│   ├── ml/                   # reused legacy ML risk engine
│   ├── Dockerfile
│   └── requirements.txt
├── ai_system/
│   ├── app/
│   │   ├── agents/           # internal agent strategies
│   │   ├── main.py           # FastAPI app
│   │   ├── llm.py            # OpenAI adapter
│   │   ├── ml.py             # ML adapter
│   │   └── orchestrator.py   # thin wrapper over LangGraph
│   ├── langgraph/
│   │   ├── graph.py
│   │   ├── nodes.py
│   │   ├── state.py
│   │   └── workflows/
│   ├── langgraph.json
│   ├── .env.example
│   └── Dockerfile
├── frontend/
├── docker-compose.yml
└── FINGUARD_COMPREHENSIVE_GUIDE.md
```

## Run With Docker

Create `ai_system/.env`:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-5.4-mini
OPENAI_REASONING_EFFORT=medium
```

Start services:

```bash
docker compose up --build
```

Service URLs:

- Backend: `http://localhost:15050`
- AI System: `http://localhost:18000`

Inside Docker, backend calls AI through `http://ai_system:8000`.

## Verified Smoke Tests

The Docker stack was rebuilt and tested through the Compose network.

Passed:

- backend health
- `ai_system` health
- auth register/login
- portfolio creation
- manual case creation
- case note and detail
- audit chain verification
- SAR JSON export
- transaction creation
- quick recommendation through `backend -> ai_system`

Known runtime note:

- If `backend/ml/models/*` trained model files are missing, risk scoring logs a model-metadata warning and falls back to rules.

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

Portfolio:

- `POST /api/portfolio`
- `POST /api/portfolios`
- `GET /api/portfolios`
- `GET /api/portfolio/{id}`
- `GET /api/portfolios/{id}`
- `POST /api/portfolio/{id}/asset`
- `GET /api/portfolio/{id}/assets`
- `POST /api/portfolio/{id}/transaction`
- `GET /api/portfolio/{id}/transactions`
- `POST /api/portfolio/{id}/analyze`
- `POST /api/portfolio/{id}/quick-recommendation`
- `POST /api/portfolio/{id}/recommendation`
- `POST /api/portfolio/{id}/alert`
- `GET /api/portfolio/{id}/alerts`

Transaction helpers:

- `POST /api/transaction/score-risk`
- `POST /api/transaction/get-ai-insights`

Market and search:

- `GET /api/sentiment`
- `GET /api/sentiment/{symbol}`
- `POST /api/search/analyses`
- `POST /api/search/risks`
- `POST /api/search/market`

Cases, audit, SAR:

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

Main path:

- `GET /health`
- `POST /orchestrate/portfolio-review`

Debug/direct agent paths:

- `POST /agents/risk/invoke`
- `POST /agents/portfolio/invoke`
- `POST /agents/compliance/invoke`
- `POST /market/sentiment`
- `POST /market/recommendation`
- `POST /risk/score-transaction`
- `POST /explanation/transaction-insights`

The production path should stay `backend -> /orchestrate/portfolio-review`. Direct agent endpoints are mainly for debugging and future extraction.

## Agent Parity Status

Current agents now expose legacy class names and helper methods inside `ai_system/app/agents`, while keeping module-function implementations for LangGraph.

Aligned legacy names:

- `AlertIntakeAgent`
- `CustomerContextAgent`
- `RiskAssessmentAgent`
- `RiskDetectionAgent`
- `ExplanationAgent`
- `EscalationCaseSummaryAgent`
- `PortfolioAnalysisAgent`
- `MarketIntelligenceAgent`
- `ComplianceAgent`

Thin legacy-named shim modules are also present, such as `risk_assessment_agent.py` and `portfolio_analysis_agent.py`.

## Minimal API Flow

```bash
curl -X POST http://localhost:15050/api/portfolio \
  -H "Content-Type: application/json" \
  -d '{"name":"Demo Portfolio","initial_investment":10000}'

curl -X POST http://localhost:15050/api/portfolio/1/transaction \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","type":"buy","quantity":2,"price":175}'

curl -X POST http://localhost:15050/api/portfolio/1/quick-recommendation \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Development Notes

- Backend config defaults live in `backend/app/main.py`.
- `ai_system` secrets live in `ai_system/.env`; do not commit real keys.
- `backend/agents` is removed.
- CrewAI is removed from the active runtime.
- LangGraph config lives in `ai_system/langgraph.json`.
- The Flask HTML console from legacy `/` is not restored; current `/` returns JSON status.
