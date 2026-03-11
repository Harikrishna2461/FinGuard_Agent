"""
base_agent.py  –  Shared Groq-powered base for every FinGuard agent.

Each specialised agent inherits from FinancialBaseAgent so the Groq
LLM configuration is in one place.
"""

import os
from groq import Groq
from typing import Dict, Any, List
from datetime import datetime


class FinancialBaseAgent:
    """Thin wrapper around the Groq chat API used by every agent."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
        self.conversation_history: List[Dict[str, str]] = []

    # ── core LLM call ──────────────────────────────────────────────
    def chat(self, message: str, system_prompt: str | None = None) -> str:
        """Send *message* to the Groq model, return the assistant reply."""
        if system_prompt:
            self.conversation_history = [
                {"role": "system", "content": system_prompt}
            ]

        self.conversation_history.append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.conversation_history,
            temperature=0.7,
            max_tokens=2048,
        )

        reply = response.choices[0].message.content
        self.conversation_history.append({"role": "assistant", "content": reply})
        return reply

    # ── helpers ────────────────────────────────────────────────────
    def reset_history(self):
        self.conversation_history.clear()

    def _stamp(self, extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Return a dict with agent name + UTC timestamp, merged with *extra*."""
        base = {
            "agent": self.agent_name,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if extra:
            base.update(extra)
        return base
