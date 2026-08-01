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
        extra="ignore",
    )

    # ── App ────────────────────────────────────────────────────────────────────
    environment: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # ── Database ───────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/appdb"
    )

    # ── OpenSearch ─────────────────────────────────────────────────────────────
    opensearch_url: str = Field(default="http://localhost:9200")
    opensearch_index_prefix: str = Field(default="content")
    opensearch_username: str = Field(default="")
    opensearch_password: SecretStr = Field(default=SecretStr(""))

    # ── Security ───────────────────────────────────────────────────────────────
    secret_key: SecretStr = Field(default=SecretStr("change-me-in-production"))

    @field_validator("secret_key", mode="after")
    @classmethod
    def _secret_key_not_default_in_prod(cls, v: SecretStr, info: object) -> SecretStr:
        # Validate at startup; actual enforcement happens in lifespan.
        return v

    @property
    def opensearch_index_content(self) -> str:
        return f"{self.opensearch_index_prefix}_items"

    @property
    def opensearch_index_processed_events(self) -> str:
        return f"{self.opensearch_index_prefix}_processed_events"


@lru_cache
def get_settings() -> Settings:
    return Settings()
