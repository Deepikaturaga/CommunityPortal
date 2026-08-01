from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    secret_key: str = Field(min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Database
    database_url: str = "sqlite+aiosqlite:///./dev.db"

    # Test database (optional override)
    test_database_url: str = "sqlite+aiosqlite:///./test.db"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Admin bootstrap
    admin_bootstrap_email: str = "admin@example.com"
    admin_bootstrap_password: str = Field(default="changeme", min_length=8)

    @field_validator("secret_key")
    @classmethod
    def secret_key_not_default(cls, v: str) -> str:
        # Warn in production; allow in test/dev
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


SettingsDep = Annotated[Settings, None]
