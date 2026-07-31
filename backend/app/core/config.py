from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings — sourced from environment variables or .env file.

    All secrets MUST be supplied via environment variables; never hardcode values here.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Application ---
    app_env: str = "development"
    debug: bool = False

    # --- Database ---
    database_url: str = "sqlite+aiosqlite:///./dev.db"

    # --- Security ---
    secret_key: str  # REQUIRED — no default; must be set in environment
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"


settings = Settings()  # secret_key must be supplied via environment variable
