"""Shared pytest fixtures for the backend test suite."""

from __future__ import annotations

# ── Set required environment variables BEFORE any app module is imported ──────
import os

os.environ.setdefault("SECRET_KEY", "testsecretkey_do_not_use_in_prod_32chars!")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/testdb")
os.environ.setdefault("DATABASE_SYNC_URL", "postgresql+psycopg2://x:x@localhost/testdb")
os.environ.setdefault("EMAIL_SKIP_SEND", "true")
os.environ.setdefault("PASSWORD_HASH_ROUNDS", "4")  # fast for tests
os.environ.setdefault("PASSWORD_MIN_LENGTH", "12")
# ─────────────────────────────────────────────────────────────────────────────

from collections.abc import AsyncGenerator  # noqa: E402

import app.models.email_verification  # noqa: E402, F401
import app.models.user  # noqa: E402, F401
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database import get_db  # noqa: E402
from app.core.models import Base  # noqa: E402
from app.main import app  # noqa: E402

# ── In-process SQLite database (no Postgres needed in CI) ─────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

_test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
_TestSessionLocal = async_sessionmaker(
    bind=_test_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(autouse=True, scope="function")
async def setup_db() -> AsyncGenerator[None, None]:
    """Create all tables before each test, drop after."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with _TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTPX AsyncClient wired to the FastAPI app with the test DB session."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
