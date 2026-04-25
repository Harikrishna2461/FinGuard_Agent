"""
agent-service  –  Standalone Flask microservice wrapping all CrewAI agents.

Endpoints (all internal — called by backend-service only):
  POST /analyze                  full 9-agent portfolio review
  POST /quick-recommendation     lightweight portfolio recommendation
  POST /recommendation           per-symbol investment recommendation
  POST /sentiment                market sentiment for symbols
  POST /insights                 guardrail + explanation for a transaction
  POST /search/analyses          semantic search over portfolio analyses
  POST /search/risks             semantic search over risk assessments
  POST /search/market            semantic search over market intelligence
  GET  /stream/<stream_id>       SSE stream for any of the above jobs
  GET  /health                   liveness probe
"""

import os
import sys
import logging
import threading
import uuid
from pathlib import Path

from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv

# ── resolve paths ─────────────────────────────────────────────────────────────
SERVICE_DIR = Path(__file__).resolve().parent   # agent-service/
# Agents + ML + vector_store live in the sibling backend/ directory
# (mounted as /app/agents, /app/ml, /app/vector_store.py in Docker;
#  in dev mode we just add backend/ to the path directly)
BACKEND_DIR = SERVICE_DIR.parent / "backend"
if BACKEND_DIR.exists():
    sys.path.insert(0, str(BACKEND_DIR))

