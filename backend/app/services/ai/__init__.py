# AI Services Package
# Exports the primary interface: get_primary_llm, get_fallback_llm, is_quota_error
from app.services.ai.router import get_primary_llm, get_fallback_llm, is_quota_error

__all__ = ["get_primary_llm", "get_fallback_llm", "is_quota_error"]
