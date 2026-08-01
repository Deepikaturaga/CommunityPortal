"""Application configuration validated at startup via pydantic-settings."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./test.db",
        description="Async SQLAlchemy database URL",
    )

    # JWT
    secret_key: str = Field(..., min_length=32, description="HS256 signing secret")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, ge=1)

    @field_validator("secret_key")
    @classmethod
    def secret_key_not_default(cls, v: str) -> str:
        if v == "change-me-in-production-use-at-least-32-random-bytes":
            import warnings  # noqa: PLC0415

            warnings.warn(
                "SECRET_KEY is set to the example default — rotate before production.",
                stacklevel=2,
            )
        return v


settings = Settings()
