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

    # Create SQL tables
    with app.app_context():
        # Import models so SQLAlchemy knows about them
        import models.models  # noqa: F401
        db.create_all()

    # Register API blueprint
    from app.routes import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.route("/health")
    def health():
        return {"status": "healthy"}, 200

    @app.route("/")
    def index():
        """Full web application UI."""
        return render_template("index.html")

    return app
