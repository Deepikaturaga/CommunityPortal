"""Shared pytest fixtures for the backend test suite."""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app as _app
from app.models.user import User
from app.services.media.s3_client import get_s3_client, override_s3_client, reset_s3_client

# ── Test settings override ─────────────────────────────────────────────────────

TEST_SETTINGS = Settings(
    app_env="testing",
    secret_key="test_secret_key_at_least_32_chars_long!!",
    database_url="sqlite+aiosqlite:///:memory:",
    s3_avatar_bucket="test-avatar-bucket",
    avatar_presign_put_expires_seconds=300,
    avatar_presign_get_expires_seconds=900,
    avatar_max_size_bytes=5_242_880,
    aws_region="us-east-1",
)


@pytest.fixture(autouse=True)
def _override_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setattr("app.core.config.get_settings", lambda: TEST_SETTINGS)
    # Patch everywhere settings is imported/called
    for module in [
        "app.core.database",
        "app.core.security",
        "app.services.media.service",
        "app.services.media.s3_client",
        "app.routers.media_router",
        "app.dependencies.auth",
    ]:
        with contextlib.suppress(AttributeError):
            monkeypatch.setattr(f"{module}.get_settings", lambda: TEST_SETTINGS)


# ── In-memory SQLite DB ────────────────────────────────────────────────────────

_test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    connect_args={"check_same_thread": False},
)
_TestSession: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_test_engine, expire_on_commit=False, autoflush=False, autocommit=False
)


@pytest_asyncio.fixture(autouse=True)
async def _setup_db() -> AsyncGenerator[None, None]:
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with _TestSession() as session:
        yield session


# ── S3 mock ────────────────────────────────────────────────────────────────────


@pytest.fixture()
def mock_s3() -> MagicMock:  # type: ignore[misc]
    client = MagicMock()
    client.generate_presigned_post.return_value = {
        "url": "https://test-avatar-bucket.s3.amazonaws.com/",
        "fields": {
            "key": "avatars/test-key",
            "Content-Type": "image/jpeg",
            "policy": "base64encodedpolicy",
            "x-amz-signature": "sig",
        },
    }
    client.generate_presigned_url.return_value = (
        "https://test-avatar-bucket.s3.amazonaws.com/avatars/test-key?X-Amz-Signature=sig"
    )
    override_s3_client(client)
    yield client
    reset_s3_client()


# ── Test user + JWT ────────────────────────────────────────────────────────────


@pytest_asyncio.fixture()
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        hashed_password=hash_password("password123"),
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture()
def auth_token(test_user: User) -> str:
    return create_access_token(str(test_user.id))


# ── HTTPX async client ─────────────────────────────────────────────────────────


@pytest_asyncio.fixture()
async def client(
    db_session: AsyncSession,
    mock_s3: MagicMock,
    auth_token: str,
) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTPX client with DB + S3 dependencies overridden."""

    async def _get_db_override() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    def _get_s3_override() -> Any:
        yield mock_s3

    _app.dependency_overrides[get_db] = _get_db_override
    _app.dependency_overrides[get_s3_client] = _get_s3_override

    async with AsyncClient(
        transport=ASGITransport(app=_app),
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {auth_token}"},
    ) as ac:
        yield ac

    _app.dependency_overrides.clear()
