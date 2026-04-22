"""Small Groq adapter for ai_system agent modules."""

from __future__ import annotations

import os
import time

try:
    from groq import Groq
except ImportError:  # pragma: no cover - optional at import time
    Groq = None


def chat(message: str, system_prompt: str | None = None, max_retries: int = 2) -> str | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or Groq is None:
        return None

    client = Groq(api_key=api_key)
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": message})

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.4,
                max_tokens=700,
            )
            return response.choices[0].message.content
        except Exception:
            if attempt == max_retries - 1:
                return None
            time.sleep(2 ** attempt)

    return None
