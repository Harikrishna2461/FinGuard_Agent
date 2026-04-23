"""
API routes for FinGuard Agent  –  microservices edition.

Responsibilities of this service (backend):
  • REST API for portfolios, transactions, alerts, cases, audit, SAR
  • ML hybrid risk scoring (rules + GradientBoosting + IsolationForest)
  • Guardrail enforcement (regex + LLM-based) before forwarding to agents
  • Delegates all CrewAI agent work to the agent-service over HTTP
  • Proxies agent-service SSE streams back to the browser

The backend no longer imports the orchestrator or any CrewAI code.
"""

from flask import Blueprint, request, jsonify, Response, stream_with_context, current_app
from app import db
from models.models import Portfolio, Asset, Transaction, Alert, RiskAssessment
from agents.guardrails import sanitize, PromptInjectionDetected
from agents.guardrails_llm import sanitize_with_llm
from app.symbols import get_all_symbols, get_symbols_by_sector, DEFAULT_SYMBOLS
from datetime import datetime
import uuid
import logging
import threading
import requests as http_requests   # renamed to avoid shadowing flask request

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)

# Lazy-initialised ML risk engine
_risk_engine = None


# ── Agent-service helpers ─────────────────────────────────────────────────────

def _agent_url() -> str:
    """Return the configured agent-service base URL."""
    return current_app.config.get("AGENT_SERVICE_URL", "http://localhost:5002")


def _fire_agent(endpoint: str, stream_id: str, payload: dict) -> None:
    """POST job to agent-service synchronously (fast — agent-service returns 202 immediately)."""
    try:
        http_requests.post(
            f"{_agent_url()}/{endpoint.lstrip('/')}",
            json={"stream_id": stream_id, **payload},
            timeout=8,
        )
    except Exception as exc:
        logger.warning("agent-service unreachable (%s): %s", endpoint, exc)


def _proxy_agent_stream(stream_id: str) -> Response:
    """Proxy the agent-service SSE stream for stream_id to the browser."""
    agent_svc = _agent_url()

    def generate():
        try:
            with http_requests.get(
                f"{agent_svc}/stream/{stream_id}",
                stream=True,
                timeout=600,
            ) as r:
                for chunk in r.iter_content(chunk_size=None):
                    if chunk:
                        yield chunk.decode("utf-8")
        except Exception as exc:
            import json
            yield f'data: {json.dumps({"type":"error","data":{"message":str(exc)}})}\n\n'
            yield 'data: {"type":"done"}\n\n'

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":        "keep-alive",
        },
    )


def _get_risk_engine():
    """Lazy-load the hybrid ML risk scoring engine."""
    global _risk_engine
    if _risk_engine is None:
        try:
            from ml.risk_scoring_engine import TransactionRiskEngine
            _risk_engine = TransactionRiskEngine()
            if _risk_engine.ml.loaded:
                logger.info("API: Hybrid ML risk engine loaded (ML + Rules)")
            else:
                logger.warning("API: Risk engine loaded in degraded mode (Rules only - ML models unavailable)")
        except Exception as e:
            logger.error("API: Failed to initialize risk engine: %s", e, exc_info=True)
            _risk_engine = None
    return _risk_engine


# ============= Symbol Routes =============

