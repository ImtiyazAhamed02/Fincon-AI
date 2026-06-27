"""
app/services/ai/router.py
─────────────────────────────────────────────────────────────────────────────
AI Router — Multi-Provider Orchestration with Automatic Fallback
─────────────────────────────────────────────────────────────────────────────

Compatible with: CrewAI 0.22.5
                 NO crewai.LLM import — uses LangChain chat models directly.
                 CrewAI 0.22.x accepts any LangChain BaseChatModel as llm=.

Architecture:
    Frontend
        ↓
    Backend API (FastAPI)
        ↓
    AI Router  ← YOU ARE HERE
        ├── Gemini  (primary)   → ChatGoogleGenerativeAI
        └── Grok    (fallback)  → ChatOpenAI @ Groq endpoint

Routing Logic:
    1. get_primary_llm()  → Gemini via ChatGoogleGenerativeAI
    2. get_fallback_llm() → Grok  via ChatOpenAI (OpenAI-compatible Groq API)
    3. is_quota_error()   → classifies 429/quota exceptions to trigger fallback
    4. get_ai_llm()       → smart factory: Gemini first, Grok if Gemini unavailable

Scalability:
    To add GPT-4o or Claude:
      1. Create app/services/ai/openai.py  → return ChatOpenAI(model="gpt-4o", ...)
      2. Add to providers list in get_ai_llm()
      3. No other files change.
"""

from __future__ import annotations
from typing import Any

from app.core.logger import logger


# ── Quota / Rate-limit error keywords ────────────────────────────────────────
# If any of these appear in an exception string, the fallback is triggered.
_QUOTA_KEYWORDS = (
    "429",
    "quota",
    "too many requests",
    "resource_exhausted",
    "rate limit",
    "ratelimit",
    "quota exceeded",
    "billing",
    "exceeded your current quota",
    "list index out of range",
    "indexerror",
    "503",
    "service unavailable",
    "high demand"
)


def is_quota_error(error: Exception) -> bool:
    """
    Returns True if the exception is a Gemini quota / rate-limit error.

    Called by the rate-limiter decorator to decide whether to activate
    the Grok fallback instead of simply retrying or re-raising.

    Args:
        error: Any exception raised during an AI provider call.

    Returns:
        bool: True → trigger Grok fallback; False → unrelated error, re-raise.
    """
    error_str = str(error).lower()
    return any(keyword in error_str for keyword in _QUOTA_KEYWORDS)


# ── Provider factories ────────────────────────────────────────────────────────

def get_primary_llm() -> Any:
    """
    Returns the primary AI LLM — Google Gemini.

    Returns a ChatGoogleGenerativeAI instance (LangChain), which CrewAI 0.22.x
    accepts directly as Agent(llm=...).

    Raises:
        ValueError: If GEMINI_API_KEY is not configured.
    """
    # Lazy import to prevent circular dependencies at module load
    from app.services.ai.gemini import get_gemini_llm
    return get_gemini_llm()


def get_fallback_llm() -> Any:
    """
    Returns the fallback AI LLM — Grok (via Groq OpenAI-compatible endpoint).

    Returns a ChatOpenAI instance pointed at https://api.groq.com/openai/v1.
    Activated automatically when Gemini quota/rate-limit errors are detected.

    Raises:
        ValueError: If GROQ_API_KEY is not configured.
    """
    from app.services.ai.grok import get_grok_llm
    return get_grok_llm()


def get_ai_llm() -> Any:
    """
    Smart LLM factory — returns the best available provider at startup.

    Tries Gemini first. If Gemini cannot initialise (bad/missing key),
    automatically falls back to Grok. If neither is available, raises.

    Fallback chain: Gemini → Grok → RuntimeError

    Used by core/llm.py to create the singleton `primary_llm` at startup.

    Returns:
        LangChain BaseChatModel: First successfully initialised LLM.

    Raises:
        RuntimeError: If no AI provider could be initialised.
    """
    providers = [
        ("Gemini", get_primary_llm),
        ("Grok",   get_fallback_llm),
    ]

    last_error: Exception | None = None

    for provider_name, factory in providers:
        try:
            llm = factory()
            logger.info(f"[AIRouter] Active provider at startup: {provider_name}")
            return llm
        except Exception as exc:
            logger.warning(
                f"[AIRouter] {provider_name} unavailable at startup: {exc}"
            )
            last_error = exc

    raise RuntimeError(
        "No AI provider could be initialised. "
        "Configure GEMINI_API_KEY or GROQ_API_KEY in your .env file."
    ) from last_error
