"""
app/services/ai/smart_llm.py
─────────────────────────────────────────────────────────────────────────────
SmartLLM — Auto-Fallback LLM Proxy
─────────────────────────────────────────────────────────────────────────────

STRATEGY: Probe Gemini at startup with a direct HTTP call (no retries).
- If Gemini responds OK       → use Gemini as primary.
- If Gemini returns 429/quota → use Grok as primary for 5 minutes.

During crew runs, every LLM call is routed through the active provider.
If Gemini fails mid-run (quota hit), the fallback kicks in for the
remainder of the session.

Why HTTP probe instead of LangChain invoke?
  LangChain's ChatGoogleGenerativeAI uses tenacity with hardcoded 10-retry
  exponential backoff (up to 60s per wait). There is no supported way to
  disable this from the outside. A raw HTTP probe with a short timeout
  gives us a definitive answer in <3 seconds.
"""

from __future__ import annotations

import time
import threading
import requests as _requests
from typing import Any, Iterator, List, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult

from app.core.logger import logger

# ── Quota / rate-limit keywords ───────────────────────────────────────────────
_QUOTA_KEYWORDS = (
    "429", "quota", "too many requests", "resource_exhausted",
    "rate limit", "ratelimit", "quota exceeded", "exceeded your current quota",
    "resourceexhausted", "503", "service unavailable", "high demand", "overloaded",
)

# Gemini REST probe endpoint (no retries, fast)
_GEMINI_PROBE_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent"
)
_PROBE_TIMEOUT = 5  # seconds
_FALLBACK_TTL  = 300.0  # 5 minutes


def _is_quota_error(error: Exception) -> bool:
    return any(kw in str(error).lower() for kw in _QUOTA_KEYWORDS)


def _probe_gemini(api_key: str) -> tuple[bool, str]:
    """
    Sends a minimal REST request to Gemini to check availability.
    Returns (is_available, reason_string).
    Does NOT use LangChain — so no tenacity retries.
    """
    try:
        resp = _requests.post(
            _GEMINI_PROBE_URL,
            params={"key": api_key},
            json={"contents": [{"parts": [{"text": "hi"}]}]},
            timeout=_PROBE_TIMEOUT,
        )
        if resp.status_code == 200:
            return True, "OK"
        if resp.status_code in (429, 503):
            body = resp.text[:200]
            return False, f"HTTP {resp.status_code}: {body}"
        return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, str(e)


