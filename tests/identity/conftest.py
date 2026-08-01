"""
tests/identity/conftest.py
--------------------------
Shared pytest fixtures for the identity / auth test suite.

Scope hierarchy
---------------
session  — engine + tables (created once)
function — async DB session, HTTP client (isolated per test)
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_totp_secret,
    hash_password,
)
from app.core.session import set_auth_cookies
from app.db.base import Base, get_db
from app.main import create_app
from app.models.user import User

# ── Test-only settings (SQLite in-memory, cookies not Secure for test) ─────────

TEST_SETTINGS = Settings(
    database_url="sqlite+aiosqlite:///:memory:",
    jwt_secret="test-secret-key-that-is-at-least-32-chars",
    session_secret="test-session-secret-32-chars!!!!",
    cookie_secure=False,      # httpx test client doesn't enforce HTTPS
    cookie_httponly=True,
    cookie_samesite="lax",
    access_token_expire_minutes=15,
    refresh_token_expire_days=7,
    session_max_age=3600,
    csrf_token_expire_seconds=3600,
    max_failed_login_attempts=5,
    lockout_duration_seconds=900,
    totp_valid_window=1,
    debug=True,
)

# ── Async engine (per-session scope) ─────────────────────────────────────────


@pytest.fixture(scope="session")
def event_loop():
    """Use a single event loop for the whole test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create the async SQLite engine once per session."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture()
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:  # type: ignore[type-arg]
    """Per-test async DB session — rolls back after each test for isolation."""
    async_session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        yield session
        await session.rollback()


# ── FastAPI app + HTTPX client ────────────────────────────────────────────────


@pytest_asyncio.fixture()
async def app(db_session: AsyncSession) -> FastAPI:
    """Create a test app instance wired to the test DB session and settings."""
    _app = create_app(settings=TEST_SETTINGS)

    # Override the get_db dependency to use the per-test session
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    # Override settings dependency
    from app.core.config import get_settings

    _app.dependency_overrides[get_db] = _override_get_db
    _app.dependency_overrides[get_settings] = lambda: TEST_SETTINGS
    return _app


@pytest_asyncio.fixture()
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTPX client wired to the test app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        follow_redirects=True,
    ) as ac:
        yield ac


# ── User factories ────────────────────────────────────────────────────────────

_DEFAULT_PASSWORD = "Password1!"


async def _make_user(
    db: AsyncSession,
    *,
    email: str = "user@example.com",
    password: str = _DEFAULT_PASSWORD,
    totp_enabled: bool = False,
    totp_secret: str | None = None,
    failed_attempts: int = 0,
    locked_until: datetime | None = None,
    refresh_token_jti: str | None = None,
) -> User:
    secret = totp_secret or (generate_totp_secret() if totp_enabled else None)
    user = User(
        email=email,
        hashed_password=hash_password(password),
        totp_enabled=totp_enabled,
        totp_secret=secret,
        failed_login_attempts=failed_attempts,
        locked_until=locked_until,
        refresh_token_jti=refresh_token_jti,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture()
async def plain_user(db_session: AsyncSession) -> User:
    """A regular active user with no MFA."""
    return await _make_user(db_session)


@pytest_asyncio.fixture()
async def mfa_user(db_session: AsyncSession) -> User:
    """A user with TOTP MFA enabled."""
    return await _make_user(
        db_session,
        email="mfa@example.com",
        totp_enabled=True,
    )


@pytest_asyncio.fixture()
async def locked_user(db_session: AsyncSession) -> User:
    """A user whose account is currently locked out."""
    from datetime import timedelta

    return await _make_user(
        db_session,
        email="locked@example.com",
        failed_attempts=5,
        locked_until=datetime.now(tz=timezone.utc) + timedelta(seconds=900),
    )


# ── Auth cookie helpers ───────────────────────────────────────────────────────


def make_cookie_header(cookies: dict[str, str]) -> str:
    """Build a Cookie header string from a dict."""
    return "; ".join(f"{k}={v}" for k, v in cookies.items())


def extract_cookies(response: Any) -> dict[str, str]:
    """Extract set-cookie values from an httpx Response into a dict."""
    result: dict[str, str] = {}
    for name, cookie in response.cookies.items():
        result[name] = cookie
    return result
