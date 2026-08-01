"""Application settings — validated at startup via pydantic-settings."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"
    SECRET_KEY: str  # no default — must be set in env; validated at startup
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ENVIRONMENT: str = "development"

    # Prevent SQLAlchemy echo in production
    @property
    def db_echo(self) -> bool:
        return self.ENVIRONMENT == "development"


settings = Settings()  # type: ignore[call-arg]
