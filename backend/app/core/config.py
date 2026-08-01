"""Application configuration validated at startup via pydantic-settings."""
from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./test.db"

    # JWT
    secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Runtime
    environment: str = "development"
    debug: bool = False

    @field_validator("secret_key")
    @classmethod
    def _secret_key_not_default(cls, v: str) -> str:
        if v == "CHANGE_ME_IN_PRODUCTION":  # noqa: S105
            import warnings

            warnings.warn(
                "SECRET_KEY is using the default placeholder value. "
                "Set a secure random value in production.",
                stacklevel=2,
            )
        return v


settings = Settings()
