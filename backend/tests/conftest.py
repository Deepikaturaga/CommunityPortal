from __future__ import annotations

# Pytest configuration — async SQLite in-memory database, one engine per test.
#
# Root-cause note (VER-004):
#   pytest discovers tests/conftest.py and registers it under the module name
#   ``conftest`` (rootdir-relative).  Test files that do
#   ``from tests.conftest import _test_session_factory`` cause Python to load a
#   *second* module object under the key ``tests.conftest``.  The two objects
#   have separate ``__dict__``s, so a ``global _current_factory`` write inside
#   a fixture (executed in the ``conftest`` module) is invisible to the proxy
#   object whose ``__call__`` closure sees ``tests.conftest._current_factory``.
#
#   Fix: store the active factory in a single well-known location that is found
#   by *both* module objects at call-time — sys.modules["conftest"].  The proxy
#   always looks it up there, regardless of which module object it lives in.
import sys
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import get_current_user_id, get_is_moderator
from app.main import create_app
from app.models.discussion import Discussion, Reply
from app.models.enums import DiscussionStatus, ReplyStatus

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

# ---------------------------------------------------------------------------
# Canonical module key for looking up the active factory.
# pytest loads this file as "conftest" (the canonical name) and test helpers
# in sub-packages may import it as "tests.conftest".  Both resolve the same
# factory by reading from sys.modules["conftest"] which is always the instance
# the fixtures run in.
# ---------------------------------------------------------------------------
_CANONICAL_MODULE = "conftest"

# Module-level factory — written and cleared by the setup_db fixture.
_current_factory: async_sessionmaker[AsyncSession] | None = None


def _get_canonical_factory() -> async_sessionmaker[AsyncSession] | None:
    """Return the active factory from the pytest-canonical module instance."""
    canonical = sys.modules.get(_CANONICAL_MODULE)
    if canonical is None:
        # Fall back to the current module if pytest has already renamed it.
        return _current_factory
    return getattr(canonical, "_current_factory", None)


class _SessionFactoryProxy:
    """Thin proxy so ``_test_session_factory()`` always calls the factory
    registered by the *current* test's ``setup_db`` fixture, regardless of
    which of the two possible module objects the proxy lives in."""

    def __call__(self, *args: object, **kwargs: object) -> AsyncSession:  # type: ignore[return]
        factory = _get_canonical_factory()
        assert factory is not None, (
            "_test_session_factory called before setup_db fixture ran; "
            "make sure your test or its fixtures depend on setup_db."
        )
        return factory(*args, **kwargs)  # type: ignore[return-value]


_test_session_factory = _SessionFactoryProxy()


@pytest_asyncio.fixture
async def setup_db() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    """Create a fresh SQLite in-memory engine + schema for each test.

    Writes the factory to ``_current_factory`` in THIS module instance (which
    pytest registered as ``sys.modules['conftest']``), so ``_get_canonical_factory``
    always finds it via ``sys.modules['conftest']``.
    """
    global _current_factory

    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine, expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    _current_factory = factory
    yield factory
    _current_factory = None

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db(setup_db: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    async with setup_db() as session:
        yield session


# ---------------------------------------------------------------------------
# App / client factories
# ---------------------------------------------------------------------------

def _make_app(
    user_id: int = 1,
    *,
    is_moderator: bool = False,
    factory: async_sessionmaker[AsyncSession] | None = None,
):
    """Return a test FastAPI app with DB, auth, and moderator role overridden.

    The DB dependency override closes over *factory* (captured at app-build time)
    so it works regardless of which event loop drives the later HTTP request.
    Falls back to ``_get_canonical_factory()`` when factory is not supplied.
    """
    resolved: async_sessionmaker[AsyncSession] = (
        factory
        if factory is not None
        else _get_canonical_factory()  # type: ignore[assignment]
    )
    assert resolved is not None, "_make_app called before setup_db fixture ran."

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with resolved() as session:
            yield session

    application = create_app()
    application.dependency_overrides[get_db] = _override_get_db
    application.dependency_overrides[get_current_user_id] = lambda: user_id
    application.dependency_overrides[get_is_moderator] = lambda: is_moderator
    return application


@pytest_asyncio.fixture
def app(request, setup_db: async_sessionmaker[AsyncSession]):
    """App fixture; override user/role via @pytest.mark.user_id(N).

    Depends on setup_db explicitly so the DB is always ready before the app is
    built, and the factory is captured correctly in the closure.
    """
    marker = request.node.get_closest_marker("user_id")
    uid = marker.args[0] if marker else 1
    return _make_app(uid, factory=setup_db)


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# DB helper factories (shared across test modules)
# ---------------------------------------------------------------------------

async def make_discussion(
    db: AsyncSession,
    *,
    author_id: int = 1,
    status: DiscussionStatus = DiscussionStatus.OPEN,
    is_hidden: bool = False,
) -> Discussion:
    d = Discussion(
        title="Test Discussion",
        body="Body text",
        author_id=author_id,
        status=status,
        is_hidden=is_hidden,
    )
    db.add(d)
    await db.commit()
    await db.refresh(d)
    return d


async def make_reply(
    db: AsyncSession,
    discussion: Discussion,
    *,
    author_id: int = 1,
    body: str = "Test reply body",
    status: ReplyStatus = ReplyStatus.VISIBLE,
    is_hidden: bool = False,
) -> Reply:
    """Create and persist a Reply for use in tests."""
    r = Reply(
        discussion_id=discussion.id,
        author_id=author_id,
        body=body,
        status=status,
        is_hidden=is_hidden,
    )
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return r
