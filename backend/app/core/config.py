"""Application configuration via pydantic-settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./blog_test.db",
        description="SQLAlchemy async database URL",
    )

    # JWT / Auth
    secret_key: str = Field(
        default="CHANGE_ME_IN_PRODUCTION",
        description="HMAC secret for JWT signing",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Runtime
    environment: str = "development"
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
