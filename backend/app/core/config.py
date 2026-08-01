"""Application settings — validated at startup via pydantic-settings."""

from __future__ import annotations

from typing import Annotated

from pydantic import AnyHttpUrl, EmailStr, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_env: str = "development"
    secret_key: str = Field(min_length=32)
    allowed_hosts: list[AnyHttpUrl] = []

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str  # asyncpg URL for the async engine
    database_sync_url: str  # psycopg2 URL for Alembic

    # ── Email verification ────────────────────────────────────────────────────
    email_verification_token_ttl: Annotated[int, Field(gt=0)] = 86400
    email_skip_send: bool = True
    smtp_host: str = "localhost"
    smtp_port: Annotated[int, Field(gt=0, lt=65536)] = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: EmailStr = "noreply@example.com"

    # ── AWS SES (production email provider) ───────────────────────────────────
    # email_provider: "smtp" (default) | "ses"
    email_provider: str = "smtp"
    aws_region: str = "us-east-1"
    ses_from_arn: str = ""  # optional; uses smtp_from identity when empty

    # ── Security ──────────────────────────────────────────────────────────────
    password_hash_rounds: Annotated[int, Field(ge=4, le=31)] = 12
    password_min_length: Annotated[int, Field(ge=8)] = 12

    @field_validator("database_url")
    @classmethod
    def _must_be_asyncpg(cls, v: str) -> str:
        if "asyncpg" not in v:
            raise ValueError("database_url must use the asyncpg driver")
        return v


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings
