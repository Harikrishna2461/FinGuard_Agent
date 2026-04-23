"""Shared helpers for ai_system analysis modules."""

from __future__ import annotations

from ai_system.app.ml import get_risk_engine


def format_dict(data: dict) -> str:
    return "\n".join(f"  {key}: {value}" for key, value in data.items())


def format_list(items: list) -> str:
    return "\n".join(f"  {index + 1}. {item}" for index, item in enumerate(items))


def ml_score_transactions(transactions: list[dict]) -> str:
    engine = get_risk_engine()
    if not engine or not transactions:
        return ""

    lines = ["\n\n── ML Risk Pre-Screening Results ──"]
    high_risk_count = 0
    for index, txn in enumerate(transactions[:20]):
        try:
            result = engine.score(txn)
            label = result["risk_label"]
            flags = result["flags"]
            if label in ("high", "critical"):
                high_risk_count += 1
            lines.append(
                f"  Txn {index + 1}: score={result['final_score']}/100 "
                f"label={label} method={result['method']} "
                f"hard_block={result['hard_block']} "
                f"flags=[{', '.join(flags)}]"
            )
        except Exception:
            lines.append(f"  Txn {index + 1}: ML scoring failed")

    lines.insert(
        1,
        f"  Total scanned: {len(transactions[:20])} | High/Critical: {high_risk_count}",
    )
    return "\n".join(lines)
