from __future__ import annotations

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: PostgresDsn = Field(
        default=...,
        description="Async PostgreSQL DSN (asyncpg driver)",
    )

    # ── Auth ──────────────────────────────────────────────────────────────────
    secret_key: str = Field(default=..., min_length=32)
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, gt=0)

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = Field(default="INFO")

    @field_validator("log_level")
    @classmethod
    def _log_level_upper(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return upper


settings = Settings()
