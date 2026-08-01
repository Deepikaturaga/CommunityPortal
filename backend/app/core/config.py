"""Application configuration via environment variables."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="sqlite+aiosqlite:///./dev.db",
        description="Async SQLAlchemy database URL",
    )

    # ── JWT ───────────────────────────────────────────────────────────────────
    jwt_secret: SecretStr = Field(
        default="change-me-in-production-at-least-32-chars!",
        description="HMAC secret for signing JWTs — minimum 32 chars",
    )
    jwt_algorithm: str = Field(default="HS256")
    # Access token lifetime (minutes)
    access_token_expire_minutes: int = Field(default=15)
    # Refresh token lifetime (days)
    refresh_token_expire_days: int = Field(default=7)

    # ── Cookie / Session ─────────────────────────────────────────────────────
    cookie_name: str = Field(default="session")
    cookie_secure: bool = Field(default=True, description="Set Secure flag on session cookie")
    cookie_httponly: bool = Field(default=True, description="Set HttpOnly flag — no JS access")
    cookie_samesite: str = Field(
        default="lax", description="SameSite policy: strict | lax | none"
    )
    cookie_domain: str | None = Field(default=None)
    session_secret: SecretStr = Field(
        default="session-secret-change-me-32-chars!!",
        description="HMAC secret for signing session cookies (itsdangerous)",
    )
    # Session absolute expiry (seconds)
    session_max_age: int = Field(default=3600, description="Session max age in seconds")

    # ── CSRF ─────────────────────────────────────────────────────────────────
    csrf_header_name: str = Field(default="X-CSRF-Token")
    csrf_cookie_name: str = Field(default="csrf_token")
    csrf_token_expire_seconds: int = Field(default=3600)

    # ── Account Lockout ──────────────────────────────────────────────────────
    max_failed_login_attempts: int = Field(default=5)
    lockout_duration_seconds: int = Field(default=900, description="15 minutes")

    # ── TOTP / MFA ───────────────────────────────────────────────────────────
    totp_issuer: str = Field(default="MyApp")
    totp_digits: int = Field(default=6)
    totp_interval: int = Field(default=30)
    totp_valid_window: int = Field(
        default=1, description="Number of intervals before/after current to accept"
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_name: str = Field(default="Identity API")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    @field_validator("jwt_secret", mode="before")
    @classmethod
    def _secret_min_length(cls, v: str | SecretStr) -> str | SecretStr:
        raw = v.get_secret_value() if isinstance(v, SecretStr) else v
        if len(raw) < 32:
            raise ValueError("jwt_secret must be at least 32 characters")
        return v

    @field_validator("cookie_samesite")
    @classmethod
    def _samesite_valid(cls, v: str) -> str:
        if v.lower() not in {"strict", "lax", "none"}:
            raise ValueError("cookie_samesite must be strict, lax, or none")
        return v.lower()

    @property
    def access_token_expire_seconds(self) -> int:
        return self.access_token_expire_minutes * 60

    @property
    def refresh_token_expire_seconds(self) -> int:
        return self.refresh_token_expire_days * 24 * 3600


@lru_cache
def get_settings() -> Settings:
    """Return singleton Settings (cached after first call)."""
    return Settings()
