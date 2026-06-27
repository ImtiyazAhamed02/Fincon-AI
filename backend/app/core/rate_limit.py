"""
app/core/rate_limit.py
─────────────────────────────────────────────────────────────────────────────
Concurrency Control Decorator
─────────────────────────────────────────────────────────────────────────────

Previously this module also handled Gemini→Grok LLM swapping. That logic has
been moved into SmartLLM (app/services/ai/smart_llm.py) which handles fallback
at the per-call level automatically.

This decorator now only:
  1. Serialises concurrent crew requests via a threading.Lock (free-tier safety
     — avoids hammering a rate-limited API with parallel requests).
  2. Catches top-level exceptions and re-raises them with a clean message.
"""

import threading
from functools import wraps

from app.core.logger import logger

# ── Global lock ───────────────────────────────────────────────────────────────
# Prevents parallel requests from racing each other on the free-tier quota.
_api_lock = threading.Lock()


def rate_limited_gemini(func):
    """
    Decorator that serialises FinancialCrew method calls.

    • Ensures only one crew run executes at a time (prevents free-tier
      parallel-request quota issues).
    • The actual Gemini→Grok fallback is handled transparently by SmartLLM.

    Usage:
        @rate_limited_gemini
        def analyze_stock(self, company, ticker): ...
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"[{func.__name__}] Waiting for API lock...")
        with _api_lock:
            logger.info(f"[{func.__name__}] Lock acquired — starting crew run.")
            try:
                result = func(*args, **kwargs)
                logger.info(f"[{func.__name__}] Crew run completed successfully.")
                return result
            except Exception as exc:
                logger.error(f"[{func.__name__}] Crew run failed: {exc}")
                raise

    return wrapper
