"""SQLite helpers for the minimal FastAPI backend."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


def _db_path() -> Path:
    configured = os.getenv("BACKEND_DB_PATH", "./data/backend.db")
    path = Path(configured)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def connect():
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                total_value REAL NOT NULL DEFAULT 0,
                cash_balance REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                total_amount REAL NOT NULL,
                fees REAL NOT NULL DEFAULT 0,
                notes TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id)
            )
            """
        )


def fetch_one(query: str, params: tuple = ()) -> dict | None:
    with connect() as conn:
        row = conn.execute(query, params).fetchone()
    return dict(row) if row else None


def fetch_all(query: str, params: tuple = ()) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def execute(query: str, params: tuple = ()) -> int:
    with connect() as conn:
        cursor = conn.execute(query, params)
        return int(cursor.lastrowid)
