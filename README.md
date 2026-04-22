# FinGuard

FinGuard is a split portfolio workflow system with a thin backend and a separate AI runtime.

- `backend`: FastAPI service for portfolio and transaction APIs
- `ai_system`: FastAPI service for LangGraph-driven portfolio review
- `frontend`: React UI

The old Flask + CrewAI runtime has been removed. Current direction is `backend -> ai_system -> LangGraph`.

## Architecture

```text
frontend -> backend -> ai_system
```

### Backend
- Owns portfolio and transaction APIs
- Stores data in SQLite
- Builds normalized payloads for AI requests
- Calls `ai_system` over HTTP

### AI System
- Owns AI behavior and orchestration
- Runs a LangGraph portfolio review flow
- Contains internal agent modules:
  - `risk`
  - `portfolio`
  - `compliance`
  - `explanation`
- Reuses the legacy hybrid risk engine through clean adapters

### Current LangGraph flow

```text
ingest_request
  -> run_risk_screen
  -> run_portfolio_review
  -> run_compliance_review
  -> run_explanation
  -> compile_response
```

## Project Structure

```text
FinGuard_Agent/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── db.py
│   │   ├── schemas.py
│   │   └── ai_client.py
│   ├── ml/
│   │   ├── risk_scoring_engine.py
│   │   └── models/
│   ├── data/
│   ├── Dockerfile
│   └── requirements.txt
├── ai_system/
│   ├── app/
│   │   ├── main.py
│   │   ├── orchestrator.py
│   │   ├── schemas.py
│   │   ├── llm.py
│   │   ├── ml.py
│   │   └── agents/
│   ├── langgraph/
│   │   ├── graph.py
│   │   ├── state.py
│   │   ├── nodes.py
│   │   └── workflows/
│   ├── langgraph.json
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
├── docker-compose.yml
└── FINGUARD_COMPREHENSIVE_GUIDE.md
```

## Runtime

### Docker Compose

Main runtime path:

```bash
docker compose up --build
```

Service URLs:
- Backend: `http://localhost:5000`
- AI System: `http://localhost:8000`

### Frontend

Frontend is still run separately:

```bash
cd frontend
npm install
npm start
```

Frontend URL:
- `http://localhost:3000`

## Environment

Current backend env example is in [backend/.env.example](backend/.env.example):

```env
BACKEND_DB_PATH=./data/backend.db
AI_SYSTEM_URL=http://localhost:8000
AI_SYSTEM_TIMEOUT_SECONDS=30
```

Optional AI env you may set for richer risk explanations:

```env
GROQ_API_KEY=...
GROQ_MODEL=llama-3.3-70b-versatile
```

## API Overview

### Backend endpoints

- `GET /health`
- `POST /api/portfolios`
- `GET /api/portfolios`
- `GET /api/portfolios/{id}`
- `POST /api/portfolios/{id}/transactions`
- `GET /api/portfolios/{id}/transactions`
- `POST /api/portfolios/{id}/quick-recommendation`

### AI System endpoints

- `GET /health`
- `POST /orchestrate/portfolio-review`
- `POST /agents/risk/invoke`
- `POST /agents/portfolio/invoke`
- `POST /agents/compliance/invoke`

The agent endpoints are useful for debugging. The main production path is the orchestrator endpoint.

## Minimal Flow

### 1. Create a portfolio

```bash
curl -X POST http://localhost:5000/api/portfolios \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo-user",
    "name": "My Portfolio",
    "initial_investment": 100000
  }'
```

### 2. Add a transaction

```bash
curl -X POST http://localhost:5000/api/portfolios/1/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "type": "buy",
    "quantity": 10,
    "price": 180,
    "fees": 5
  }'
```

### 3. Request AI review

```bash
curl -X POST http://localhost:5000/api/portfolios/1/quick-recommendation \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "quick"
  }'
```

## LangGraph Notes

- LangGraph config lives in [ai_system/langgraph.json](ai_system/langgraph.json)
- Primary graph entrypoint is [ai_system/langgraph/graph.py](ai_system/langgraph/graph.py)
- FastAPI currently uses the compiled graph through a thin wrapper in [ai_system/app/orchestrator.py](ai_system/app/orchestrator.py)

This means the runtime is already LangGraph-backed, even though the graph is still small.

## Current Scope

What is implemented now:
- portfolio creation
- transaction recording
- AI portfolio review path
- internal risk/portfolio/compliance/explanation modules
- LangGraph-first orchestration structure

What is intentionally not fully rebuilt yet:
- old large case-management surface
- old broad compliance/audit/auth domain
- full production persistence redesign
- deep multi-workflow graph set

## Development Notes

- `ai_system` is the canonical home for AI behavior
- old backend-side agent package is gone
- old Flask/CrewAI runtime is gone
- legacy ML risk scoring code is reused through adapters, not through the old architecture

For a fuller system description, see [FINGUARD_COMPREHENSIVE_GUIDE.md](FINGUARD_COMPREHENSIVE_GUIDE.md).
