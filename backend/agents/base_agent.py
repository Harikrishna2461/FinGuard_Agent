"""
base_agent.py  –  Shared Groq-powered base for every FinGuard agent.

Each specialised agent inherits from FinancialBaseAgent so the Groq
LLM configuration is in one place.
"""

import os
import logging
import time
from groq import Groq
from typing import Dict, Any, List
from datetime import datetime

# RAG knowledge-base retrieval
import vector_store

logger = logging.getLogger(__name__)


class FinancialBaseAgent:
    """Thin wrapper around the Groq chat API used by every agent."""

    # Subclasses should set this to their domain name so the RAG
    # retrieval filters the knowledge_base collection correctly.
    # Valid values: alert_intake, compliance, customer_context,
    #   escalation, explanation, market_intelligence,
    #   portfolio_analysis, risk_assessment, risk_detection
    AGENT_DOMAIN: str | None = None

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        
        # Verify API key is available
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            error_msg = "GROQ_API_KEY environment variable not set"
            logger.error(f"{agent_name}: {error_msg}")
            raise ValueError(error_msg)
        
        self.client = Groq(api_key=api_key)
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b")#-versatile")
        self.conversation_history: List[Dict[str, str]] = []
        logger.info(f"{agent_name}: Initialized with model {self.model}")

    # ── RAG context retrieval ──────────────────────────────────────
    def _get_rag_context(self, query: str, n: int = 3) -> str:
        """Retrieve relevant knowledge-base passages for *query*."""
        try:
            return vector_store.get_rag_context(
                query, agent_domain=self.AGENT_DOMAIN, n=n
            )
        except Exception:
            return ""

    # ── core LLM call ──────────────────────────────────────────────
    def chat(self, message: str, system_prompt: str | None = None, max_retries: int = 3) -> str:
        """Send *message* to the Groq model, return the assistant reply.
        
        Automatically augments the message with relevant knowledge-base
        context (RAG) when an AGENT_DOMAIN is set.
        
        Includes error handling with informative error messages and
        automatic retry on rate limit errors with exponential backoff.
        """
        if system_prompt:
            self.conversation_history = [
                {"role": "system", "content": system_prompt}
            ]

        # Inject RAG context before the user message
        rag_context = self._get_rag_context(message)
        if rag_context:
            augmented = (
                f"── Reference Knowledge ──\n{rag_context}\n"
                f"── End Reference Knowledge ──\n\n{message}"
            )
        else:
            augmented = message

        self.conversation_history.append({"role": "user", "content": augmented})

        # Retry loop for rate limits
        for attempt in range(max_retries):
            try:
                # Check API key
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key:
                    error_msg = (
                        "❌ LLM Configuration Error: GROQ_API_KEY environment variable is not set.\n"
                        "Please set GROQ_API_KEY in your .env file: GROQ_API_KEY=gsk_..."
                    )
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                if api_key.startswith("gsk_") and len(api_key) < 20:
                    error_msg = (
                        "❌ LLM Configuration Error: GROQ_API_KEY appears to be invalid or incomplete.\n"
                        f"Current key length: {len(api_key)} (expected 100+)"
                    )
                    logger.error(error_msg)
                    raise ValueError(error_msg)

                if attempt == 0:
                    logger.info(f"{self.agent_name}: Calling Groq LLM (model: {self.model})")
                else:
                    logger.info(f"{self.agent_name}: Retry attempt {attempt}/{max_retries - 1}")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation_history,
                    temperature=0.7,
                    max_tokens=2048,
                )

                reply = response.choices[0].message.content
                self.conversation_history.append({"role": "assistant", "content": reply})
                return reply
                
            except ValueError as e:
                # Configuration errors - don't retry
                logger.error(f"{self.agent_name}: Configuration error: {str(e)}")
                raise
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                
                # Check if it's a rate limit error
                is_rate_limit = "429" in error_msg or "rate_limit" in error_msg or "Rate limit" in error_msg
                
                if is_rate_limit and attempt < max_retries - 1:
                    # Exponential backoff: 2s, 4s, 8s, etc.
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"{self.agent_name}: Rate limited. Waiting {wait_time}s before retry "
                        f"(attempt {attempt + 1}/{max_retries - 1})"
                    )
                    time.sleep(wait_time)
                    continue
                
                # Parse specific Groq API errors
                if "401" in error_msg or "Unauthorized" in error_msg or "APIError" in error_msg:
                    user_msg = (
                        "❌ LLM Authentication Failed: Invalid or expired Groq API key\n"
                        f"Details: {error_msg}\n"
                        "Fix: Update GROQ_API_KEY in .env file with valid key from https://console.groq.com"
                    )
                elif is_rate_limit:
                    user_msg = (
                        "⏳ LLM Rate Limited: Too many requests to Groq API (exceeded after retries)\n"
                        f"Details: {error_msg}\n"
                        "Fix: Wait a few minutes and retry. Consider upgrading Groq API plan for higher limits."
                    )
                elif "503" in error_msg or "Service unavailable" in error_msg:
                    user_msg = (
                        "🚨 LLM Service Unavailable: Groq API is temporarily down\n"
                        f"Details: {error_msg}\n"
                        "Fix: Check https://status.groq.com and retry in a moment"
                    )
                else:
                    user_msg = (
                        f"❌ LLM Call Failed ({error_type}):\n"
                        f"{error_msg}\n"
                        f"Agent: {self.agent_name}\n"
                        "Fix: Check API key, rate limits, and Groq API status"
                    )
                
                logger.error(
                    f"{self.agent_name}: LLM call failed\n"
                    f"Error Type: {error_type}\n"
                    f"Error Message: {error_msg}"
                )
                raise RuntimeError(user_msg) from e

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
