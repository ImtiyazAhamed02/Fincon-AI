"""
app/services/ai/gemini.py
─────────────────────────────────────────────────────────────────────────────
Gemini AI Provider Service
─────────────────────────────────────────────────────────────────────────────

Compatible with: CrewAI 0.22.5
LLM type      : langchain_google_genai.ChatGoogleGenerativeAI
                (CrewAI 0.22.x accepts any LangChain chat model as `llm=`)

Responsibilities:
  - Build and return a ChatGoogleGenerativeAI instance for Google Gemini.
  - Validates the API key before creating the instance.
  - Exposes a clean factory: get_gemini_llm()
"""


from app.core.config import settings
from app.core.logger import logger

from typing import Any

# ── Patch LangChain tenacity retry loop ───────────────────────────────────────
# By default, langchain_google_genai's _create_retry_decorator retries 10 times
# with exponential backoff (2s, 4s, 8s, 16s, 32s, 64s = ~126s total) on 429
# ResourceExhausted before raising the exception. This causes agent runs to hang
# for > 2 minutes whenever Gemini free quota is exhausted.
# We patch it to stop after attempt 1 so SmartLLM can failover to Groq instantly (< 0.5s).
try:
    import langchain_google_genai.chat_models as _cm
    from tenacity import retry, stop_after_attempt

    _cm._create_retry_decorator = lambda: retry(stop=stop_after_attempt(1), reraise=True)
except Exception as _patch_err:
    logger.debug(f"[GeminiService] Could not patch tenacity retry decorator: {_patch_err}")

try:
    from crewai import LLM
    HAS_CREWAI_LLM = True
except ImportError:
    HAS_CREWAI_LLM = False


def get_gemini_llm() -> Any:
    """
    Factory that returns the appropriate Gemini LLM instance depending on the CrewAI version.
    """

    # ── Validate API key ────────────────────────────────────────────────────
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY in ("your_gemini_api_key", ""):
        raise ValueError(
            "GEMINI_API_KEY is not configured. "
            "Please set a valid key in your .env file."
        )

    model_name: str = settings.GEMINI_MODEL
    logger.info(f"[GeminiService] Initialising Gemini LLM: model={model_name}")

    if HAS_CREWAI_LLM:
        # CrewAI 0.30+ uses LiteLLM via the LLM class
        return LLM(
            model=f"gemini/{model_name}",
            api_key=settings.GEMINI_API_KEY,
            temperature=0.2
        )
    else:
        # CrewAI 0.22.x uses LangChain ChatGoogleGenerativeAI
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.2,
            convert_system_message_to_human=True,
            max_retries=0,  # Fail immediately — SmartLLM handles retries & fallback
        )


