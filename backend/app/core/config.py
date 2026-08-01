"""Application configuration validated at startup via pydantic-settings."""
from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Security
    secret_key: str = "dev-secret-key-change-in-production-min-32-chars!!"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Database
    database_url: str = "sqlite+aiosqlite:///./test.db"

    @field_validator("secret_key")
    @classmethod
    def _secret_key_min_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("secret_key must be at least 32 characters")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
