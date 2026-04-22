"""HTTP client for the ai_system service."""

from __future__ import annotations

import os

import requests


class AIServiceError(RuntimeError):
    """Raised when ai_system returns an unusable response."""


def request_portfolio_review(portfolio: dict, transactions: list[dict], mode: str = "quick") -> dict:
    base_url = os.getenv("AI_SYSTEM_URL", "http://localhost:8000").rstrip("/")
    timeout = float(os.getenv("AI_SYSTEM_TIMEOUT_SECONDS", "30"))

    response = requests.post(
        f"{base_url}/orchestrate/portfolio-review",
        json={
            "portfolio": portfolio,
            "transactions": transactions,
            "mode": mode,
        },
        timeout=timeout,
    )

    try:
        payload = response.json()
    except ValueError as exc:
        raise AIServiceError("ai_system returned a non-JSON response") from exc

    if response.status_code >= 400:
        detail = payload.get("detail") if isinstance(payload, dict) else payload
        raise AIServiceError(f"ai_system request failed: {detail}")

    return payload