@api_bp.route("/symbols", methods=["GET"])
def get_symbols():
    """Get all available stock symbols."""
    try:
        return jsonify({
            "symbols": get_all_symbols(),
            "default_symbols": DEFAULT_SYMBOLS
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/symbols/sectors", methods=["GET"])
def get_symbols_sectors():
    """Get symbols grouped by sector."""
    try:
        return jsonify({
            "sectors": get_symbols_by_sector()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ============= Portfolio Routes =============

@api_bp.route("/portfolio", methods=["POST"])
def create_portfolio():
    try:
        data = request.json
        user_id = data.get("user_id", str(uuid.uuid4()))
        portfolio = Portfolio(
            user_id=user_id,
            name=data.get("name", "My Portfolio"),
            total_value=data.get("initial_investment", 0),
            cash_balance=data.get("initial_investment", 0),
        )
        db.session.add(portfolio)
        db.session.commit()
        return jsonify({
            "id": portfolio.id,
            "user_id": portfolio.user_id,
            "name": portfolio.name,
            "created_at": portfolio.created_at.isoformat(),
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@api_bp.route("/portfolios", methods=["GET"])
def list_portfolios():
    """List all portfolios."""
    try:
        portfolios = Portfolio.query.order_by(Portfolio.created_at.desc()).all()
        return jsonify({
            "portfolios": [
                {
                    "id": p.id,
                    "user_id": p.user_id,
                    "name": p.name,
                    "total_value": p.total_value,
                    "cash_balance": p.cash_balance,
                    "created_at": p.created_at.isoformat(),
                    "updated_at": p.updated_at.isoformat(),
                }
                for p in portfolios
            ]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/portfolio/<int:portfolio_id>", methods=["GET"])
def get_portfolio(portfolio_id):
    try:
        portfolio = Portfolio.query.get(portfolio_id)
        if not portfolio:
            return jsonify({"error": "Portfolio not found"}), 404
        assets = Asset.query.filter_by(portfolio_id=portfolio_id).all()
        return jsonify({
            "id": portfolio.id,
            "user_id": portfolio.user_id,
            "name": portfolio.name,
            "total_value": portfolio.total_value,
            "cash_balance": portfolio.cash_balance,
            "assets_count": len(assets),
            "created_at": portfolio.created_at.isoformat(),
            "updated_at": portfolio.updated_at.isoformat(),
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/portfolio/<int:portfolio_id>/analyze", methods=["POST"])
def analyze_portfolio(portfolio_id):
    """Delegate full 9-agent analysis to agent-service; return stream_id."""
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        return jsonify({"error": "Portfolio not found"}), 404

    assets       = Asset.query.filter_by(portfolio_id=portfolio_id).all()
    transactions = Transaction.query.filter_by(portfolio_id=portfolio_id).all()

    portfolio_data = {
        "id": portfolio.id, "name": portfolio.name,
        "total_value": portfolio.total_value, "cash_balance": portfolio.cash_balance,
        "assets": [
            {"symbol": a.symbol, "name": a.name, "quantity": a.quantity,
             "current_price": a.current_price, "purchase_price": a.purchase_price,
             "asset_type": a.asset_type}
            for a in assets
        ],
    }
    transactions_list = [
        {"symbol": t.symbol, "type": t.transaction_type, "quantity": t.quantity,
         "price": t.price, "timestamp": t.timestamp.isoformat()}
        for t in transactions[:50]
    ]

    stream_id = str(uuid.uuid4())
    _fire_agent("analyze", stream_id, {
        "portfolio_data": portfolio_data,
        "transactions":   transactions_list,
    })
    return jsonify({"stream_id": stream_id}), 202


@api_bp.route("/portfolio/<int:portfolio_id>/analyze/stream/<stream_id>", methods=["GET"])
def analyze_portfolio_stream(portfolio_id, stream_id):
    return _proxy_agent_stream(stream_id)


@api_bp.route("/portfolio/<int:portfolio_id>/quick-recommendation", methods=["POST"])
def quick_recommendation(portfolio_id):
    """Delegate lightweight recommendation to agent-service."""
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        return jsonify({"error": "Portfolio not found"}), 404

    assets       = Asset.query.filter_by(portfolio_id=portfolio_id).all()
    transactions = Transaction.query.filter_by(portfolio_id=portfolio_id).all()

    portfolio_data = {
        "id": portfolio.id, "name": portfolio.name,
        "total_value": portfolio.total_value, "cash_balance": portfolio.cash_balance,
        "assets": [{"symbol": a.symbol, "name": a.name, "quantity": a.quantity,
                    "current_price": a.current_price, "purchase_price": a.purchase_price,
                    "asset_type": a.asset_type} for a in assets],
    }
    transactions_list = [
        {"symbol": t.symbol, "type": t.transaction_type, "quantity": t.quantity,
         "price": t.price, "timestamp": t.timestamp.isoformat()}
        for t in transactions[:50]
    ]

    stream_id = str(uuid.uuid4())
    _fire_agent("quick-recommendation", stream_id, {
        "portfolio_data": portfolio_data,
        "transactions":   transactions_list,
    })
    return jsonify({"stream_id": stream_id}), 202


@api_bp.route("/portfolio/<int:portfolio_id>/quick-recommendation/stream/<stream_id>", methods=["GET"])
def quick_recommendation_stream(portfolio_id, stream_id):
    return _proxy_agent_stream(stream_id)


# ============= Asset Routes =============

@api_bp.route("/portfolio/<int:portfolio_id>/asset", methods=["POST"])
def add_asset(portfolio_id):
    try:
        portfolio = Portfolio.query.get(portfolio_id)
        if not portfolio:
            return jsonify({"error": "Portfolio not found"}), 404
        data = request.json
        asset = Asset(
            portfolio_id=portfolio_id,
            symbol=data.get("symbol", "").upper(),
            name=data.get("name", ""),
            quantity=data.get("quantity", 0),
            purchase_price=data.get("purchase_price", 0),
            current_price=data.get("current_price", data.get("purchase_price", 0)),
            asset_type=data.get("asset_type", "stock"),
            sector=data.get("sector"),
        )
        db.session.add(asset)
        db.session.commit()
        return jsonify({
            "id": asset.id,
            "symbol": asset.symbol,
            "quantity": asset.quantity,
            "created_at": asset.created_at.isoformat(),
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@api_bp.route("/portfolio/<int:portfolio_id>/assets", methods=["GET"])
def get_assets(portfolio_id):
    try:
        portfolio = Portfolio.query.get(portfolio_id)
        if not portfolio:
            return jsonify({"error": "Portfolio not found"}), 404
        assets = Asset.query.filter_by(portfolio_id=portfolio_id).all()
        return jsonify({
            "assets": [
                {
                    "id": a.id,
                    "symbol": a.symbol,
                    "name": a.name,
                    "quantity": a.quantity,
                    "purchase_price": a.purchase_price,
                    "current_price": a.current_price,
                    "current_value": a.quantity * a.current_price,
                    "gain_loss": (a.current_price - a.purchase_price) * a.quantity,
                    "return_percent": (
                        ((a.current_price - a.purchase_price) / a.purchase_price * 100)
                        if a.purchase_price
                        else 0
                    ),
                    "asset_type": a.asset_type,
                    "sector": a.sector,
                }
                for a in assets
            ]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ============= Transaction Routes =============

@api_bp.route("/portfolio/<int:portfolio_id>/transaction", methods=["POST"])
def add_transaction(portfolio_id):
    try:
        portfolio = Portfolio.query.get(portfolio_id)
        if not portfolio:
            return jsonify({"error": "Portfolio not found"}), 404
        data = request.json
        total_amount = data.get("quantity", 0) * data.get("price", 0)
        fees = data.get("fees", 0)
        transaction = Transaction(
            portfolio_id=portfolio_id,
            symbol=data.get("symbol", "").upper(),
            transaction_type=data.get("type", "buy"),
            quantity=data.get("quantity"),
            price=data.get("price"),
            total_amount=total_amount,
            fees=fees,
            notes=data.get("notes"),
        )
        if data.get("type") == "buy":
            portfolio.cash_balance -= total_amount + fees
        else:
            portfolio.cash_balance += total_amount - fees
        portfolio.updated_at = datetime.utcnow()
        db.session.add(transaction)
        db.session.commit()

        # ── ML Risk Scoring ──────────────────────────────────────
        risk_info = None
        engine = _get_risk_engine()
        if engine is not None:
            try:
                # Build feature dict from available data
                txn_features = {
                    "amount":               total_amount,
                    "transaction_type":      data.get("type", "buy"),
                    "asset_type":            data.get("asset_type", "stock"),
                    "sector":               data.get("sector", "Unknown"),
                    "sender_country":        data.get("sender_country", "US"),
                    "receiver_country":      data.get("receiver_country", "US"),
                    "currency":             data.get("currency", "USD"),
                    "channel":              data.get("channel", "web"),
                    "device_type":          data.get("device_type", "desktop"),
                    "is_new_payee":         data.get("is_new_payee", 0),
                    "account_age_days":     data.get("account_age_days", 365),
                    "customer_avg_txn_amount": data.get("customer_avg_txn_amount", total_amount),
                    "customer_txn_count_30d":  data.get("customer_txn_count_30d", 1),
                    "amount_deviation_from_avg": data.get("amount_deviation_from_avg", 0),
                    "time_of_day_hour":     datetime.utcnow().hour,
                    "is_weekend":           int(datetime.utcnow().weekday() >= 5),
                    "ip_country_match":     data.get("ip_country_match", 1),
                    "failed_login_attempts_24h": data.get("failed_login_attempts_24h", 0),
                    "num_txns_last_1h":     data.get("num_txns_last_1h", 0),
                    "num_txns_last_24h":    data.get("num_txns_last_24h", 0),
                    "days_since_last_txn":  data.get("days_since_last_txn", 1),
                    "receiver_account_age_days": data.get("receiver_account_age_days", 365),
                    "is_high_risk_country": data.get("is_high_risk_country", 0),
                    "is_sanctioned_country": data.get("is_sanctioned_country", 0),
                    "pep_flag":             data.get("pep_flag", 0),
                    "portfolio_concentration_pct": data.get("portfolio_concentration_pct", 10),
                    "market_volatility_index": data.get("market_volatility_index", 20),
                }
                result = engine.score(txn_features)
                risk_info = {
                    "risk_score":  result["final_score"],
                    "risk_label":  result["risk_label"],
                    "method":      result["method"],
                    "hard_block":  result["hard_block"],
                    "flags":       result["flags"],
                    "needs_llm_review": result.get("needs_llm_review"),
                    "rule_details": {
                        "rule_score": result["rule_details"]["rule_score"],
                        "flags":      result["rule_details"]["flags"],
                        "details":    result["rule_details"]["details"],
                    },
                    "ml_details": {
                        "ml_risk_score":    result["ml_details"].get("ml_risk_score"),
                        "ml_risk_label":    result["ml_details"].get("ml_risk_label"),
                        "ml_fraud_flag":    result["ml_details"].get("ml_fraud_flag"),
                        "ml_anomaly_score": result["ml_details"].get("ml_anomaly_score"),
                        "ml_confidence":    result["ml_details"].get("ml_confidence"),
                        "available":        result["ml_details"].get("available"),
                        "reason":           result["ml_details"].get("reason"),
                    },
                }
                # Auto-create alert for high/critical risk
                auto_alert = None
                if result["final_score"] >= 55:
                    auto_alert = Alert(
                        portfolio_id=portfolio_id,
                        alert_type="ml_risk_detection",
                        symbol=data.get("symbol", "").upper(),
                        message=(
                            f"ML Risk Alert: Transaction #{transaction.id} scored "
                            f"{result['final_score']}/100 ({result['risk_label']}). "
                            f"Flags: {', '.join(result['flags']) or 'none'}"
                        ),
                    )
                    db.session.add(auto_alert)
                    db.session.commit()

                    # Auto-open an investigation case (tenant-scoped).
                    try:
                        from app.cases import open_case_for_transaction
                        from app.auth import current_tenant_id
                        from models.models import Tenant, DEFAULT_TENANT_SLUG
                        tid = current_tenant_id()
                        if tid is None:
                            default = Tenant.query.filter_by(slug=DEFAULT_TENANT_SLUG).first()
                            tid = default.id if default else None
                        if tid is not None:
                            case = open_case_for_transaction(
                                tenant_id=tid,
                                transaction=transaction,
                                portfolio=portfolio,
                                risk_score=int(result["final_score"]),
                                flags=list(result.get("flags") or []),
                                alert=auto_alert,
                            )
                            if case is not None:
                                db.session.commit()
                                risk_info["case_id"] = case.id
                    except Exception as ce:
                        db.session.rollback()
                        logger.warning("Case auto-open failed for txn %s: %s", transaction.id, ce)
            except Exception as e:
                logger.warning("ML scoring failed for txn %s: %s", transaction.id, e)

        response = {
            "id": transaction.id,
            "symbol": transaction.symbol,
            "type": transaction.transaction_type,
            "amount": total_amount,
            "timestamp": transaction.timestamp.isoformat(),
        }
        if risk_info:
            response["risk"] = risk_info
        return jsonify(response), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@api_bp.route("/portfolio/<int:portfolio_id>/transactions", methods=["GET"])
def get_transactions(portfolio_id):
    try:
        portfolio = Portfolio.query.get(portfolio_id)
        if not portfolio:
            return jsonify({"error": "Portfolio not found"}), 404
        transactions = (
            Transaction.query.filter_by(portfolio_id=portfolio_id)
            .order_by(Transaction.timestamp.desc())
            .limit(100)
            .all()
        )
        return jsonify({
            "transactions": [
                {
                    "id": t.id,
                    "symbol": t.symbol,
                    "type": t.transaction_type,
                    "quantity": t.quantity,
                    "price": t.price,
                    "total_amount": t.total_amount,
                    "fees": t.fees,
                    "timestamp": t.timestamp.isoformat(),
                    "notes": t.notes,
                }
                for t in transactions
            ]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ============= Transaction Risk Scoring (standalone) =============

@api_bp.route("/transaction/score-risk", methods=["POST"])
def score_transaction_risk():
    """
    Score a transaction's risk using the hybrid ML pipeline.
    Falls back to rules-based scoring if ML models are unavailable.
    Does NOT persist the transaction — use this for pre-screening.

    Expects JSON body with transaction features (amount, type, country, etc.).
    Returns risk score, label, flags, and ML details (empty if ML unavailable).
    """
    try:
        data = request.json or {}
        if not data.get("amount"):
            return jsonify({"error": "amount is required"}), 400

        engine = _get_risk_engine()
        if engine is None:
            return jsonify({"error": "Risk engine initialization failed"}), 503

        result = engine.score(data)
        return jsonify({
            "risk_score":      result["final_score"],
            "risk_label":      result["risk_label"],
            "method":          result["method"],
            "hard_block":      result["hard_block"],
            "flags":           result["flags"],
            "needs_llm_review": result["needs_llm_review"],
            "rule_details": {
                "rule_score": result["rule_details"]["rule_score"],
                "flags":      result["rule_details"]["flags"],
                "details":    result["rule_details"]["details"],
            },
            "ml_details": {
                "ml_risk_score":    result["ml_details"].get("ml_risk_score"),
                "ml_risk_label":    result["ml_details"].get("ml_risk_label"),
                "ml_fraud_flag":    result["ml_details"].get("ml_fraud_flag"),
                "ml_anomaly_score": result["ml_details"].get("ml_anomaly_score"),
                "ml_confidence":    result["ml_details"].get("ml_confidence"),
                "available":        result["ml_details"].get("available"),
                "reason":           result["ml_details"].get("reason"),
            },
            "timestamp": result["timestamp"],
        }), 200
    except Exception as e:
        logger.error("Score transaction risk error: %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 400


@api_bp.route("/transaction/get-ai-insights", methods=["POST"])
def get_transaction_ai_insights():
    """
    Guardrail check (backend) → delegate explanation to agent-service.
    Returns stream_id immediately; events arrive via SSE proxy.
    """
    data        = request.json or {}
    transaction = data.get("transaction", {})
    score       = data.get("score", 50)
    factors     = data.get("factors", {})

    if not transaction:
        return jsonify({"error": "transaction required"}), 400

    stream_id = str(uuid.uuid4())

    # Guardrail lives at the gateway — check before involving agents
    txn_input = str(transaction.get("description", ""))
    if txn_input:
        try:
            guard = sanitize_with_llm(txn_input)
            if not guard.ok:
                # Return a synthetic blocked SSE stream without calling agent-service
                from app.agent_stream import create_stream, emit, close_stream
                create_stream(stream_id)

                def _emit_block():
                    from app.agent_stream import emit as _e, close_stream as _c
                    _e(stream_id, "crew_start",    {"crew": 1, "name": "Guardrail Check", "agents": ["Guardrail LLM"]})
                    _e(stream_id, "agent_thinking",{"agent": "Guardrail LLM", "crew": 1,
                                                    "thought": f"Checking: {txn_input}"})
                    _e(stream_id, "crew_done",     {"crew": 1, "name": "Guardrail Check", "output": f"BLOCKED: {guard.reason}"})
                    _e(stream_id, "result", {
                        "insights": f"Input blocked by security guardrail: {guard.reason}",
                        "agent": "Guardrail LLM", "success": False,
                        "blocked": True, "reason": guard.reason,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    _c(stream_id)

                threading.Thread(target=_emit_block, daemon=True).start()
                return jsonify({"stream_id": stream_id}), 202
        except Exception:
            pass  # if guardrail itself fails, let agent-service handle it

    _fire_agent("insights", stream_id, {
        "transaction": transaction,
        "score":       score,
        "factors":     factors,
    })
    return jsonify({"stream_id": stream_id}), 202


@api_bp.route("/transaction/insights/stream/<stream_id>", methods=["GET"])
def transaction_insights_stream(stream_id):
    # If a local (blocked) stream exists, serve it; otherwise proxy agent-service
    from app.agent_stream import _queues
    if stream_id in _queues:
        from app.agent_stream import sse_generator as local_sse
        return Response(stream_with_context(local_sse(stream_id)), mimetype="text/event-stream",
                        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no","Connection":"keep-alive"})
    return _proxy_agent_stream(stream_id)


# ============= Alert Routes =============

@api_bp.route("/portfolio/<int:portfolio_id>/alert", methods=["POST"])
def create_alert(portfolio_id):
    try:
        portfolio = Portfolio.query.get(portfolio_id)
        if not portfolio:
            return jsonify({"error": "Portfolio not found"}), 404
        data = request.json
        alert = Alert(
            portfolio_id=portfolio_id,
            alert_type=data.get("alert_type"),
            symbol=data.get("symbol"),
            target_price=data.get("target_price"),
            threshold=data.get("threshold"),
            message=data.get("message"),
        )
        db.session.add(alert)
        db.session.commit()
        return jsonify({
            "id": alert.id,
            "alert_type": alert.alert_type,
            "is_active": alert.is_active,
            "created_at": alert.created_at.isoformat(),
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@api_bp.route("/portfolio/<int:portfolio_id>/alerts", methods=["GET"])
def get_alerts(portfolio_id):
    try:
        portfolio = Portfolio.query.get(portfolio_id)
        if not portfolio:
            return jsonify({"error": "Portfolio not found"}), 404
        alerts = Alert.query.filter_by(portfolio_id=portfolio_id).all()
        return jsonify({
            "alerts": [
                {
                    "id": a.id,
                    "type": a.alert_type,
                    "symbol": a.symbol,
                    "target_price": a.target_price,
                    "threshold": a.threshold,
                    "is_active": a.is_active,
                    "triggered": a.triggered,
                    "message": a.message,
                    "created_at": a.created_at.isoformat(),
                }
                for a in alerts
            ]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ============= Analysis Routes (single-agent, quick) =============

@api_bp.route("/portfolio/<int:portfolio_id>/recommendation", methods=["POST"])
def get_recommendation(portfolio_id):
    """Delegate per-symbol recommendation to agent-service."""
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        return jsonify({"error": "Portfolio not found"}), 404
    data   = request.json or {}
    symbol = (data.get("symbol") or "").upper()
    if not symbol:
        return jsonify({"error": "Symbol required"}), 400

    stream_id = str(uuid.uuid4())
    _fire_agent("recommendation", stream_id, {
        "symbol":         symbol,
        "portfolio_size": portfolio.total_value,
        "risk_profile":   data.get("risk_profile", "moderate"),
    })
    return jsonify({"stream_id": stream_id}), 202


@api_bp.route("/portfolio/<int:portfolio_id>/recommendation/stream/<stream_id>", methods=["GET"])
def recommendation_stream(portfolio_id, stream_id):
    return _proxy_agent_stream(stream_id)


@api_bp.route("/sentiment/analyze", methods=["POST"])
def analyze_sentiment():
    """Start market sentiment analysis — returns stream_id for SSE proxy."""
    data    = request.json or {}
    symbols = [s.strip().upper() for s in data.get("symbols", []) if s.strip()]
    if not symbols:
        return jsonify({"error": "symbols required"}), 400
    if len(symbols) > 10:
        symbols = symbols[:10]

    stream_id = str(uuid.uuid4())
    _fire_agent("sentiment", stream_id, {"symbols": symbols})
    return jsonify({"stream_id": stream_id}), 202


@api_bp.route("/sentiment/stream/<stream_id>", methods=["GET"])
def sentiment_stream(stream_id):
    return _proxy_agent_stream(stream_id)


# ============= Vector search endpoints =============

def _guardrail_check(query: str):
    """Run LLM guardrail; return (cleaned_query, None) or (None, error_response)."""
    try:
        guard = sanitize_with_llm(query)
        if not guard.ok:
            return None, jsonify({"error": f"Query blocked: {guard.reason}"}), 400
        return guard.cleaned, None, None
    except Exception:
        return query, None, None


@api_bp.route("/search/analyses", methods=["POST"])
def search_analyses():
    data  = request.json or {}
    query = data.get("query", "")
    pid   = data.get("portfolio_id")
    if not query:
        return jsonify({"error": "query required"}), 400

    cleaned, err, code = _guardrail_check(query)
    if err:
        return err, code

    stream_id = str(uuid.uuid4())
    _fire_agent("search/analyses", stream_id, {"query": cleaned, "portfolio_id": pid})
    return jsonify({"stream_id": stream_id}), 202


@api_bp.route("/search/analyses/stream/<stream_id>", methods=["GET"])
def search_analyses_stream(stream_id):
    return _proxy_agent_stream(stream_id)


@api_bp.route("/search/risks", methods=["POST"])
def search_risks():
    data  = request.json or {}
    query = data.get("query", "")
    pid   = data.get("portfolio_id")
    if not query:
        return jsonify({"error": "query required"}), 400

    cleaned, err, code = _guardrail_check(query)
    if err:
        return err, code

    stream_id = str(uuid.uuid4())
    _fire_agent("search/risks", stream_id, {"query": cleaned, "portfolio_id": pid})
    return jsonify({"stream_id": stream_id}), 202


@api_bp.route("/search/risks/stream/<stream_id>", methods=["GET"])
def search_risks_stream(stream_id):
    return _proxy_agent_stream(stream_id)


@api_bp.route("/search/market", methods=["POST"])
def search_market():
    data   = request.json or {}
    query  = data.get("query", "")
    symbol = data.get("symbol")
    if not query:
        return jsonify({"error": "query required"}), 400

    cleaned, err, code = _guardrail_check(query)
    if err:
        return err, code

    stream_id = str(uuid.uuid4())
    _fire_agent("search/market", stream_id, {"query": cleaned, "symbol": symbol})
    return jsonify({"stream_id": stream_id}), 202


@api_bp.route("/search/market/stream/<stream_id>", methods=["GET"])
def search_market_stream(stream_id):
    return _proxy_agent_stream(stream_id)


# ============= Agent Reasoning Demo =============

@api_bp.route("/agent/demo", methods=["POST"])
def agent_reasoning_demo():
    """Demo endpoint that shows agent reasoning flow."""
    import uuid
    import time
    from app.agent_reasoning import create_flow, complete_flow, AgentStep

    flow_id = str(uuid.uuid4())
    flow_name = "Portfolio Risk Analysis Crew"

    flow = create_flow(flow_id, flow_name)

    # Simulate agent steps
    start_time = time.time()

    # Step 1: Risk Assessment Agent
    step1_start = time.time()
    flow.add_step(AgentStep(
        agent_name="Risk Assessment Agent",
        step_number=1,
        input_data={
            "portfolio_id": "PORT_001",
            "transactions": [
                {"id": "TXN_1", "amount": 10000, "receiver_country": "IR"},
                {"id": "TXN_2", "amount": 5000, "receiver_country": "US"}
            ]
        },
        reasoning="Analyzing transactions for AML compliance. Found one transaction to Iran (sanctioned country) with amount $10k. This triggers SANCTIONED_COUNTRY flag and increases risk score significantly.",
        output_data={
            "risk_score": 85,
            "flags": ["SANCTIONED_COUNTRY", "LARGE_TXN"],
            "compliance_status": "CRITICAL"
        },
        duration_ms=(time.time() - step1_start) * 1000
    ))

    # Step 2: Portfolio Analysis Agent
    step2_start = time.time()
    flow.add_step(AgentStep(
        agent_name="Portfolio Analysis Agent",
        step_number=2,
        input_data={
            "risk_score": 85,
            "flags": ["SANCTIONED_COUNTRY", "LARGE_TXN"],
            "portfolio_composition": {"stocks": 60, "bonds": 30, "cash": 10}
        },
        reasoning="Receiving risk assessment from Risk Agent. Evaluating portfolio diversification and allocation. High risk score indicates need for immediate escalation. Current allocation shows moderate diversification but overall portfolio at elevated risk due to flagged transactions.",
        output_data={
            "portfolio_risk_level": "CRITICAL",
            "diversification_score": 65,
            "recommendation": "immediate_review"
        },
        duration_ms=(time.time() - step2_start) * 1000
    ))

    # Step 3: Escalation Agent
    step3_start = time.time()
    flow.add_step(AgentStep(
        agent_name="Escalation & Summary Agent",
        step_number=3,
        input_data={
            "portfolio_risk_level": "CRITICAL",
            "recommendation": "immediate_review",
            "risk_score": 85
        },
        reasoning="Summarizing findings from Risk and Portfolio agents. Portfolio shows critical risk level primarily due to transaction to sanctioned country. Preparing escalation summary for manual review and potential hard block.",
        output_data={
            "escalation_level": "URGENT",
            "action_required": "IMMEDIATE_BLOCK",
            "assigned_to": "Compliance_Officer_1",
            "summary": "Transaction to Iran flagged as critical risk. Recommended hard block pending manual review."
        },
        duration_ms=(time.time() - step3_start) * 1000
    ))

    total_duration = (time.time() - start_time) * 1000
    complete_flow(flow_id, total_duration, "completed")

    return jsonify({
        "flow_id": flow_id,
        "flow_name": flow_name,
        "status": "completed",
        "message": "Demo agent flow created successfully",
        "total_duration_ms": total_duration,
        "steps": len(flow.steps)
    }), 200


# ============= Health =============

@api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}), 200
