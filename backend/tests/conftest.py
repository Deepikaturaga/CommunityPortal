"""Shared pytest fixtures for the backend test suite."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.enums import PostStatus, UserRole
from app.core.security import create_access_token
from app.main import create_app
from app.models.post import Post
from app.models.user import User

# ---------------------------------------------------------------------------
# In-memory SQLite engine for tests
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

_test_engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
_TestSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_test_engine, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with _TestSessionLocal() as session:
        yield session
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Helpers: build ORM objects directly (no HTTP) to keep tests fast
# ---------------------------------------------------------------------------


def _make_user(
    role: UserRole = UserRole.READER,
    *,
    user_id: uuid.UUID | None = None,
    email: str | None = None,
) -> User:
    uid = user_id or uuid.uuid4()
    return User(
        id=uid,
        email=email or f"{uid}@example.com",
        hashed_password="$2b$12$notreal",
        display_name="Test User",
        role=role,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_post(
    author: User,
    status: PostStatus = PostStatus.PUBLISHED,
    *,
    post_id: uuid.UUID | None = None,
) -> Post:
    pid = post_id or uuid.uuid4()
    return Post(
        id=pid,
        title="Test Post",
        slug=f"test-post-{pid}",
        body="Body text",
        status=status,
        author_id=author.id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest_asyncio.fixture
async def author_user(db: AsyncSession) -> User:
    user = _make_user(UserRole.AUTHOR)
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def other_author_user(db: AsyncSession) -> User:
    user = _make_user(UserRole.AUTHOR)
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession) -> User:
    user = _make_user(UserRole.ADMIN)
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def reader_user(db: AsyncSession) -> User:
    user = _make_user(UserRole.READER)
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def draft_post(db: AsyncSession, author_user: User) -> Post:
    post = _make_post(author_user, PostStatus.DRAFT)
    db.add(post)
    await db.flush()
    return post


@pytest_asyncio.fixture
async def published_post(db: AsyncSession, author_user: User) -> Post:
    post = _make_post(author_user, PostStatus.PUBLISHED)
    db.add(post)
    await db.flush()
    return post


def bearer(user: User) -> dict[str, Any]:
    """Return Authorization header for a user."""
    token = create_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}