class SmartLLM(BaseChatModel):
    """
    LangChain BaseChatModel with automatic Gemini → Grok failover.

    Probes Gemini before every call (using a cache):
    - Probe is free (REST, no tenacity), takes < 5s.
    - Once Gemini is confirmed unavailable, Grok is used for 5 minutes.
    - After 5 minutes, Gemini is re-probed automatically.
    """

    class Config:
        arbitrary_types_allowed = True

    _primary: Any = None       # ChatGoogleGenerativeAI
    _fallback: Any = None      # ChatOpenAI @ Groq
    _lock: Any = None
    _fallback_until: float = 0.0
    _gemini_api_key: str = ""

    def __init__(self, **data):
        super().__init__(**data)
        object.__setattr__(self, "_lock", threading.Lock())
        object.__setattr__(self, "_fallback_until", 0.0)
        object.__setattr__(self, "_primary", None)
        object.__setattr__(self, "_fallback", None)
        # Resolve Gemini API key for probing
        try:
            from app.core.config import settings
            object.__setattr__(self, "_gemini_api_key", settings.GEMINI_API_KEY or "")
        except Exception:
            object.__setattr__(self, "_gemini_api_key", "")

    # ── Lazy provider factories ───────────────────────────────────────────────

    def _get_primary(self) -> Any:
        if self._primary is None:
            from app.services.ai.gemini import get_gemini_llm
            object.__setattr__(self, "_primary", get_gemini_llm())
        return self._primary

    def _get_fallback(self) -> Any:
        # Always get fresh cascade so it picks the best available Grok model
        from app.services.ai.grok import get_grok_llm_with_cascade
        return get_grok_llm_with_cascade()

    # ── Availability cache ────────────────────────────────────────────────────

    def _is_fallback_active(self) -> bool:
        return time.time() < self._fallback_until

    def _activate_fallback(self, reason: str = "") -> None:
        object.__setattr__(self, "_fallback_until", time.time() + _FALLBACK_TTL)
        logger.warning(
            f"[SmartLLM] Gemini unavailable ({reason}) — "
            f"using Grok for next {_FALLBACK_TTL:.0f}s."
        )

    def _gemini_is_available(self) -> bool:
        """
        Returns True if Gemini can accept requests RIGHT NOW.
        Uses a direct REST probe (no tenacity / no LangChain retries).
        """
        if not self._gemini_api_key:
            return False
        available, reason = _probe_gemini(self._gemini_api_key)
        if not available:
            self._activate_fallback(reason)
        return available

    # ── Core generation ───────────────────────────────────────────────────────

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs,
    ) -> ChatResult:
        with self._lock:
            # ── Fast path: Gemini known down → Grok ───────────────────────
            if self._is_fallback_active():
                logger.info("[SmartLLM] Gemini in cooldown — routing to Grok.")
                return self._call_fallback(messages, stop, **kwargs)

            # ── Probe Gemini before calling (< 5s, no retries) ────────────
            logger.info("[SmartLLM] Probing Gemini availability...")
            if not self._gemini_is_available():
                # _activate_fallback already called inside _gemini_is_available
                return self._call_fallback(messages, stop, **kwargs)

            # ── Gemini confirmed available — call it ──────────────────────
            try:
                logger.info("[SmartLLM] Calling Gemini LLM...")
                primary = self._get_primary()
                result = primary._generate(messages, stop=stop, **kwargs)
                logger.info("[SmartLLM] Gemini OK.")
                return result
            except Exception as e:
                if _is_quota_error(e):
                    self._activate_fallback(f"mid-call quota: {type(e).__name__}")
                    return self._call_fallback(messages, stop, **kwargs)
                logger.warning(f"[SmartLLM] Gemini error: {type(e).__name__} — trying Grok.")
                return self._call_fallback(messages, stop, **kwargs)

    def _call_fallback(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs,
    ) -> ChatResult:
        """
        Tries each Grok model in cascade order.
        On a 429 / rate-limit from one model, moves directly to the next
        without relying on the probe (which can miss daily TPD limits).
        """
        from app.services.ai.grok import _MODEL_CASCADE, get_grok_llm, _is_rate_limited
        from app.core.config import settings

        groq_key = settings.GROQ_API_KEY
        last_error: Exception = Exception("No Grok models available")

        for model in _MODEL_CASCADE:
            try:
                logger.info(f"[SmartLLM] Trying Grok model: {model}")
                llm = get_grok_llm(model_name=model)
                result = llm._generate(messages, stop=stop, **kwargs)
                logger.info(f"[SmartLLM] Grok OK ({model}).")
                return result
            except Exception as e:
                if _is_rate_limited(e):
                    logger.warning(f"[SmartLLM] {model} rate-limited — trying next.")
                    last_error = e
                    continue
                else:
                    # Non-rate-limit error — log and try next model anyway
                    logger.warning(f"[SmartLLM] {model} error ({type(e).__name__}) — trying next.")
                    last_error = e
                    continue

        logger.error(f"[SmartLLM] All Grok models exhausted. Last error: {last_error}")
        raise Exception(
            "Both AI providers (Gemini and Grok) are currently unavailable. "
            "Grok daily token limits have been reached. Please try again in ~1 hour."
        ) from last_error


    # ── LangChain protocol ────────────────────────────────────────────────────

    @property
    def _llm_type(self) -> str:
        return "smart_llm_auto_fallback"

    @property
    def _identifying_params(self) -> dict:
        return {"primary": "Gemini", "fallback": "Grok", "fallback_ttl": _FALLBACK_TTL}

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        result = self._generate(messages, stop=stop, **kwargs)
        for gen in result.generations:
            yield gen
