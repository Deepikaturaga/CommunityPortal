"""Application settings – validated at startup via pydantic-settings."""

from __future__ import annotations

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────────────────────
    app_env: str = "development"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Rate-limit thresholds (per-account, sliding-window) ───────────────────
    ratelimit_register_max: int = 5
    ratelimit_register_window_seconds: int = 3600

    ratelimit_login_max: int = 10
    ratelimit_login_window_seconds: int = 900

    ratelimit_content_create_max: int = 60
    ratelimit_content_create_window_seconds: int = 3600

    @field_validator("secret_key")
    @classmethod
    def _secret_key_strength(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @model_validator(mode="after")
    def _no_default_secret_in_prod(self) -> "Settings":
        if self.app_env == "production" and "CHANGE_ME" in self.secret_key:
            raise ValueError("SECRET_KEY must not be the default value in production")
        return self


def get_settings() -> Settings:
    """Return a cached Settings instance (FastAPI dependency-safe)."""
    return _settings


# Module-level singleton; fail fast at import time if env is misconfigured.
_settings = Settings(
    secret_key="CHANGE_ME_IN_PRODUCTION_use_openssl_rand_hex_32_dev_only",
    database_url="sqlite+aiosqlite:///./dev.db",
)
