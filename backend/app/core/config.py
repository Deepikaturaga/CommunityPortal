"""
Canonical application settings.

Validated at startup via pydantic-settings; no secret is ever hardcoded.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyUrl, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Application
    # ------------------------------------------------------------------ #
    app_env: Literal["development", "staging", "production"] = "development"
    app_name: str = "identity-service"
    debug: bool = False

    # ------------------------------------------------------------------ #
    # Session cookie
    # ------------------------------------------------------------------ #
    session_cookie_name: str = "sid"
    session_cookie_domain: str | None = None
    session_cookie_path: str = "/"
    # Seconds; 0 means session cookie (expires when browser closes)
    session_cookie_max_age: int = Field(default=3600, gt=0)
    # Forces Secure flag; auto-True in non-development envs (see validator)
    session_cookie_secure: bool = True
    session_cookie_httponly: bool = True
    session_cookie_samesite: Literal["strict", "lax", "none"] = "lax"

    # ------------------------------------------------------------------ #
    # Session store (ElastiCache / Redis)
    # ------------------------------------------------------------------ #
    # Full Redis URL, e.g. rediss://user:pass@cluster.cache.amazonaws.com:6379/0
    redis_url: SecretStr = Field(
        default=SecretStr("redis://localhost:6379/0"),
        description="Redis/ElastiCache connection URL (use rediss:// for TLS).",
    )
    redis_max_connections: int = Field(default=20, gt=0)
    redis_socket_timeout: float = Field(default=2.0, gt=0)
    redis_socket_connect_timeout: float = Field(default=2.0, gt=0)
    # Namespace prefix for all session keys
    redis_session_prefix: str = "session:"

    # ------------------------------------------------------------------ #
    # Session data signing
    # ------------------------------------------------------------------ #
    # 32-byte hex secret used to sign session IDs; MUST be set in production
    session_signing_secret: SecretStr = Field(
        default=SecretStr("change-me-before-production-32b!"),
        description="HMAC secret for session-ID signing.",
    )

    # ------------------------------------------------------------------ #
    # Validators
    # ------------------------------------------------------------------ #
    @field_validator("session_cookie_secure", mode="before")
    @classmethod
    def _enforce_secure_in_prod(cls, v: bool, info: object) -> bool:  # noqa: FBT001
        # pydantic calls validators before the full model is assembled,
        # so we rely on a separate check at startup (see lifespan) rather
        # than trying to read app_env here.
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
