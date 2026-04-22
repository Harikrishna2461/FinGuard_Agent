# FinGuard — System Architecture

Satisfies Briefing p.12 (System Architecture Document) and Presentation
Guideline §2.

## 1. Logical Architecture

```mermaid
flowchart TB
    subgraph Client [Client Tier]
        UI[React SPA<br/>6 pages · Recharts]
    end

    subgraph API [API Tier · Flask]
        R1[api_bp<br/>portfolio, assets,<br/>alerts, scoring]
        R2[auth_bp<br/>JWT · RBAC]
        R3[cases_bp<br/>case lifecycle]
        R4[sar_bp<br/>SAR export]
        R5[audit_bp<br/>hash-chain]
        OBS[observability.py<br/>JSON log · /api/metrics]
        GR[guardrails.py<br/>prompt-injection · PII]
    end

    subgraph Agents [Agent Tier · CrewAI]
        O[AIAgentOrchestrator]
        A1[AlertIntakeAgent]
        A2[CustomerContextAgent]
        A3[RiskAssessmentAgent]
        A4[RiskDetectionAgent]
        A5[PortfolioAnalysisAgent]
        A6[MarketIntelligenceAgent]
        A7[ComplianceAgent]
        A8[ExplanationAgent]
        A9[EscalationCaseSummaryAgent]
    end

    subgraph ML [ML Tier]
        RE[RuleEngine<br/>13 rules · hard-block]
        MLS[MLScorer<br/>GradientBoosting +<br/>IsolationForest]
        LLM[Groq LLM<br/>llama-3.3-70b]
    end

    subgraph Data [Data Tier]
        DB[(SQLite / PostgreSQL<br/>11 tables)]
        VEC[(ChromaDB<br/>9 domain collections)]
        KB[Curated knowledge base<br/>markdown · read-only]
    end

    UI --> R1 & R2 & R3 & R4 & R5
    R1 -.guarded.-> GR --> O
    O --> A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9
    A3 --> RE --> MLS --> LLM
    A1 & A2 & A3 & A8 -.RAG.-> VEC
    KB -.ingest.-> VEC
    R1 & R3 & R4 & R5 --> DB
    R1 & R2 & R3 & R4 & R5 -.emit.-> OBS
```

### Style justification

* **Layered architecture** (Client → API → Agents → ML → Data): each tier has
  one reason to change, which keeps agent prompt changes isolated from API
  contracts.
* **Hybrid rule+ML+LLM scoring**: rules are fast, deterministic and auditable;
  ML adds fuzzy coverage for unseen combinations; LLM handles the long-tail
  borderline narrative. This is the **Ensemble with Fallback** pattern — best
  of all three without over-trusting any one.
* **RAG over 9 domain-specific ChromaDB collections**: per-agent retrieval
  filter prevents cross-domain hallucination (a compliance question never
  pulls from the market-intelligence collection).
* **Append-only audit chain**: mandatory for FinTech; decouples governance
  from application logic.

## 2. Physical Architecture (deployment)

```mermaid
flowchart LR
    subgraph Edge [Edge]
        User((Analyst<br/>browser))
    end

    subgraph Cluster [Container runtime · Docker/K8s]
        direction LR
        subgraph Frontend [frontend container · nginx]
            S1[static React bundle]
            S2[reverse-proxy /api → backend]
        end
        subgraph Backend [backend container · gunicorn]
            G[gunicorn 2×workers]
            FL[Flask app]
            MET[/api/metrics/]
        end
        subgraph PromStack [ops container]
            P[Prometheus<br/>:9090]
        end
    end

    subgraph External [Managed services]
        G1[Groq API<br/>LLM inference]
        CH[ChromaDB<br/>embedded · volume-mounted]
        SQL[(SQLite volume<br/>→ PostgreSQL in prod)]
    end

    User -- HTTPS --> Frontend
    Frontend -- HTTP --> Backend
    Backend -- HTTPS --> G1
    Backend --> CH
    Backend --> SQL
    P -- scrape --> MET
```

### Infrastructure details

| Component | Image / Tech | Port | Persistence |
|---|---|---|---|
| Frontend | `finguard/frontend:latest` (nginx:1.27-alpine) | 80 → 8080 | — |
| Backend | `finguard/backend:latest` (python:3.11-slim + gunicorn) | 5001 | `backend-data` volume |
| Prometheus | `prom/prometheus:v2.55.0` | 9090 | optional |
| ChromaDB | Embedded in backend | — | `backend-data/chroma` |
| DB | SQLite (dev) / Postgres (prod) | — | `backend-data/finguard.db` |

### Deployment strategy

1. **Build**: `docker build -f backend/Dockerfile .` and
   `docker build -f frontend/Dockerfile .`
2. **Scan**: Trivy HIGH/CRITICAL fail-safe (CI job `docker-build-scan`).
3. **Ship**: push to registry with immutable tag = git SHA.
4. **Release**: `docker compose up -d` for single-host; Helm chart for K8s
   (future).
5. **Promote**: staging env approves manually → production (CI job
   `deploy-staging` placeholder).

## 3. Data Flow — risk scoring of a single transaction

```mermaid
sequenceDiagram
    autonumber
    participant User as Analyst (UI)
    participant API as Flask API
    participant GR as Guardrail
    participant Engine as RiskEngine
    participant R as RuleEngine
    participant M as MLScorer
    participant L as Groq LLM
    participant Audit as Audit Log

    User->>API: POST /api/transaction/score-risk
    API->>Audit: log request (hash-chained)
    API->>GR: sanitize(free_text)
    GR-->>API: ok | blocked(reason)
    API->>Engine: score(txn)
    Engine->>R: evaluate rules
    R-->>Engine: rule_score, hard_block, flags
    alt hard_block == True
        Engine-->>API: final_score ≥ 90 (rules)
    else
        Engine->>M: predict(txn)
        M-->>Engine: ml_score, ml_anomaly
        Engine->>Engine: blend 0.4·rules + 0.6·ML
        alt borderline 40–60
            Engine->>L: deep-dive narrative
            L-->>Engine: rationale text
        end
        Engine-->>API: final_score, risk_label, method
    end
    API->>Audit: log result
    API-->>User: JSON { score, label, flags, explanation }
```

## 4. Tech Stack

| Layer | Tech | Version | Why |
|---|---|---|---|
| UI | React + TailwindCSS + Recharts | 18.2 | SPA, rich charting, ubiquitous |
| API | Flask + Gunicorn | 3.0 | Minimal, stable, extension-rich |
| ORM | SQLAlchemy | 2.0 | Type-safe, migration-friendly |
| Agent framework | CrewAI | 0.108 | Native multi-agent primitives |
| LLM | Groq (`llama-3.3-70b`) | — | Low-latency, OpenAI-compatible |
| Vector store | ChromaDB | 0.6 | Embeddable, persistent, no server |
| ML | scikit-learn (GradientBoosting + IsolationForest) | 1.8 | CPU-only, interpretable |
| Auth | PyJWT | 2.8 | Standard JWT |
| Container | Docker + Compose | 24 / 2 | Reproducible builds |
| CI | GitHub Actions | — | Already in the team's workflow |
| Metrics | Prometheus text format (`/api/metrics`) | 0.0.4 | Scrape-friendly, no SDK needed |
| Image scan | Trivy | 0.50 | Free, SARIF → GitHub code-scanning |
| SAST | Bandit | — | Python-native |
| Dep CVE | pip-audit | — | PyPI-backed advisory database |