load_dotenv(BACKEND_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [agent-svc] %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

from agent_stream import create_stream, close_stream, emit, sse_generator  # noqa: E402

app = Flask(__name__)
CORS(app)

# ── Lazy singletons ───────────────────────────────────────────────────────────
_orchestrator = None
_orch_lock = threading.Lock()


def _get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        with _orch_lock:
            if _orchestrator is None:
                from agents.crew_orchestrator import AIAgentOrchestrator
                _orchestrator = AIAgentOrchestrator()
                logger.info("Orchestrator initialised")
    return _orchestrator


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_in_bg(fn, stream_id, *args, **kwargs):
    """Run fn in a daemon thread; emit error + close stream on exception."""
    def _wrap():
        try:
            fn(stream_id, *args, **kwargs)
        except Exception as exc:
            logger.exception("Agent job failed: %s", exc)
            emit(stream_id, "error", {"message": str(exc)})
        finally:
            close_stream(stream_id)

    threading.Thread(target=_wrap, daemon=True).start()


# ── Agent job functions ───────────────────────────────────────────────────────

def _job_analyze(stream_id, portfolio_data, transactions):
    orch = _get_orchestrator()
    result = orch.comprehensive_portfolio_review(
        portfolio_data, transactions, stream_id=stream_id, emit_fn=emit)
    emit(stream_id, "result", result)


def _job_quick_recommendation(stream_id, portfolio_data, transactions):
    orch = _get_orchestrator()
    result = orch.quick_portfolio_recommendation(
        portfolio_data, transactions, stream_id=stream_id, emit_fn=emit)
    emit(stream_id, "result", result)


def _job_recommendation(stream_id, symbol, portfolio_size, risk_profile):
    orch = _get_orchestrator()
    result = orch.quick_recommendation(
        symbol, portfolio_size, risk_profile, stream_id=stream_id, emit_fn=emit)
    emit(stream_id, "result", result)


def _job_sentiment(stream_id, symbols):
    orch = _get_orchestrator()
    result = orch.quick_market_sentiment(symbols, stream_id=stream_id, emit_fn=emit)
    emit(stream_id, "result", result)


def _job_insights(stream_id, transaction, score, factors, cleaned_input):
    """Explanation agent job (guardrail already cleared by backend)."""
    orch = _get_orchestrator()
    emit(stream_id, "crew_start", {"crew": 2, "name": "Risk Explanation", "agents": ["Explanation Agent"]})
    emit(stream_id, "agent_thinking", {
        "agent": "Explanation Agent", "crew": 2,
        "thought": (
            f"Generating explanation for risk score {score}/100\n\n"
            f"Transaction: {transaction}\n\n"
            f"Risk factors:\n"
            + "".join(f"  - {k}: {v}\n" for k, v in (factors or {}).items())
            + "\nFormulating human-readable analysis with actionable recommendations..."
        ),
    })
    try:
        result = orch.explanation_agent.explain_risk_score(
            transaction=transaction,
            score=score,
            factors=factors or {},
        )
        text = result.get("explanation", str(result))
        emit(stream_id, "crew_done", {"crew": 2, "name": "Risk Explanation", "output": text[:300]})
        emit(stream_id, "result", {"insights": text, "agent": "Explanation", "success": True})
    except Exception as exc:
        emit(stream_id, "crew_done", {"crew": 2, "name": "Risk Explanation", "output": f"Error: {exc}"})
        emit(stream_id, "result", {"insights": f"AI analysis error: {exc}", "success": False})


def _job_search(stream_id, search_type, query, portfolio_id, symbol=None):
    """Vector search job (guardrail already cleared by backend; cleaned query passed)."""
    import vector_store as vs
    orch = _get_orchestrator()

    label_map = {
        "analyses": "Portfolio Analysis Search",
        "risks":    "Risk Assessment Search",
        "market":   "Market Intelligence Search",
    }
    label = label_map.get(search_type, "Search")

    extra_ctx = f"Portfolio: {portfolio_id}" if portfolio_id else (f"Symbol: {symbol}" if symbol else "")
    emit(stream_id, "crew_start", {"crew": 2, "name": label, "agents": ["Vector Search Agent"]})
    emit(stream_id, "agent_thinking", {
        "agent": "Vector Search Agent", "crew": 2,
        "thought": (
            f"Querying ChromaDB for {search_type}:\n"
            f"Query: {query}\n{extra_ctx}\n\n"
            "Computing embeddings and retrieving nearest neighbours..."
        ),
    })

    try:
        if search_type == "analyses":
            results = orch.search_past_analyses(query, portfolio_id)
        elif search_type == "risks":
            results = orch.search_past_risks(query, portfolio_id)
        else:
            results = orch.search_past_market(query, symbol)
    except Exception:
        # Fallback to direct vector_store calls
        if search_type == "analyses":
            raw = vs.search_portfolio(query, portfolio_id=portfolio_id)
        elif search_type == "risks":
            raw = vs.search_risk(query, portfolio_id=portfolio_id)
        else:
            raw = vs.search_market(query)
        results = [r.get("document", r) for r in raw]

    emit(stream_id, "crew_done", {"crew": 2, "name": label, "output": f"Found {len(results)} result(s)"})
    emit(stream_id, "result", {"results": results})


# ── HTTP endpoints ────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    return {"status": "healthy", "service": "agent-service"}, 200


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json or {}
    stream_id = data.get("stream_id") or str(uuid.uuid4())
    create_stream(stream_id)
    _run_in_bg(_job_analyze, stream_id,
               data.get("portfolio_data", {}),
               data.get("transactions", []))
    return jsonify({"stream_id": stream_id}), 202


@app.route("/quick-recommendation", methods=["POST"])
def quick_recommendation():
    data = request.json or {}
    stream_id = data.get("stream_id") or str(uuid.uuid4())
    create_stream(stream_id)
    _run_in_bg(_job_quick_recommendation, stream_id,
               data.get("portfolio_data", {}),
               data.get("transactions", []))
    return jsonify({"stream_id": stream_id}), 202


@app.route("/recommendation", methods=["POST"])
def recommendation():
    data = request.json or {}
    stream_id = data.get("stream_id") or str(uuid.uuid4())
    create_stream(stream_id)
    _run_in_bg(_job_recommendation, stream_id,
               data.get("symbol", ""),
               data.get("portfolio_size", 0),
               data.get("risk_profile", "moderate"))
    return jsonify({"stream_id": stream_id}), 202


@app.route("/sentiment", methods=["POST"])
def sentiment():
    data = request.json or {}
    stream_id = data.get("stream_id") or str(uuid.uuid4())
    create_stream(stream_id)
    _run_in_bg(_job_sentiment, stream_id, data.get("symbols", []))
    return jsonify({"stream_id": stream_id}), 202


@app.route("/insights", methods=["POST"])
def insights():
    data = request.json or {}
    stream_id = data.get("stream_id") or str(uuid.uuid4())
    create_stream(stream_id)
    _run_in_bg(_job_insights, stream_id,
               data.get("transaction", {}),
               data.get("score", 0),
               data.get("factors", {}),
               data.get("cleaned_input", ""))
    return jsonify({"stream_id": stream_id}), 202


@app.route("/search/<search_type>", methods=["POST"])
def search(search_type):
    if search_type not in ("analyses", "risks", "market"):
        return jsonify({"error": "unknown search type"}), 400
    data = request.json or {}
    stream_id = data.get("stream_id") or str(uuid.uuid4())
    create_stream(stream_id)
    _run_in_bg(_job_search, stream_id,
               search_type,
               data.get("query", ""),
               data.get("portfolio_id"),
               symbol=data.get("symbol"))
    return jsonify({"stream_id": stream_id}), 202


@app.route("/stream/<stream_id>")
def stream(stream_id):
    return Response(
        stream_with_context(sse_generator(stream_id)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":       "keep-alive",
        },
    )


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("AGENT_SERVICE_PORT", 5002))
    host = "0.0.0.0"

    # On macOS, skip gunicorn (fork() conflicts with Objective-C runtime).
    # Everywhere else, prefer gunicorn (gthread worker) so SSE streams don't block.
    import platform
    import shutil, subprocess  # noqa: E401
    
    use_gunicorn = platform.system() != "Darwin"  # Skip gunicorn on macOS
    gunicorn = None
    
    if use_gunicorn:
        gunicorn = shutil.which("gunicorn")
        if not gunicorn:
            # Also check the sibling .venv used by the project
            _venv = Path(__file__).resolve().parent.parent / ".venv" / "bin" / "gunicorn"
            if _venv.exists():
                gunicorn = str(_venv)

    if gunicorn:
        logger.info("agent-service starting via gunicorn on %s:%d", host, port)
        subprocess.run([
            gunicorn,
            "--worker-class", "gthread",
            "--workers", "1",
            "--threads", "32",         # high thread count: each SSE stream holds a thread
            "--bind", f"{host}:{port}",
            "--timeout", "0",          # disable worker timeout — SSE streams are long-lived
            "--graceful-timeout", "30",
            "--keep-alive", "75",
            "--access-logfile", "-",   # log requests to stdout for debugging
            "--chdir", str(SERVICE_DIR),  # must cd into agent-service/ so app:app resolves
            "app:app",
        ])
    else:
        logger.info("agent-service starting (Flask dev) on port %d", port)
        app.run(host=host, port=port, debug=False, threaded=True)
