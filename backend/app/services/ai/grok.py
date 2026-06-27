"""
app/services/ai/grok.py
─────────────────────────────────────────────────────────────────────────────
Grok AI Provider Service  (via Groq's OpenAI-compatible API)
─────────────────────────────────────────────────────────────────────────────

Model cascade: tries models in order, each has its own TPD quota.
If the primary model is rate-limited (per-minute OR daily), falls back to next.

Model priority order (best quality first):
  1. llama-3.3-70b-versatile       — best quality, 100K TPD
  2. meta-llama/llama-4-scout-17b  — strong quality, separate daily quota
  3. llama-3.1-8b-instant          — fast & reliable, separate daily quota
"""

from app.core.config import settings
from app.core.logger import logger
from typing import Any

_GROQ_BASE_URL = "https://api.groq.com/openai/v1"

_MODEL_CASCADE = [
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.1-8b-instant",
]

_RATE_LIMIT_KEYWORDS = (
    "429", "rate_limit_exceeded", "rate limit", "tokens per day",
    "tpd", "too many requests", "quota", "ratelimit",
)


def _is_rate_limited(error: Exception) -> bool:
    return any(kw in str(error).lower() for kw in _RATE_LIMIT_KEYWORDS)


def _probe_model(model: str, api_key: str) -> tuple:
    """
    Probes a model with a real request to detect both per-minute AND daily
    (TPD) quota limits. Returns (available: bool, reason: str).

    After a successful call, checks the remaining-tokens header to ensure
    there is enough headroom (>= 5000 tokens) for a real crew agent call.
    """
    import requests as _req
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Briefly explain what a stock market is in 2 sentences."}],
        "max_tokens": 80,
    }
    try:
        resp = _req.post(
            f"{_GROQ_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=8,
        )
        if resp.status_code == 200:
            # Check remaining tokens in the current rate-limit window
            remaining = resp.headers.get("x-ratelimit-remaining-tokens", "99999")
            try:
                remaining_int = int(remaining)
            except ValueError:
                remaining_int = 99999
            if remaining_int < 5000:
                return False, f"Low token headroom ({remaining_int} tokens left in window)"
            return True, "OK"
        if resp.status_code == 429:
            err_msg = resp.json().get("error", {}).get("message", resp.text)[:150]
            return False, f"429: {err_msg}"
        return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, str(e)[:100]


def get_grok_llm(model_name: str = None) -> Any:
    """
    Returns a ChatOpenAI instance for the given Groq model.
    """
    groq_api_key = settings.GROQ_API_KEY
    if not groq_api_key or groq_api_key in ("your_groq_api_key", ""):
        raise ValueError(
            "GROQ_API_KEY is not configured. "
            "Get a free key at https://console.groq.com and add it to .env"
        )

    if model_name is None:
        env_model = getattr(settings, "GROQ_MODEL", None) or _MODEL_CASCADE[0]
        if env_model.startswith("groq/"):
            env_model = env_model[len("groq/"):]
        model_name = env_model

    logger.info(f"[GrokService] Initialising Grok LLM: model={model_name}")

    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model_name,
        openai_api_key=groq_api_key,
        openai_api_base=_GROQ_BASE_URL,
        temperature=0.2,
        max_retries=0,   # Never retry — SmartLLM handles retry logic
    )


def get_grok_llm_with_cascade() -> Any:
    """
    Probes each model in the cascade and returns the first available one.
    Each model has a completely independent daily token quota on Groq.
    """
    groq_api_key = settings.GROQ_API_KEY
    if not groq_api_key or groq_api_key in ("your_groq_api_key", ""):
        raise ValueError("GROQ_API_KEY not configured.")

    for model in _MODEL_CASCADE:
        logger.info(f"[GrokService] Probing model: {model}")
        available, reason = _probe_model(model, groq_api_key)
        if available:
            logger.info(f"[GrokService] Using model: {model}")
            return get_grok_llm(model_name=model)
        else:
            logger.warning(f"[GrokService] {model} unavailable ({reason}) — trying next.")

    raise RuntimeError(
        "All Grok models are currently rate-limited. "
        "This usually resets within 1 hour. Please try again later."
    )
