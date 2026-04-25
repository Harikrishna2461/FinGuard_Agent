#!/usr/bin/env python3
"""
main.py  –  Single entry-point for the entire FinGuard Agent.

Usage  (from project root):
    python3 main.py

What happens on start:
    1. Loads .env
    2. Installs Python dependencies (pip) if needed
    3. Initialises SQLite + ChromaDB
    4. Starts Flask (serves API + UI from project_root/frontend/index.html)
"""

import os
import sys
import subprocess
from pathlib import Path

# ── resolve paths relative to this file (project root) ───────────
PROJECT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_DIR / "backend"
FRONTEND_DIR = PROJECT_DIR / "frontend"

# Add backend/ to sys.path so that `from app import …`, `from agents import …`,
# `from ml import …`, etc. work exactly as before.
sys.path.insert(0, str(BACKEND_DIR))

# Flask / SQLAlchemy and all backend imports expect cwd = backend/
os.chdir(BACKEND_DIR)


# ───────────────────────────────────────────────────────────────────
#  Helpers
# ───────────────────────────────────────────────────────────────────

def _run(cmd: list[str], cwd: str | Path = BACKEND_DIR, check: bool = True):
    """Run a subprocess, streaming output to the console."""
    print(f"\n  ▸ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(cwd), check=check)


def _pip_install():
    """Install Python requirements if any are missing."""
    req = BACKEND_DIR / "requirements.txt"
    if not req.exists():
        return
    print("\n⏳  Checking Python dependencies …")
    _run([sys.executable, "-m", "pip", "install", "-q", "-r", str(req)])
    print("  ✔  Python dependencies OK")


# ───────────────────────────────────────────────────────────────────
#  Main
# ───────────────────────────────────────────────────────────────────

def main():
    # 1. Load environment variables (backend/.env)
    from dotenv import load_dotenv
    load_dotenv(BACKEND_DIR / ".env")

    print("=" * 60)
    print("  🛡️  FinGuard Agent  –  starting up")
    print("=" * 60)

    # 2. Install Python deps
    _pip_install()

    # 3. Create data directories (relative to backend/)
    chroma_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
    os.makedirs(chroma_dir, exist_ok=True)

    # 4. Bootstrap Flask + DB
    from app import create_app, db

    env = os.getenv("FLASK_ENV", "development")
    app = create_app(env)

    with app.app_context():
        db.create_all()

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5001))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

    if not FRONTEND_DIR.exists():
        print(f"  ⚠  frontend/ not found at {FRONTEND_DIR} — UI will not load")
    print(f"\n  🌐  App  → http://{host}:{port}")
    print(f"  🖥️   UI   → http://{host}:{port}  (frontend/index.html)")
    print()

    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()
