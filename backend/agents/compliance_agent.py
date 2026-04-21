"""
compliance_agent.py

Responsible for:
    • Transaction compliance review (PDT, wash-sale, AML)
    • Tax reporting and optimisation
    • Regulatory risk flagging
"""

import json
from typing import Dict, Any, List

from agents.base_agent import FinancialBaseAgent


class ComplianceAgent(FinancialBaseAgent):
    """Reviews transactions for regulatory compliance and generates tax reports."""

    AGENT_DOMAIN = "compliance"

    def __init__(self):
        super().__init__("ComplianceOfficer")

    # ── compliance review ─────────────────────────────────────────
    def review_transactions_compliance(
        self, transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
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
        response = self.chat(prompt)
        return self._stamp({"review_type": "transaction_compliance", "findings": response})

    # ── tax report ────────────────────────────────────────────────
    def generate_tax_report(
        self,
        transaction_history: List[Dict[str, Any]],
        year: int,
    ) -> Dict[str, Any]:
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
        response = self.chat(prompt)
        return self._stamp({"report_type": "tax", "year": year, "report": response})