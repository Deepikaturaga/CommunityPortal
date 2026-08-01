from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./dev.db"

    # Security
    secret_key: str = "changeme-dev-secret-32-bytes-long!!"
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"

    # Runtime
    environment: str = "development"
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
