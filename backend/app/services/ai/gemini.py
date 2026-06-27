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


