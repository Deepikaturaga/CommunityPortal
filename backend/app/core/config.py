"""Application configuration — validated at startup via pydantic-settings."""

from __future__ import annotations

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/app",
        description="Async SQLAlchemy database URL",
    )

    # ── Search backend ────────────────────────────────────────────────────────
    search_host: AnyHttpUrl = Field(
        default="http://localhost:9200",  # type: ignore[assignment]
        description="OpenSearch / Elasticsearch base URL",
    )
    search_username: str = Field(default="admin")
    search_password: SecretStr = Field(default=SecretStr("admin"))
    search_use_ssl: bool = Field(default=False)
    search_verify_certs: bool = Field(default=False)

    # ── Reconciliation job ────────────────────────────────────────────────────
    reindex_batch_size: int = Field(default=500, gt=0, le=10_000)
    reindex_scroll_timeout: str = Field(default="5m")
    reindex_max_retries: int = Field(default=3, ge=0)

    # ── Scheduler (APScheduler) ────────────────────────────────────────────────
    reindex_cron_enabled: bool = Field(default=False)
    reindex_cron_hour: int = Field(default=2, ge=0, le=23)
    reindex_cron_minute: int = Field(default=0, ge=0, le=59)

    # ── General ────────────────────────────────────────────────────────────────
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")


settings = Settings()
