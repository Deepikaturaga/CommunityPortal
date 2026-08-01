"""
Application configuration — single canonical settings module.
All values read from environment variables; validated at startup.
"""

from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ------------------------------------------------------------------
    # Core security
    # ------------------------------------------------------------------
    SECRET_KEY: str = Field(
        ...,
        description="HMAC signing key for CSRF tokens, session cookies, etc. "
        "Must be >=32 random bytes in production.",
    )

    COOKIE_SECURE: bool = Field(
        default=True,
        description="Set Secure flag on cookies and emit HSTS header. "
        "Set to False only in local HTTP development.",
    )

    # ------------------------------------------------------------------
    # CORS / CSRF origin allow-list
    # ------------------------------------------------------------------
    ALLOWED_ORIGINS: list[str] = Field(
        default_factory=list,
        description="List of allowed request origins for CORS and CSRF origin check. "
        "e.g. ['https://app.example.com']",
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    APP_ENV: str = Field(
        default="production",
        description="'development' | 'staging' | 'production'",
    )
    DEBUG: bool = Field(default=False)

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/appdb",
    )

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------
    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v


settings = Settings()
