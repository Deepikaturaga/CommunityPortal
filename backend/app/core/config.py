"""Application configuration — validated at startup via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────
    app_env: Literal["development", "testing", "production"] = "development"
    secret_key: str = Field(..., min_length=32)
    access_token_expire_minutes: int = Field(30, gt=0)

    # ── Database ───────────────────────────────────────────
    database_url: str = Field(..., pattern=r"^(postgresql|sqlite)")

    # ── AWS / S3 ───────────────────────────────────────────
    aws_region: str = "us-east-1"
    s3_avatar_bucket: str = Field(..., min_length=3)

    # Time-limited presigned URLs (seconds)
    avatar_presign_put_expires_seconds: int = Field(300, ge=60, le=900)
    avatar_presign_get_expires_seconds: int = Field(900, ge=60, le=3600)

    # Hard upload cap (default 5 MiB)
    avatar_max_size_bytes: int = Field(5_242_880, ge=1, le=20_971_520)

    # Optional overrides — must be absent/empty in production (IAM roles used)
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_endpoint_url: str = ""  # LocalStack / testing override

    @field_validator("secret_key")
    @classmethod
    def _secret_key_not_default(cls, v: str) -> str:
        if v.lower().startswith("change_me"):
            raise ValueError("secret_key must be changed from the default placeholder")
        return v

    @model_validator(mode="after")
    def _prod_must_not_have_static_creds(self) -> "Settings":
        if self.app_env == "production" and (
            self.aws_access_key_id or self.aws_secret_access_key
        ):
            raise ValueError(
                "Static AWS credentials must not be set in production; use IAM roles."
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton settings instance (cached after first call)."""
    return Settings()
