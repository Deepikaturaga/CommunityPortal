from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/discussion_dev"

    # JWT
    secret_key: str = "change-me-in-production-min-32-chars-long!!"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Reply limits
    reply_min_length: int = 1
    reply_max_length: int = 10_000


@lru_cache
def get_settings() -> Settings:
    return Settings()
