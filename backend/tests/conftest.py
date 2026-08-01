"""Shared pytest fixtures for the backend test suite."""
from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import bcrypt  # type: ignore[import-untyped]
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from starlette.exceptions import HTTPException

# ---------------------------------------------------------------------------
# Force env before any app module imports Settings
# ---------------------------------------------------------------------------
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-only")
os.environ.setdefault("ENVIRONMENT", "test")

from app.core.database import Base, get_db  # noqa: E402
from app.main import create_app  # noqa: E402
from app.services.identity.models import AccountStatus, MFAMethod, User  # noqa: E402

# ---------------------------------------------------------------------------
# In-memory SQLite engine for unit + integration tests
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Pre-hash the test password once to avoid per-fixture bcrypt cost
_HASHED_CORRECT_PASSWORD = bcrypt.hashpw(
    b"correct-password", bcrypt.gensalt(rounds=4)  # low rounds for test speed
).decode()


@pytest_asyncio.fixture(scope="function")
async def engine() -> AsyncGenerator:  # type: ignore[type-arg]
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(engine: AsyncGenerator) -> AsyncGenerator[AsyncSession, None]:  # type: ignore[type-arg]
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(engine: AsyncGenerator) -> AsyncGenerator[AsyncClient, None]:  # type: ignore[type-arg]
    """HTTP test client with the DB overridden to the in-memory SQLite engine.

    HTTPException is a normal application result (not a DB error), so we
    commit the session even when the route raises one.  This ensures that
    side-effectful writes (e.g. failed_login_count increments) are visible
    to subsequent requests within the same test.  True DB errors
    (SQLAlchemyError) trigger a rollback.
    """
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except HTTPException:
                # Application-level rejection — commit any state already written
                # (e.g. failed_login_count increments) so subsequent requests
                # see the accumulated count.
                await session.commit()
                raise
            except SQLAlchemyError:
                await session.rollback()
                raise
            except Exception:
                await session.rollback()
                raise

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# User factory helpers
# ---------------------------------------------------------------------------


def _make_user(
    status: AccountStatus = AccountStatus.ACTIVE,
    mfa_method: MFAMethod = MFAMethod.NONE,
    mfa_enabled: bool = False,
    failed_login_count: int = 0,
    locked_until: datetime | None = None,
    email: str = "user@example.com",
) -> User:
    return User(
        id=uuid.uuid4(),
        email=email,
        password_hash=_HASHED_CORRECT_PASSWORD,
        full_name="Test User",
        status=status,
        mfa_method=mfa_method,
        mfa_enabled=mfa_enabled,
        failed_login_count=failed_login_count,
        locked_until=locked_until,
    )


@pytest_asyncio.fixture
async def active_user(db_session: AsyncSession) -> User:
    user = _make_user()
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def locked_user(db_session: AsyncSession) -> User:
    user = _make_user(
        status=AccountStatus.LOCKED,
        failed_login_count=5,
        locked_until=datetime.now(UTC) + timedelta(minutes=15),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def suspended_user(db_session: AsyncSession) -> User:
    user = _make_user(status=AccountStatus.SUSPENDED)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def unverified_user(db_session: AsyncSession) -> User:
    user = _make_user(status=AccountStatus.UNVERIFIED)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def totp_user(db_session: AsyncSession) -> User:
    user = _make_user(mfa_method=MFAMethod.TOTP, mfa_enabled=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
