"""
API routes for FinGuard Agent.

All routes live under the /api blueprint.
The orchestrator uses CrewAI agents + ChromaDB under the hood.
ML hybrid scoring (Rules + GradientBoosting + IsolationForest) is
applied automatically when transactions are created or scored.
"""

from flask import Blueprint, request, jsonify
from app import db
from models.models import Portfolio, Asset, Transaction, Alert, RiskAssessment
from agents.crew_orchestrator import AIAgentOrchestrator
from agents.guardrails import sanitize, PromptInjectionDetected
from agents.guardrails_llm import sanitize_with_llm
from app.symbols import get_all_symbols, get_symbols_by_sector, DEFAULT_SYMBOLS
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)

# Lazy-initialised orchestrator (created on first request)
_orchestrator = None

# Lazy-initialised ML risk engine
_risk_engine = None


def _get_orchestrator() -> AIAgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AIAgentOrchestrator()
    return _orchestrator


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
    """Run full CrewAI multi-agent analysis."""
    try:
        portfolio = Portfolio.query.get(portfolio_id)
        if not portfolio:
            return jsonify({"error": "Portfolio not found"}), 404

        assets = Asset.query.filter_by(portfolio_id=portfolio_id).all()
        transactions = Transaction.query.filter_by(portfolio_id=portfolio_id).all()

        portfolio_data = {
            "id": portfolio.id,
            "name": portfolio.name,
            "total_value": portfolio.total_value,
            "cash_balance": portfolio.cash_balance,
            "assets": [
                {
                    "symbol": a.symbol,
                    "name": a.name,
                    "quantity": a.quantity,
                    "current_price": a.current_price,
                    "purchase_price": a.purchase_price,
                    "asset_type": a.asset_type,
                }
                for a in assets
            ],
        }
        transactions_list = [
            {
                "symbol": t.symbol,
                "type": t.transaction_type,
                "quantity": t.quantity,
                "price": t.price,
                "timestamp": t.timestamp.isoformat(),
            }
            for t in transactions[:50]
        ]

        orch = _get_orchestrator()
        result = orch.comprehensive_portfolio_review(portfolio_data, transactions_list)

        # Persist to SQL as well
        risk_assessment = RiskAssessment(
            portfolio_id=portfolio_id,
            assessment_data=result,
        )
        db.session.add(risk_assessment)
        db.session.commit()
        return jsonify(result), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Portfolio analysis error: {str(e)}", exc_info=True)
        
        # Provide detailed error response to help diagnosis
        error_response = {
            "error": "Portfolio analysis failed",
            "details": str(e),
            "type": type(e).__name__,
            "help": "Check server logs for more details. Ensure GROQ_API_KEY is set and valid."
        }
        return jsonify(error_response), 400


