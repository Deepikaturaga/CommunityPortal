"""Shared test fixtures for the backend test suite."""
from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, build_engine, build_session_factory, get_db
from app.core.security import create_access_token, hash_password
from app.main import create_app
from app.models.content import ContentItem, ContentStatus
from app.models.moderation import ModerationAction, ModerationVerdict
from app.models.user import User, UserRole, UserStatus

TEST_DB_URL = "sqlite+aiosqlite:///./test_dashboard.db"


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = build_engine(TEST_DB_URL)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    factory = build_session_factory(engine)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


def admin_token(user_id: str = "admin-001") -> str:
    return create_access_token(subject=user_id, extra_claims={"role": "admin"})


def user_token(user_id: str = "user-001") -> str:
    return create_access_token(subject=user_id, extra_claims={"role": "user"})


def moderator_token(user_id: str = "mod-001") -> str:
    return create_access_token(subject=user_id, extra_claims={"role": "moderator"})


# ---------------------------------------------------------------------------
# Data seeding helpers
# ---------------------------------------------------------------------------


async def seed_user(
    db: AsyncSession,
    *,
    user_id: str | None = None,
    role: UserRole = UserRole.user,
    status: UserStatus = UserStatus.active,
    created_at: datetime | None = None,
) -> User:
    u = User(
        id=user_id or str(uuid.uuid4()),
        email=f"{uuid.uuid4()}@example.com",
        hashed_password=hash_password("Password1!"),
        display_name="Test User",
        role=role,
        status=status,
    )
    if created_at is not None:
        u.created_at = created_at
    db.add(u)
    await db.flush()
    return u


async def seed_content(
    db: AsyncSession,
    *,
    author_id: str,
    status: ContentStatus = ContentStatus.pending,
    created_at: datetime | None = None,
) -> ContentItem:
    c = ContentItem(
        id=str(uuid.uuid4()),
        author_id=author_id,
        title="Test content",
        body="Body text",
        status=status,
    )
    if created_at is not None:
        c.created_at = created_at
    db.add(c)
    await db.flush()
    return c


async def seed_moderation(
    db: AsyncSession,
    *,
    content_item_id: str,
    moderator_id: str | None,
    verdict: ModerationVerdict,
    created_at: datetime | None = None,
) -> ModerationAction:
    m = ModerationAction(
        id=str(uuid.uuid4()),
        content_item_id=content_item_id,
        moderator_id=moderator_id,
        verdict=verdict,
    )
    if created_at is not None:
        m.created_at = created_at
    db.add(m)
    await db.flush()
    return m
