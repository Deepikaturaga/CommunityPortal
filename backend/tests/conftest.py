"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture()
def default_settings() -> Settings:
    """Settings with HTTPS-proxy mode ON (mirrors production ALB deployment)."""
    return Settings(
        app_env="test",
        app_debug=False,
        https_behind_proxy=True,
        hsts_max_age=31_536_000,
        hsts_include_subdomains=True,
        hsts_preload=False,
        cors_allow_origins=["https://app.example.com"],
        cors_allow_credentials=True,
        cors_allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        cors_allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        csp_policy="default-src 'none'; frame-ancestors 'none'; form-action 'none'",
    )


@pytest.fixture()
def no_proxy_settings(default_settings: Settings) -> Settings:
    """Settings where the app is NOT behind a TLS-terminating proxy."""
    return default_settings.model_copy(update={"https_behind_proxy": False})


@pytest.fixture()
async def client(default_settings: Settings) -> AsyncClient:
    """AsyncClient wired to the test app (HTTPS-proxy mode)."""
    app = create_app(default_settings)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://testserver") as ac:
        yield ac  # type: ignore[misc]


@pytest.fixture()
async def client_no_proxy(no_proxy_settings: Settings) -> AsyncClient:
    """AsyncClient wired to the test app (direct TLS mode – no redirect logic)."""
    app = create_app(no_proxy_settings)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://testserver") as ac:
        yield ac  # type: ignore[misc]
