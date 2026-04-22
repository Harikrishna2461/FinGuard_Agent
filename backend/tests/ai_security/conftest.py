"""Pytest configuration for the AI-security suite.

Ensures `backend/` is on sys.path so `from agents...` / `from ml...` work
whether pytest is invoked from the repo root or from `backend/`.
"""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
