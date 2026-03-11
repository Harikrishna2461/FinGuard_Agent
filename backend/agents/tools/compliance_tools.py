"""
compliance_tools.py  –  CrewAI @tool wrappers for compliance / tax
"""

from crewai.tools import tool


@tool("Check PDT Violations")
def check_pdt_violations(transactions_json: str) -> str:
    """
    Scan transactions for Pattern Day Trader violations
    (4+ day-trades within 5 business days in a margin account).
    """
    return (
        f"Checking PDT violations:\n{transactions_json}\n"
        "[Tool placeholder – returns violation count and dates.]"
    )


@tool("Identify Wash Sales")
def identify_wash_sales(transactions_json: str) -> str:
    """
    Identify potential wash-sale violations where a security was
    sold at a loss and re-purchased within 30 days.
    """
    return (
        f"Scanning for wash sales:\n{transactions_json}\n"
        "[Tool placeholder – returns flagged transactions.]"
    )


@tool("Generate Tax Report")
def generate_tax_report(transactions_json: str, year: str) -> str:
    """
    Produce a capital-gains / losses summary for the given tax year.
    """
    return (
        f"Generating tax report for {year}:\n{transactions_json}\n"
        "[Tool placeholder – returns gains, losses, net liability.]"
    )
