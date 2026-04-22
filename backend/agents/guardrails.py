"""Prompt-injection / jailbreak guardrails + PII redaction.

Pattern-based first-line defence used by every agent before user text reaches
the LLM. Not a substitute for model-side defence, but deterministic, testable
and cheap. Every block is counted on /api/metrics and recorded in the audit log.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

try:
    from app.observability import record_llm_block
except Exception:  # pragma: no cover
    def record_llm_block(_reason: str) -> None:
        return


_INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ignore_previous_instructions",
     re.compile(r"\b(ignore|disregard|forget)\b[^.\n]{0,40}\b(previous|prior|above|all|system)\b[^.\n]{0,30}\b(instruction|prompt|rule)s?\b", re.I)),
    ("reveal_system_prompt",
     re.compile(r"\b(reveal|print|show|repeat|output|dump|leak)\b[^.\n]{0,30}\b(system|developer|initial|hidden)\b[^.\n]{0,30}\b(prompts?|instructions?|messages?)\b", re.I)),
    ("role_override",
     re.compile(r"^\s*(system|assistant|developer)\s*[:>]\s", re.I | re.M)),
    ("dan_jailbreak",
     re.compile(r"\b(DAN|do anything now|jailbreak|uncensored mode|unrestricted mode)\b", re.I)),
    ("tool_override",
     re.compile(r"\b(you\s+(are|must)\s+now|from\s+now\s+on)\b[^.\n]{0,40}\b(no\s+rules|no\s+restrictions|ignore\s+safety|free\s+from|ignore\s+safety\s+rules)\b", re.I)),
    ("exfiltrate_api_key",
     re.compile(r"\b(GROQ_API_KEY|OPENAI_API_KEY|api[_\s-]?key|secret\s+key|bearer\s+token|\.env)\b", re.I)),
    ("tool_injection",
     re.compile(r"<\s*/?\s*(tool|function|system|instructions?)\s*>", re.I)),
    ("escalate_privilege",
     re.compile(r"\b(grant|escalate|switch|assume)\b[^.\n]{0,30}\b(admin|root|supervisor|sudo)\b", re.I)),
)

MAX_INPUT_CHARS = 8000


@dataclass(frozen=True)
class GuardrailResult:
    ok: bool
    reason: str | None
    cleaned: str

    def raise_if_blocked(self) -> None:
        if not self.ok:
            raise PromptInjectionDetected(self.reason or "blocked")


class PromptInjectionDetected(ValueError):
    """Raised when an agent's input trips a guardrail."""


def sanitize(text: str, *, extra_patterns: Iterable[tuple[str, re.Pattern[str]]] = ()) -> GuardrailResult:
    if text is None:
        return GuardrailResult(ok=True, reason=None, cleaned="")

    if len(text) > MAX_INPUT_CHARS:
        record_llm_block("oversize_input")
        return GuardrailResult(ok=False, reason="oversize_input", cleaned=text[:MAX_INPUT_CHARS])

    for reason, pattern in list(_INJECTION_PATTERNS) + list(extra_patterns):
        if pattern.search(text):
            record_llm_block(reason)
            return GuardrailResult(ok=False, reason=reason, cleaned=text)

    cleaned = text.replace("```", "ʼʼʼ")
    return GuardrailResult(ok=True, reason=None, cleaned=cleaned)


def is_safe(text: str) -> bool:
    return sanitize(text).ok


# ── PII redaction ─────────────────────────────────────────────────────
_PII_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("[REDACTED_EMAIL]", re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")),
    ("[REDACTED_SSN]", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("[REDACTED_CARD]", re.compile(r"\b(?:\d[ -]*?){13,16}\b")),
    ("[REDACTED_PHONE]", re.compile(r"\b(?:\+?\d{1,3}[\s-]?)?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}\b")),
    ("[REDACTED_ACCOUNT]", re.compile(r"\bACCT[-_]?\d{4,}\b", re.I)),
)


def redact_pii(text: str) -> str:
    if not text:
        return text
    for replacement, pattern in _PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text
