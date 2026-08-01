from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str

    # Security — JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # MFA
    mfa_challenge_expire_seconds: int = 300

    # Lockout
    max_login_attempts: int = 5
    lockout_duration_seconds: int = 900
    # Max per-attempt back-off delay before returning a 401 (caps the delay schedule)
    lockout_delay_max_seconds: float = 5.0

    # App
    environment: str = "development"
    log_level: str = "INFO"

    @field_validator("secret_key")
    @classmethod
    def _secret_key_not_default(cls, v: str) -> str:
        if v.startswith("change-me"):
            import os

            if os.getenv("ENVIRONMENT", "development") == "production":
                raise ValueError("SECRET_KEY must be changed from the default in production")
        return v

    @model_validator(mode="after")
    def _validate_lockout(self) -> Settings:
        if self.max_login_attempts < 1:
            raise ValueError("max_login_attempts must be >= 1")
        if self.lockout_duration_seconds < 1:
            raise ValueError("lockout_duration_seconds must be >= 1")
        if self.lockout_delay_max_seconds < 0:
            raise ValueError("lockout_delay_max_seconds must be >= 0")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
