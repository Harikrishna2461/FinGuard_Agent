"""Compliance agent service."""

from __future__ import annotations


def invoke(portfolio: dict, transactions: list[dict], mode: str = "quick") -> dict:
    findings = []
    if any((txn.get("type") or "").lower() not in {"buy", "sell", "dividend"} for txn in transactions):
        findings.append("One or more transaction types fall outside the current simplified policy set.")
    if len(transactions) >= 20:
        findings.append("High transaction volume should be reviewed for reporting and surveillance thresholds.")
    if not findings:
        findings.append("Quick compliance screen found no immediate policy concern.")

    return {
        "agent": "compliance",
        "mode": mode,
        "summary": " ".join(findings),
        "findings": findings,
    }
