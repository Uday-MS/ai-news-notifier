"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the AI News Notifier backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────
    APP_NAME: str = "AI News Notifier"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://ainuser:ainpass@db:5432/aindb"

    # ── Redis ────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"

    # ── JWT ──────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "CHANGE_ME_TO_A_RANDOM_SECRET_KEY_AT_LEAST_32_CHARS"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── CORS ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]

    # ── Google OAuth (architecture only) ─────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # ── Email Provider (Resend) ──────────────────────────────────────────
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "AI News <noreply@resend.dev>"

    # ── Frontend ─────────────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:5173"

    # ── Collector Engine ─────────────────────────────────────────────────
    COLLECTOR_LOG_LEVEL: str = "INFO"
    GITHUB_API_TOKEN: str = ""
    COLLECTOR_REQUEST_TIMEOUT: int = 30
    COLLECTOR_MAX_ITEMS_PER_RUN: int = 100
    COLLECTOR_MAX_RETRIES: int = 3
    COLLECTOR_RETRY_BACKOFF_BASE: float = 1.0

    # ── LLM Intelligence ────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    LLM_PROVIDER: str = "gemini"
    LLM_MODEL: str = "gemini-2.0-flash"
    LLM_MAX_RETRIES: int = 3
    LLM_RETRY_BACKOFF_BASE: float = 2.0
    LLM_REQUEST_TIMEOUT: int = 30
    LLM_MAX_TOKENS: int = 2048
    INTELLIGENCE_PROMPT_VERSION: str = "1.0"
    LLM_BATCH_SIZE: int = 10
    LLM_QUOTA_COOLDOWN_SECONDS: int = 3600

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings = Settings()
