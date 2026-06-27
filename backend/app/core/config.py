"""
app/core/config.py
─────────────────────────────────────────────────────────────────────────────
Application Settings  (updated for multi-AI provider support)
─────────────────────────────────────────────────────────────────────────────
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # ── Server ────────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"

    # ── AI Providers ──────────────────────────────────────────────────────────
    # Primary: Google Gemini
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Fallback: Grok (powered by Groq's inference API)
    # Get a free key at https://console.groq.com
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: Optional[str] = "llama-3.3-70b-versatile"

    # News Provider
    FINNHUB_API_KEY: Optional[str] = None

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",   # Silently ignore any unknown .env keys
    )


settings = Settings()
