"""Application settings – validated at startup via pydantic-settings."""

from __future__ import annotations

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────────────────────
    app_env: str = "development"
    app_debug: bool = False

    # ── TLS / HTTPS enforcement ───────────────────────────────────────────────
    # When True the app sits behind an AWS ALB that has already terminated TLS.
    # The middleware trusts X-Forwarded-Proto and enforces HTTPS-only responses.
    https_behind_proxy: bool = True
    hsts_max_age: int = 31_536_000  # 1 year in seconds
    hsts_include_subdomains: bool = True
    hsts_preload: bool = False

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_allow_origins: list[str] = ["https://app.example.com"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    cors_allow_headers: list[str] = [
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "X-Idempotency-Key",
    ]

    # ── Content Security Policy ───────────────────────────────────────────────
    csp_policy: str = "default-src 'none'; frame-ancestors 'none'; form-action 'none'"

    # ── Validators ────────────────────────────────────────────────────────────
    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _split_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @field_validator("cors_allow_methods", mode="before")
    @classmethod
    def _split_methods(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [m.strip().upper() for m in v.split(",") if m.strip()]
        return v

    @field_validator("cors_allow_headers", mode="before")
    @classmethod
    def _split_headers(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [h.strip() for h in v.split(",") if h.strip()]
        return v

    @model_validator(mode="after")
    def _forbid_wildcard_with_credentials(self) -> Settings:
        if self.cors_allow_credentials and "*" in self.cors_allow_origins:
            raise ValueError(
                "CORS wildcard origin ('*') must not be used with credentials=true "
                "(OWASP A05 – Security Misconfiguration)."
            )
        return self


def get_settings() -> Settings:
    return Settings()
