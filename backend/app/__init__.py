"""Flask application factory and initialisation."""
import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv

# Load .env as early as possible
load_dotenv()

# Extensions (shared with models & routes)
db = SQLAlchemy()


def create_app(config_name: str = "development") -> Flask:
    """Application factory."""
    app = Flask(__name__)

    # Pick config class
    cfg_map = {
        "development": "app.config.DevelopmentConfig",
        "production": "app.config.ProductionConfig",
        "testing": "app.config.TestingConfig",
    }
    app.config.from_object(cfg_map.get(config_name, cfg_map["development"]))

    # Extensions
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": os.getenv("CORS_ORIGINS", "*")}})

    # Create SQL tables + bootstrap the default tenant
    with app.app_context():
        # Import models so SQLAlchemy knows about them
        import models.models  # noqa: F401
        db.create_all()
        _sqlite_add_missing_columns()
        _bootstrap_default_tenant()

    # Register API blueprints
    from app.routes import api_bp
    from app.auth import auth_bp, resolve_identity, _attach_to_g
    from app.audit import audit_bp
    from app.cases import cases_bp
    from app.sar import sar_bp
    from app.agent_reasoning_routes import reasoning_bp

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(audit_bp, url_prefix="/api")
    app.register_blueprint(cases_bp, url_prefix="/api")
    app.register_blueprint(sar_bp, url_prefix="/api")
    app.register_blueprint(reasoning_bp)

    # Structured JSON logging + /api/metrics for Prometheus scraping
    from app.observability import init_observability
    init_observability(app)

    # Resolve (user, tenant) once per request so every handler can rely on
    # g.current_user / g.current_tenant without opting in.
    @app.before_request
    def _load_identity():
        u, t = resolve_identity()
        _attach_to_g(u, t)

    @app.route("/health")
    def health():
        return {"status": "healthy"}, 200

    @app.route("/")
    def index():
        """Full web application UI."""
        return render_template("index.html")

    return app


def _bootstrap_default_tenant() -> None:
    """Ensure a 'default' tenant row exists so legacy (unauthenticated) calls have somewhere to attach."""
    from models.models import Tenant, DEFAULT_TENANT_SLUG
    if not Tenant.query.filter_by(slug=DEFAULT_TENANT_SLUG).first():
        db.session.add(Tenant(slug=DEFAULT_TENANT_SLUG, name="Default Tenant"))
        db.session.commit()


def _sqlite_add_missing_columns() -> None:
    """Lightweight forward-only migration for SQLite.

    db.create_all() creates missing tables but never adds columns to existing
    ones. Case management extended several tables (audit_logs, users, etc.)
    with new columns, so pre-existing local DBs break on first query. Walk
    each model, diff against the live schema, and ALTER TABLE ADD COLUMN for
    anything missing.
    """
    from sqlalchemy import inspect, text
    engine = db.engine
    if engine.dialect.name != "sqlite":
        return
    insp = inspect(engine)
    existing_tables = set(insp.get_table_names())
    for table_name, table in db.metadata.tables.items():
        if table_name not in existing_tables:
            continue
        live_cols = {c["name"] for c in insp.get_columns(table_name)}
        for col in table.columns:
            if col.name in live_cols:
                continue
            col_type = col.type.compile(dialect=engine.dialect)
            null_clause = "" if col.nullable else " NOT NULL"
            default_clause = ""
            if col.default is not None and getattr(col.default, "is_scalar", False):
                val = col.default.arg
                if isinstance(val, bool):
                    default_clause = f" DEFAULT {1 if val else 0}"
                elif isinstance(val, (int, float)):
                    default_clause = f" DEFAULT {val}"
                elif isinstance(val, str):
                    default_clause = f" DEFAULT '{val}'"
            ddl = f'ALTER TABLE "{table_name}" ADD COLUMN "{col.name}" {col_type}{null_clause}{default_clause}'
            try:
                with engine.begin() as conn:
                    conn.execute(text(ddl))
            except Exception:
                # Best-effort — skip columns SQLite refuses to add (e.g. NOT NULL
                # without default on populated tables). The caller will surface
                # the underlying error at query time.
                pass
