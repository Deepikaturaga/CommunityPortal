"""Application settings validated at startup via pydantic-settings."""

from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = Field(..., description="SQLAlchemy async DSN")

    # Auth / JWT
    secret_key: str = Field(..., min_length=32, description="HS256 signing key")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, gt=0)

    # Runtime
    debug: bool = Field(default=False)

    @field_validator("database_url")
    @classmethod
    def _no_sync_driver(cls, v: str) -> str:
        if v.startswith("postgresql://"):
            # Transparently upgrade legacy DSNs to asyncpg
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return (and cache) the application settings singleton."""
    global _settings  # noqa: PLW0603
    if _settings is None:
        _settings = Settings()
    return _settings