@api_bp.route("/portfolio/<int:portfolio_id>/quick-recommendation", methods=["POST"])
def quick_recommendation(portfolio_id):
    """Run lightweight single-agent quick recommendation (~1k tokens, always works on free tier)."""
    try:
        portfolio = Portfolio.query.get(portfolio_id)
        if not portfolio:
            return jsonify({"error": "Portfolio not found"}), 404

        assets = Asset.query.filter_by(portfolio_id=portfolio_id).all()
        transactions = Transaction.query.filter_by(portfolio_id=portfolio_id).all()

        portfolio_data = {
            "id": portfolio.id,
            "name": portfolio.name,
            "total_value": portfolio.total_value,
            "cash_balance": portfolio.cash_balance,
            "assets": [
                {
                    "symbol": a.symbol,
                    "name": a.name,
                    "quantity": a.quantity,
                    "current_price": a.current_price,
                    "purchase_price": a.purchase_price,
                    "asset_type": a.asset_type,
                }
                for a in assets
            ],
        }
        transactions_list = [
            {
                "symbol": t.symbol,
                "type": t.transaction_type,
                "quantity": t.quantity,
                "price": t.price,
                "timestamp": t.timestamp.isoformat(),
            }
            for t in transactions[:50]
        ]

        orch = _get_orchestrator()
        result = orch.quick_portfolio_recommendation(portfolio_data, transactions_list)

        return jsonify(result), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Quick recommendation error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Quick recommendation failed",
            "details": str(e),
            "type": type(e).__name__,
        }), 400


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
    Get AI-powered insights for a transaction's risk score.
    Uses ExplanationAgent to generate human-readable analysis.
    
    Expects JSON body with:
    - transaction: dict with transaction details
    - score: int 0-100 risk score
    - factors: dict of contributing factors
    
    Returns: {"insights": str, "agent": "Explanation", "timestamp": str, "success": bool}
    """
    try:
        data = request.json or {}
        transaction = data.get("transaction", {})
        score = data.get("score", 50)
        factors = data.get("factors", {})
        
        if not transaction:
            return jsonify({"error": "transaction required"}), 400

        orch = _get_orchestrator()
        
        # Get ExplanationAgent and generate insights
        try:
            result = orch.explanation_agent.explain_risk_score(
                transaction=transaction,
                score=score,
                factors=factors
            )
            return jsonify({
                "insights": result.get("explanation", ""),
                "agent": "Explanation",
                "timestamp": result.get("timestamp", datetime.utcnow().isoformat()),
                "success": True,
            }), 200
        except RuntimeError as e:
            # LLM error - provide helpful fallback with better formatting
            error_msg = str(e)
            risk_level = "CRITICAL" if score >= 80 else "HIGH" if score >= 55 else "MEDIUM" if score >= 30 else "LOW"
            
            fallback_insights = (
                f"**Risk Assessment Summary**\n"
                f"Risk Score: {score}/100\n"
                f"Risk Level: {risk_level}\n\n"
                f"**Contributing Factors**\n"
            )
            for key, value in factors.items():
                fallback_insights += f"- {key}: {value}\n"
            
            fallback_insights += (
                f"\n**Analysis**\n"
                f"The combination of these factors indicates {risk_level.lower()} risk. "
            )
            
            if score >= 80:
                fallback_insights += (
                    "Immediate action is recommended:\n"
                    "- Review transaction details carefully\n"
                    "- Consider blocking the transaction\n"
                    "- Contact the customer if appropriate"
                )
            elif score >= 55:
                fallback_insights += (
                    "Further investigation recommended:\n"
                    "- Gather additional context\n"
                    "- Monitor for related activity\n"
                    "- Escalate if patterns emerge"
                )
            else:
                fallback_insights += "Continue routine monitoring."
            
            fallback_insights += f"\n\n**Error Details**\n{error_msg}"
            
            return jsonify({
                "insights": fallback_insights,
                "agent": "Explanation",
                "timestamp": datetime.utcnow().isoformat(),
                "success": False,
                "error_reason": error_msg,
            }), 200
            
    except Exception as e:
        logger.error("Get AI insights error: %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 400


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
    try:
        portfolio = Portfolio.query.get(portfolio_id)
        if not portfolio:
            return jsonify({"error": "Portfolio not found"}), 404
        data = request.json
        symbol = (data.get("symbol") or "").upper()
        if not symbol:
            return jsonify({"error": "Symbol required"}), 400
        orch = _get_orchestrator()
        rec = orch.quick_recommendation(
            symbol=symbol,
            portfolio_size=portfolio.total_value,
            risk_profile=data.get("risk_profile", "moderate"),
        )
        return jsonify(rec), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/sentiment", methods=["GET"])
@api_bp.route("/sentiment/<symbol>", methods=["GET"])
def get_sentiment(symbol=None):
    """
    Get sentiment analysis for one or more symbols.
    
    Can be called in two ways:
    1. /sentiment/AAPL - get sentiment for a single symbol
    2. /sentiment?symbols=AAPL,MSFT,GOOGL - get sentiment for multiple symbols
    """
    try:
        orch = _get_orchestrator()
        
        # Get symbols from either path parameter or query parameter
        symbols = []
        if symbol:
            symbols = [symbol.upper()]
        else:
            # Get from query parameter (comma-separated)
            symbols_param = request.args.get("symbols", "")
            if symbols_param:
                symbols = [s.strip().upper() for s in symbols_param.split(",")]
        
        if not symbols:
            return jsonify({"error": "Symbol(s) required. Use /sentiment/AAPL or /sentiment?symbols=AAPL,MSFT"}), 400
        
        # Limit to 10 symbols max
        if len(symbols) > 10:
            symbols = symbols[:10]
        
        sentiment = orch.quick_market_sentiment(symbols)
        return jsonify(sentiment), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ============= Vector search endpoints =============

@api_bp.route("/search/analyses", methods=["POST"])
def search_analyses():
    """Semantic search over past portfolio analyses stored in ChromaDB."""
    data = request.json or {}
    query = data.get("query", "")
    pid = data.get("portfolio_id")
    if not query:
        return jsonify({"error": "query required"}), 400

    # LLM-based guardrail (semantic detection of prompt injection)
    guard = sanitize_with_llm(query)
    if not guard.ok:
        logger.warning(f"search_analyses: guardrail blocked query (reason={guard.reason}, confidence={guard.confidence})")
        return jsonify({"error": f"Query blocked: {guard.reason}", "confidence": guard.confidence}), 400

    orch = _get_orchestrator()
    results = orch.search_past_analyses(guard.cleaned, pid)
    return jsonify({"results": results}), 200


@api_bp.route("/search/risks", methods=["POST"])
def search_risks():
    data = request.json or {}
    query = data.get("query", "")
    if not query:
        return jsonify({"error": "query required"}), 400

    # LLM-based guardrail
    guard = sanitize_with_llm(query)
    if not guard.ok:
        logger.warning(f"search_risks: guardrail blocked query (reason={guard.reason}, confidence={guard.confidence})")
        return jsonify({"error": f"Query blocked: {guard.reason}", "confidence": guard.confidence}), 400

    orch = _get_orchestrator()
    results = orch.search_past_risks(guard.cleaned, data.get("portfolio_id"))
    return jsonify({"results": results}), 200


@api_bp.route("/search/market", methods=["POST"])
def search_market():
    data = request.json or {}
    query = data.get("query", "")
    if not query:
        return jsonify({"error": "query required"}), 400

    # LLM-based guardrail
    guard = sanitize_with_llm(query)
    if not guard.ok:
        logger.warning(f"search_market: guardrail blocked query (reason={guard.reason}, confidence={guard.confidence})")
        return jsonify({"error": f"Query blocked: {guard.reason}", "confidence": guard.confidence}), 400

    orch = _get_orchestrator()
    results = orch.search_past_market(guard.cleaned, data.get("symbol"))
    return jsonify({"results": results}), 200


# ============= Health =============

@api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}), 200
