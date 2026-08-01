from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Database ────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="sqlite+aiosqlite:///./test.db",
        description="Async SQLAlchemy DSN",
    )

    # ── Auth ────────────────────────────────────────────────────────────────
    secret_key: SecretStr = Field(
        default=...,
        min_length=32,
        description="JWT signing secret — never log this",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # ── Event backend ───────────────────────────────────────────────────────
    event_backend: Literal["memory", "sns"] = "memory"
    aws_sns_topic_arn: str | None = None
    aws_region: str = "us-east-1"

    @field_validator("aws_sns_topic_arn")
    @classmethod
    def _require_arn_when_sns(cls, v: str | None, info: object) -> str | None:
        # Pydantic v2: info.data carries already-validated siblings
        data = getattr(info, "data", {})
        if data.get("event_backend") == "sns" and not v:
            raise ValueError("aws_sns_topic_arn is required when event_backend=sns")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # pydantic-settings resolves env vars; secret_key required at runtime
    return Settings.model_validate({})
