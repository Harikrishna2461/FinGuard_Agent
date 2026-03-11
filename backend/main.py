#!/usr/bin/env python3
"""
main.py  –  Single entry-point for the entire FinGuard Agent backend.

Usage:
    python3 main.py

What happens on start:
    1. Loads .env
    2. Installs Python dependencies (pip) if needed
    3. Installs frontend npm packages if needed
    4. Builds React production bundle if it doesn't exist
    5. Initialises SQLite + ChromaDB
  6. Starts Flask (serves API *and* the React build)
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# ── resolve paths relative to this file ──────────────────────────
BASE_DIR = Path(__file__).resolve().parent                # backend/
PROJECT_DIR = BASE_DIR.parent                             # FinGuard_Agent/
FRONTEND_DIR = PROJECT_DIR / "frontend"
FRONTEND_BUILD = FRONTEND_DIR / "build"

os.chdir(BASE_DIR)                                        # ensure cwd = backend/


# ───────────────────────────────────────────────────────────────────
#  Helpers
# ───────────────────────────────────────────────────────────────────

def _run(cmd: list[str], cwd: str | Path = BASE_DIR, check: bool = True):
    """Run a subprocess, streaming output to the console."""
    print(f"\n  ▸ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(cwd), check=check)


def _pip_install():
    """Install Python requirements if any are missing."""
    req = BASE_DIR / "requirements.txt"
    if not req.exists():
        return
    print("\n⏳  Checking Python dependencies …")
    _run([sys.executable, "-m", "pip", "install", "-q", "-r", str(req)])
    print("  ✔  Python dependencies OK")


def _npm_install():
    """Run npm install in the frontend directory if node_modules is absent."""
    if not FRONTEND_DIR.exists():
        print("  ⚠  frontend/ directory not found – skipping npm install")
        return
    node_modules = FRONTEND_DIR / "node_modules"
    if node_modules.exists():
        return
    npm = shutil.which("npm")
    if npm is None:
        print("  ⚠  npm not found on PATH – skipping frontend install")
        return
    print("\n⏳  Installing frontend dependencies (npm install) …")
    _run([npm, "install"], cwd=FRONTEND_DIR)
    print("  ✔  npm install OK")


def _npm_build():
    """Build the React app if build/ does not exist yet."""
    if FRONTEND_BUILD.exists():
        return                               # already built
    npm = shutil.which("npm")
    if npm is None or not FRONTEND_DIR.exists():
        return
    print("\n⏳  Building React production bundle …")
    _run([npm, "run", "build"], cwd=FRONTEND_DIR)
    print("  ✔  Frontend build OK")


# ───────────────────────────────────────────────────────────────────
#  Main
# ───────────────────────────────────────────────────────────────────

def main():
    # 1. Load environment variables
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")

    print("=" * 60)
    print("  🛡️  FinGuard Agent  –  starting up")
    print("=" * 60)

    # 2. Install Python deps
    _pip_install()

    # 3. Install + build frontend (non-fatal – Flask still serves the API)
    try:
        _npm_install()
        _npm_build()
    except Exception as exc:
        print(f"  ⚠  Frontend setup failed ({exc})")
        print("     The API will still work; run the React dev server separately.")

    # 4. Create data directories
    chroma_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
    os.makedirs(chroma_dir, exist_ok=True)

    # 5. Bootstrap Flask + DB
    from app import create_app, db

    env = os.getenv("FLASK_ENV", "development")
    app = create_app(env)

    # Serve React static files from Flask in production
    if FRONTEND_BUILD.exists():
        from flask import send_from_directory

        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def serve_react(path):
            # API requests are already handled by the /api blueprint
            file_path = FRONTEND_BUILD / path
            if path and file_path.exists():
                return send_from_directory(str(FRONTEND_BUILD), path)
            return send_from_directory(str(FRONTEND_BUILD), "index.html")

    with app.app_context():
        db.create_all()

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")

    print(f"\n  🌐  Backend  → http://{host}:{port}")
    if FRONTEND_BUILD.exists():
        print(f"  🖥️   Frontend → http://{host}:{port}  (served by Flask)")
    else:
        print(f"  🖥️   Frontend → run  cd ../frontend && npm start  (dev mode on :3000)")
    print()

    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
