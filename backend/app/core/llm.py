"""
app/core/llm.py
─────────────────────────────────────────────────────────────────────────────
LLM Instance Factory  (CrewAI 0.22.5 compatible)
─────────────────────────────────────────────────────────────────────────────

Returns a SmartLLM — a LangChain-compatible proxy that:
  1. Calls Gemini first.
  2. Falls back to Grok (Groq) automatically on any quota / rate-limit error.
  3. Caches the fallback state for 5 minutes so rate-limited Gemini is skipped.

This replaces the old monkeypatch + rate_limit decorator approach. The proxy
approach is more reliable because the fallback is embedded in the LLM object
itself — so every CrewAI Agent that holds a reference gets the fallback for
free, even when multiple agents share the same LLM instance.

The public interface `primary_llm` is unchanged — crew.py imports and uses it
identically.
"""

from app.core.logger import logger
from app.services.ai.smart_llm import SmartLLM

logger.info("[AIRouter] Initialising SmartLLM (Gemini → Grok auto-fallback).")

primary_llm = SmartLLM()

logger.info("[AIRouter] SmartLLM ready.")
