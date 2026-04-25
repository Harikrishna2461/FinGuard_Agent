"""WSGI entry-point for gunicorn / production Docker."""
import sys
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(str(BACKEND_DIR))

from app import create_app  # noqa: E402

app = create_app("production")
