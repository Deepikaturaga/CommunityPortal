"""Shared pytest fixtures for profile/admin/taxonomy auth tests."""
from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.passwords import hash_password
from app.core.database import Base, get_db
from app.main import create_app
from app.models.enums import UserRole
from app.models.user import User
# Import taxonomy models so Base.metadata knows about them
from app.models.taxonomy import TaxonomyVocabulary, TaxonomyTerm  # noqa: F401

# ──────────────────────────────────────────────────────────────────────────────
# In-memory SQLite engine (isolated per test session)
# ──────────────────────────────────────────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture(scope="session")
def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture()
async def db_session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI test client with DB override
# ──────────────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture()
async def client(session_factory) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ──────────────────────────────────────────────────────────────────────────────
# User factory helpers
# ──────────────────────────────────────────────────────────────────────────────

PASSWORD = "Test1234!"


async def _create_user(db: AsyncSession, role: UserRole, suffix: str = "") -> User:
    uid = str(uuid.uuid4())
    tag = suffix or uid[:8]
    user = User(
        id=uid,
        email=f"{role.value}-{tag}@test.example",
        hashed_password=hash_password(PASSWORD),
        full_name=f"{role.value.title()} User",
        role=role,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _get_token(client: AsyncClient, email: str, password: str = PASSWORD) -> str:
    resp = await client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": password},
    )
    assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
    return resp.json()["access_token"]


@pytest_asyncio.fixture()
async def users(db_session: AsyncSession) -> dict[str, User]:
    """Create one user per role, keyed by role value."""
    return {
        role.value: await _create_user(db_session, role)
        for role in UserRole
    }


@pytest_asyncio.fixture()
async def tokens(client: AsyncClient, users: dict[str, User]) -> dict[str, str]:
    """Return JWT tokens keyed by role value."""
    result: dict[str, str] = {}
    for role_val, user in users.items():
        result[role_val] = await _get_token(client, user.email)
    return result


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
