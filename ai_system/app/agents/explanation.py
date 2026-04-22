"""Explanation agent service."""

from __future__ import annotations


def invoke(portfolio: dict, transactions: list[dict], findings: list[str]) -> dict:
    if findings:
        narrative = (
            f"Portfolio '{portfolio.get('name', 'Unnamed Portfolio')}' was reviewed across "
            f"{len(transactions)} recent transactions. "
            + " ".join(findings)
        )
    else:
        narrative = (
            f"Portfolio '{portfolio.get('name', 'Unnamed Portfolio')}' was reviewed and "
            "no material finding was surfaced in the quick path."
        )

    return {
        "agent": "explanation",
        "summary": narrative,
    }
