"""Compliance logic aligned to the legacy prompts."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from ai_system.app.llm import chat


def review_transactions_compliance(transactions: list[dict]) -> dict:
    prompt = (
        "You are a compliance officer. Review these transactions for regulatory compliance:\n\n"
        f"Transactions:\n{json.dumps(transactions[:20], indent=2)}\n\n"
        "Check for:\n"
        "1. Pattern Day Trader (PDT) violations\n"
        "2. Wash sale violations\n"
        "3. Insider trading concerns\n"
        "4. Reporting requirements\n"
        "5. Tax implications\n"
        "6. AML (Anti-Money Laundering) flags"
    )
    response = chat(prompt)
    return {
        "agent": "ComplianceOfficer",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "review_type": "transaction_compliance",
        "findings": response or "Compliance review unavailable.",
    }


def generate_tax_report(transaction_history: list[dict], year: int) -> dict:
    prompt = (
        f"You are a tax specialist. Generate a tax report for {year} based on:\n\n"
        f"Transactions:\n{json.dumps(transaction_history, indent=2)}\n\n"
        "Provide:\n"
        "1. Total capital gains/losses\n"
        "2. Short-term vs long-term breakdown\n"
        "3. Dividend income summary\n"
        "4. Tax-loss harvesting opportunities\n"
        "5. Estimated tax liability\n"
        "6. Recommended strategies for next year"
    )
    response = chat(prompt)
    return {
        "agent": "ComplianceOfficer",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "report_type": "tax",
        "year": year,
        "report": response or "Tax report unavailable.",
    }


def invoke(portfolio: dict, transactions: list[dict], mode: str = "quick") -> dict:
    if mode == "full":
        result = review_transactions_compliance(transactions)
        return {
            "agent": "compliance",
            "mode": mode,
            "summary": result["findings"],
            "findings": [result["findings"]],
        }

    findings = []
    if any(
        (txn.get("type") or "").lower() not in {"buy", "sell", "dividend"}
        for txn in transactions
    ):
        findings.append(
            "One or more transaction types fall outside the current simplified policy set."
        )
    if len(transactions) >= 20:
        findings.append(
            "High transaction volume should be reviewed for reporting and surveillance thresholds."
        )
    if not findings:
        findings.append("Quick compliance screen found no immediate policy concern.")

    return {
        "agent": "compliance",
        "mode": mode,
        "summary": " ".join(findings),
        "findings": findings,
    }


class ComplianceAgent:
    AGENT_DOMAIN = "compliance"

    def review_transactions_compliance(self, transactions: list[dict]) -> dict:
        return review_transactions_compliance(transactions)

    def generate_tax_report(self, transaction_history: list[dict], year: int) -> dict:
        return generate_tax_report(transaction_history, year)
