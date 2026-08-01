# Implementation Report

---

## Phase 1/3

Two remaining issues: the router has a docstring before imports (E402), and B008 ignore isn't being picked up (the config file is in `backend/`, but ruff is called from repo root). Let me check where ruff looks for config and fix the router docstring + isinstance issue:

---

## Phase 2/3

Now run the tests:

---

## Phase 3/3

Now run mypy on the changed files:

## Verification
- `python3 -c "import os; files=[]; [files.extend([os.path.join(r,f) for f in fs]) for r,ds,fs in os.walk('backend')]; print('\n'.join(sorted(files)))"` → exit 0
- `python3 -c "import os; files=[]; [files.extend([os.path.join(r,f) for f in fs]) for r,ds,fs in os.walk('.')]; print('\n'.join(sorted(f for f in files if not f.startswith('./.git'))))"` → exit 0
- `python3 -c "
import os, pathlib
# Create the __init__.py files we can't write via tool due to collision detection
for p in [
    'backend/app/services/discussion/__init__.py',
    'backend/app/routers/__init__.py',
    'backend/tests/__init__.py',
    'backend/tests/services/__init__.py',
    'backend/tests/routers/__init__.py',
]:
    pathlib.Path(p).parent.mkdir(parents=True, exist_ok=True)
    if not pathlib.Path(p).exists():
        pathlib.Path(p).write_text('# package\n')
        print(f'created {p}')
    else:
        print(f'exists  {p}')
"` → exit 0
- `pip install -e "backend[dev]" --quiet` → exit 0
- `ruff check backend/app backend/tests` → exit 1
- `ruff check backend/app backend/tests --fix` → exit 1
- `ruff check backend/app backend/tests` → exit 1
- `ruff check backend/app backend/tests --fix` → exit 1
- `ruff check backend/app backend/tests --fix` → exit 1
- `pip install -e ".[dev]" -q` → exit 0
- `python -m pytest tests/ -x -q 2>&1` → exit 4
- `python -m pytest tests/ -x -q` → exit 1
- `python -m pytest tests/ -x -q` → exit 1
- `python -m pytest tests/ -x -q` → exit 1
- `python -m pytest tests/ -x -q` → exit 1
- `python -m pytest tests/ -x -q` → exit 1
- `python -m pytest tests/ -x -q` → exit 1
- `python -m pytest tests/routers/test_reply_router.py::test_create_reply_returns_201 -x -v --co` → exit 0
- `python -c "import pytest_asyncio; print(pytest_asyncio.__version__)"` → exit 0
- `python -c "import inspect, pytest_asyncio.plugin as p; src=inspect.getsource(p); print(src[src.find('asyncio_default'):src.find('asyncio_default')+200])"` → exit 0
- `python -m pytest tests/ -x -q` → exit 1
- `python -m pytest tests/routers/test_reply_router.py::test_create_reply_returns_201 -x -v -s` → exit 1
- `python -m pytest tests/ -x -q` → exit 1
- `python -m pytest tests/routers/test_reply_router.py::test_create_reply_returns_201 -x -v -s --fixtures-per-test` → exit 0
- `python -c "
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import DeclarativeBase
import sqlalchemy as sa

class Base(DeclarativeBase): pass

class T(Base):
    __tablename__ = 'test_t'
    id: sa.orm.Mapped[int] = sa.orm.mapped_column(sa.Integer, primary_key=True)

engine = create_async_engine('sqlite+aiosqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
factory = async_sessionmaker(engine, expire_on_commit=False)

async def run():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with factory() as s:
        s.add(T(id=1))
        await s.commit()
    async with factory() as s:
        r = await s.execute(sa.select(T))
        print('rows:', r.scalars().all())

asyncio.run(run())
"` → exit 0
- `python -m pytest tests/ -x -q` → exit 1
- `python -m pytest tests/ -x -q` → exit 1
- `python -m pytest tests/ -x -q` → exit 1
- `python -m pytest tests/ -x -q` → exit 1
- `python -m pytest tests/ -x -q` → exit 1
- `pip install -e ".[dev]" -q` → exit 0
- `python -m pytest tests/ -v --tb=short 2>&1` → exit 4
- `python -m pytest tests/ -v --tb=short` → exit 1
- `python -m pytest tests/ -v --tb=long -x` → exit 1
- `python -m pytest tests/ -v --tb=short` → exit 1
- `python -m pytest tests/ -v --tb=short -q` → exit 1
- `python -m pytest tests/ -v --tb=short` → exit 1
- `python -m pytest tests/routers/test_reply_router.py::test_create_reply_returns_201 -v --tb=long -s` → exit 1
- `python -m pytest tests/routers/test_reply_router.py -v --tb=short` → exit 1
- `python -c "
import asyncio
import pytest_asyncio
print('pytest-asyncio version:', pytest_asyncio.__version__)
"` → exit 0
- `python -c "
# Quick test: does asyncio.get_event_loop() inside an async function return the running loop?
import asyncio

async def check():
    running = asyncio.get_running_loop()
    current = asyncio.get_event_loop()
    print('running loop id:', id(running))
    print('current loop id:', id(current))
    print('same?', running is current)

asyncio.run(check())
"` → exit 0
- `python -m pytest tests/routers/test_reply_router.py --collect-only -q` → exit 0
- `python -m pytest tests/routers/test_reply_router.py::test_create_reply_unknown_discussion_returns_404 -v --tb=short` → exit 0
- `python -m pytest tests/routers/test_reply_router.py::test_create_reply_returns_201 -v --tb=long` → exit 1
- `python -c "
import sys
sys.path.insert(0, '.')
import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

TEST_DB_URL = 'sqlite+aiosqlite:///:memory:'
_factory_by_loop = {}

async def fixture_body():
    loop = asyncio.get_event_loop()
    print('fixture loop id:', id(loop), 'running:', loop.is_running())
    engine = create_async_engine(TEST_DB_URL, connect_args={'check_same_thread': False}, poolclass=StaticPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    _factory_by_loop[id(loop)] = factory
    return loop

async def test_body(fixture_loop):
    loop = asyncio.get_event_loop()
    print('test loop id:', id(loop), 'running:', loop.is_running())
    print('factory available:', id(loop) in _factory_by_loop)
    print('same loop?', id(loop) == id(fixture_loop))

# Simulate different loops
loop1 = asyncio.new_event_loop()
fixture_loop = loop1.run_until_complete(fixture_body())

loop2 = asyncio.new_event_loop()
loop2.run_until_complete(test_body(fixture_loop))
"` → exit 0
- `python -m pytest tests/routers/test_reply_router.py -v --tb=short -o "asyncio_default_fixture_loop_scope=session"` → exit 1
- `python -c "
# Test that with session-scoped pytest-asyncio, the same event loop is used
# For now just check that get_event_loop returns same object in sequential async calls
import asyncio

_loop_ids = []

async def first():
    _loop_ids.append(id(asyncio.get_event_loop()))

async def second():
    _loop_ids.append(id(asyncio.get_event_loop()))

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(first())
loop.run_until_complete(second())
print('Both same loop?', _loop_ids[0] == _loop_ids[1])
print('IDs:', _loop_ids)
"` → exit 0
- `python -m pytest tests/routers/test_reply_router.py::test_create_reply_unknown_discussion_returns_404 -v --tb=long -o "asyncio_default_fixture_loop_scope=session" -s` → exit 1
- `python -m pytest tests/routers/test_reply_router.py -v --tb=short` → exit 1
- `python -m pytest tests/routers/test_reply_router.py::test_create_reply_returns_201 -v --tb=long -s -o "asyncio_default_fixture_loop_scope=session"` → exit 1
- `python -c "
import sys
sys.path.insert(0, 'tests')
sys.path.insert(0, '.')

# Simulate what pytest does: does setup_db run before the test body?
# The app fixture is SYNC, and depends on setup_db which is ASYNC.
# In pytest-asyncio 0.24, a SYNC fixture that depends on an ASYNC fixture:
# the async fixture runs in the session event loop, and the sync fixture
# runs synchronously after.

# Key question: does pytest-asyncio treat 'app' as running in the same
# context as 'setup_db' (async fixture)?

# Let's just check: if app is sync and setup_db is async, does setup_db
# set global state before app's body runs?
print('The app fixture is a SYNC fixture depending on an ASYNC fixture (setup_db).')
print('pytest-asyncio must complete setup_db (up to yield) before app runs.')
print('So _current_factory should be set when app runs.')
print('Unless: the test body async context is created BEFORE setup_db starts.')
"` → exit 0
- `python -c "
# Write a minimal test file to check fixture ordering
import subprocess, sys, os, textwrap, tempfile, pathlib

test_code = '''
from __future__ import annotations
import pytest
import pytest_asyncio

_value = None

@pytest_asyncio.fixture
async def my_fixture():
    global _value
    print(f'FIXTURE: setting _value')
    _value = 'set'
    yield 'the_value'
    _value = None
    print(f'FIXTURE: cleared _value')

@pytest_asyncio.fixture
def sync_fixture(my_fixture):
    print(f'SYNC FIXTURE: _value={_value!r}')
    return my_fixture

@pytest_asyncio.fixture
async def client_fixture(sync_fixture):
    yield sync_fixture

async def test_thing(client_fixture):
    print(f'TEST: _value={_value!r}')
    assert _value == 'set', f\"Expected 'set', got {_value!r}\"
'''

tmpdir = tempfile.mkdtemp()
conftest = pathlib.Path(tmpdir) / 'test_order.py'
conftest.write_text(test_code)

ini = pathlib.Path(tmpdir) / 'pytest.ini'
ini.write_text('[pytest]\nasyncio_mode = auto\nasyncio_default_fixture_loop_scope = function\n')

result = subprocess.run(
    [sys.executable, '-m', 'pytest', str(conftest), '-v', '-s', '--tb=short'],
    capture_output=True, text=True
)
print('STDOUT:', result.stdout[-2000:])
print('STDERR:', result.stderr[-500:])
"` → exit 0
- `python -c "
import subprocess, sys, tempfile, pathlib

test_code = '''
from __future__ import annotations
import pytest
import pytest_asyncio

_value = None

@pytest_asyncio.fixture
async def my_fixture():
    global _value
    print(f'CONFTEST: setting _value, id(module)={id(__import__(\"conftest\"))}')
    _value = 'set'
    yield 'the_value'
    _value = None

def get_value():
    return _value
'''

test_file = '''
from conftest import _value, get_value
import pytest

async def test_thing(my_fixture):
    import conftest
    print(f'TEST: _value from module={_value!r}')
    print(f'TEST: get_value()={get_value()!r}')
    # Are they the same module?
    import sys
    mod_keys = [k for k in sys.modules if 'conftest' in k]
    print(f'conftest modules in sys.modules: {mod_keys}')
'''

tmpdir = tempfile.mkdtemp()
conftest_path = pathlib.Path(tmpdir) / 'conftest.py'
conftest_path.write_text(test_code)
test_path = pathlib.Path(tmpdir) / 'test_me.py'
test_path.write_text(test_file)
ini_path = pathlib.Path(tmpdir) / 'pytest.ini'
ini_path.write_text('[pytest]\nasyncio_mode = auto\nasyncio_default_fixture_loop_scope = function\n')

result = subprocess.run(
    [sys.executable, '-m', 'pytest', str(test_path), '-v', '-s', '--tb=short'],
    capture_output=True, text=True
)
print('STDOUT:', result.stdout[-3000:])
"` → exit 0
- `python -c "
import subprocess, sys, tempfile, pathlib

conftest_code = '''
from __future__ import annotations
import pytest
import pytest_asyncio

_current_factory = None

class _Proxy:
    def __call__(self):
        assert _current_factory is not None, f'factory is None!'
        return _current_factory()

_test_session_factory = _Proxy()

@pytest_asyncio.fixture
async def setup_db():
    global _current_factory
    print(f'SETUP_DB: setting factory')
    _current_factory = lambda: 42
    yield _current_factory
    _current_factory = None
    print(f'SETUP_DB: cleared factory')

@pytest_asyncio.fixture
def app(setup_db):
    print(f'APP: _current_factory={_current_factory!r}')
    return 'app_object'

@pytest_asyncio.fixture
async def client(app):
    yield app
'''

test_code = '''
from __future__ import annotations
from conftest import _test_session_factory

async def test_thing(client):
    print(f'TEST: calling _test_session_factory()')
    result = _test_session_factory()
    print(f'TEST: got {result}')
    assert result == 42
'''

tmpdir = tempfile.mkdtemp()
pathlib.Path(tmpdir, 'conftest.py').write_text(conftest_code)
pathlib.Path(tmpdir, 'test_it.py').write_text(test_code)
pathlib.Path(tmpdir, 'pytest.ini').write_text('[pytest]\nasyncio_mode = auto\nasyncio_default_fixture_loop_scope = function\n')

result = subprocess.run(
    [sys.executable, '-m', 'pytest', str(pathlib.Path(tmpdir, 'test_it.py')), '-v', '-s', '--tb=short'],
    capture_output=True, text=True
)
print(result.stdout[-2000:])
"` → exit 0
- `python -c "
import subprocess, sys, tempfile, pathlib

tmpdir = pathlib.Path(tempfile.mkdtemp())
(tmpdir / 'tests').mkdir()

conftest_code = '''
from __future__ import annotations
import pytest
import pytest_asyncio

_current_factory = None

class _Proxy:
    def __call__(self):
        assert _current_factory is not None, f'factory is None!'
        return _current_factory()

_test_session_factory = _Proxy()

@pytest_asyncio.fixture
async def setup_db():
    global _current_factory
    _current_factory = lambda: 42
    yield _current_factory
    _current_factory = None

@pytest_asyncio.fixture
def app(setup_db):
    return 'app_object'

@pytest_asyncio.fixture
async def client(app):
    yield app
'''

test_code = '''
from __future__ import annotations
from tests.conftest import _test_session_factory

async def test_thing(client):
    result = _test_session_factory()
    assert result == 42
'''

(tmpdir / 'tests' / 'conftest.py').write_text(conftest_code)
(tmpdir / 'tests' / 'test_it.py').write_text(test_code)
(tmpdir / 'pytest.ini').write_text('[pytest]\nasyncio_mode = auto\nasyncio_default_fixture_loop_scope = function\ntestpaths = tests\n')

result = subprocess.run(
    [sys.executable, '-m', 'pytest', str(tmpdir / 'tests' / 'test_it.py'), '-v', '-s', '--tb=short'],
    capture_output=True, text=True, cwd=str(tmpdir)
)
print(result.stdout[-2000:])
print('STDERR:', result.stderr[-500:])
"` → exit 0
- `python -m pytest tests/routers/test_reply_router.py -v --tb=short` → exit 0
- `python -m pytest tests/ -v --tb=short` → exit 1
- `python -m pytest tests/ -v --tb=short` → exit 4
- `python -m pytest tests/ -v --tb=short` → exit 0
- `python -m ruff check app/ tests/` → exit 1
- `python -m ruff check app/services/discussion/replies.py tests/conftest.py` → exit 1
- `python -m ruff check --fix app/services/discussion/replies.py tests/conftest.py` → exit 0
- `python -m ruff check app/services/discussion/replies.py tests/conftest.py` → exit 1
- `python -m ruff check app/services/discussion/replies.py tests/conftest.py` → exit 0
- `python -m mypy app/services/discussion/replies.py tests/conftest.py --ignore-missing-imports` → exit 1

## Generated Files

### `backend/.env.example`
```text
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/discussion_dev
SECRET_KEY=change-me-in-production-min-32-chars-long!!
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

```

### `backend/alembic.ini`
```text
# Alembic configuration for discussion-api
# See https://alembic.sqlalchemy.org/en/latest/tutorial.html

[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

# URL is overridden in env.py via pydantic-settings
sqlalchemy.url = postgresql+asyncpg://postgres:postgres@localhost:5432/discussion_dev

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S

```

### `backend/alembic/env.py`
```python
from __future__ import annotations

"""Alembic env.py — async SQLAlchemy 2.0 pattern."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.core.database import Base

# Import models so Alembic sees them in Base.metadata
import app.models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    return get_settings().database_url


def run_migrations_offline() -> None:
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: object) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)  # type: ignore[arg-type]
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = create_async_engine(get_url())
    async with engine.connect() as conn:
        await conn.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

```

### `backend/alembic/script.py.mako`
```text
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from __future__ import annotations

from collections.abc import Sequence

import alembic.op as op
import sqlalchemy as sa

revision: str = ${repr(up_revision)}
down_revision: str | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}

```

### `backend/alembic/versions/0001_initial.py`
```python
"""Initial schema — discussions and replies tables.

Revision ID: 0001_initial
Revises: None
Create Date: 2025-01-01 00:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enums
    discussionstatus = sa.Enum("open", "locked", "hidden", name="discussionstatus")
    replystatus = sa.Enum("visible", "hidden", name="replystatus")
    discussionstatus.create(op.get_bind(), checkfirst=True)
    replystatus.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "discussions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("open", "locked", "hidden", name="discussionstatus"),
            nullable=False,
            server_default="open",
        ),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_discussions_id", "discussions", ["id"])
    op.create_index("ix_discussions_author_id", "discussions", ["author_id"])

    op.create_table(
        "replies",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "discussion_id",
            sa.Integer(),
            sa.ForeignKey("discussions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("visible", "hidden", name="replystatus"),
            nullable=False,
            server_default="visible",
        ),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_replies_id", "replies", ["id"])
    op.create_index("ix_replies_discussion_id", "replies", ["discussion_id"])
    op.create_index("ix_replies_author_id", "replies", ["author_id"])


def downgrade() -> None:
    op.drop_table("replies")
    op.drop_table("discussions")
    op.execute("DROP TYPE IF EXISTS replystatus")
    op.execute("DROP TYPE IF EXISTS discussionstatus")

```

### `backend/app/__init__.py`
```python
# app package

```

### `backend/app/core/__init__.py`
```python
# core package

```

### `backend/app/core/config.py`
```python
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/discussion_dev"

    # JWT
    secret_key: str = "change-me-in-production-min-32-chars-long!!"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Reply limits
    reply_min_length: int = 1
    reply_max_length: int = 10_000


@lru_cache
def get_settings() -> Settings:
    return Settings()

```

### `backend/app/core/database.py`
```python
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _make_engine() -> tuple[
    "create_async_engine.__class__",  # type: ignore[name-defined]
    async_sessionmaker[AsyncSession],
]:
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return engine, session_factory


_engine, _session_factory = _make_engine()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _session_factory() as session:
        yield session

```

### `backend/app/core/exception_handlers.py`
```python
from __future__ import annotations

"""Global exception handlers registered on the canonical FastAPI app."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.services.discussion.exceptions import (
    DiscussionHiddenError,
    DiscussionLockedError,
    DiscussionNotFoundError,
    ReplyBodyTooLongError,
    ReplyBodyTooShortError,
    ReplyForbiddenError,
    ReplyHiddenError,
    ReplyNotFoundError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DiscussionNotFoundError)
    async def discussion_not_found(
        _request: Request, exc: DiscussionNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Discussion not found."})

    @app.exception_handler(DiscussionLockedError)
    async def discussion_locked(
        _request: Request, exc: DiscussionLockedError
    ) -> JSONResponse:
        # AC-010.2: locked thread → 423 Locked
        return JSONResponse(
            status_code=423,
            content={"detail": "This discussion is locked and no longer accepts replies."},
        )

    @app.exception_handler(DiscussionHiddenError)
    async def discussion_hidden(
        _request: Request, exc: DiscussionHiddenError
    ) -> JSONResponse:
        # Opaque 404 — never reveal hidden status to non-moderators (AC-012.3)
        return JSONResponse(status_code=404, content={"detail": "Discussion not found."})

    @app.exception_handler(ReplyNotFoundError)
    async def reply_not_found(_request: Request, exc: ReplyNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Reply not found."})

    @app.exception_handler(ReplyForbiddenError)
    async def reply_forbidden(_request: Request, exc: ReplyForbiddenError) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"detail": "You are not authorised to modify this reply."},
        )

    @app.exception_handler(ReplyHiddenError)
    async def reply_hidden(_request: Request, exc: ReplyHiddenError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Reply not found."})

    @app.exception_handler(ReplyBodyTooShortError)
    async def reply_too_short(
        _request: Request, exc: ReplyBodyTooShortError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(ReplyBodyTooLongError)
    async def reply_too_long(_request: Request, exc: ReplyBodyTooLongError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

```

### `backend/app/core/security.py`
```python
from __future__ import annotations

from datetime import datetime, timezone

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import Settings, get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(data: dict[str, object], settings: Settings) -> str:
    from datetime import timedelta

    payload = data.copy()
    expire = _utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload["exp"] = expire
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


async def get_current_user_id(
    token: str = Depends(oauth2_scheme),
    settings: Settings = Depends(get_settings),
) -> int:
    """Return the authenticated user's integer ID from the JWT, or raise 401."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        sub: str | None = payload.get("sub")
        if sub is None:
            raise credentials_exception
        return int(sub)
    except (JWTError, ValueError):
        raise credentials_exception


async def get_is_moderator(
    token: str = Depends(oauth2_scheme),
    settings: Settings = Depends(get_settings),
) -> bool:
    """Return True when the JWT carries role=moderator (AC-013.3).

    Missing or invalid tokens are treated as non-moderator (False) rather than
    raising 401, because listing endpoints are readable without elevated rights.
    Token validation still uses the same secret so forged tokens cannot elevate privilege.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return str(payload.get("role", "")).lower() == "moderator"
    except (JWTError, ValueError):
        return False

```

### `backend/app/main.py`
```python
from __future__ import annotations

"""Canonical ASGI entrypoint — one app, one router chain."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.routers.reply_router import router as replies_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Validate settings at startup; fail fast on misconfiguration.
    get_settings()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Discussion API",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    app.include_router(replies_router, prefix="/api/v1")

    @app.get("/healthz", tags=["ops"], include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

```

### `backend/app/models/__init__.py`
```python
from app.models.discussion import Discussion, Reply

__all__ = ["Discussion", "Reply"]

```

### `backend/app/models/discussion.py`
```python
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import DiscussionStatus, ReplyStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Discussion(Base):
    """Top-level discussion thread."""

    __tablename__ = "discussions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    status: Mapped[DiscussionStatus] = mapped_column(
        Enum(DiscussionStatus, name="discussionstatus"),
        nullable=False,
        default=DiscussionStatus.OPEN,
        server_default=DiscussionStatus.OPEN.value,
    )
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    replies: Mapped[list["Reply"]] = relationship(
        "Reply", back_populates="discussion", cascade="all, delete-orphan"
    )

    @property
    def is_locked(self) -> bool:
        return self.status == DiscussionStatus.LOCKED


class Reply(Base):
    """A single reply within a discussion thread."""

    __tablename__ = "replies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    discussion_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("discussions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ReplyStatus] = mapped_column(
        Enum(ReplyStatus, name="replystatus"),
        nullable=False,
        default=ReplyStatus.VISIBLE,
        server_default=ReplyStatus.VISIBLE.value,
    )
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    discussion: Mapped["Discussion"] = relationship("Discussion", back_populates="replies")

```

### `backend/app/models/enums.py`
```python
from __future__ import annotations

import enum


class DiscussionStatus(str, enum.Enum):
    """Lifecycle status of a top-level discussion thread."""

    OPEN = "open"
    LOCKED = "locked"   # No new replies allowed (AC-012)
    HIDDEN = "hidden"   # Not surfaced in listings (AC-013)


class ReplyStatus(str, enum.Enum):
    """Visibility/moderation status of a single reply."""

    VISIBLE = "visible"
    HIDDEN = "hidden"   # Soft-hidden by moderator (AC-013)

```

### `backend/app/routers/reply_router.py`
```python
from __future__ import annotations

# Reply HTTP router — mounts under /api/v1/discussions/{discussion_id}/replies
# POST /              → create reply (AC-010 length, AC-012 lock/hide)
# GET  /              → list replies (AC-012.3 hide-state filtering)
# PATCH /{reply_id}   → edit own reply (AC-013.2 auth, AC-013.3 moderator)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import get_current_user_id, get_is_moderator
from app.services.discussion import replies as reply_service
from app.services.discussion.exceptions import (
    DiscussionHiddenError,
    DiscussionLockedError,
    DiscussionNotFoundError,
    ReplyBodyTooLongError,
    ReplyBodyTooShortError,
    ReplyForbiddenError,
    ReplyHiddenError,
    ReplyNotFoundError,
)
from app.services.discussion.schemas import ReplyCreate, ReplyResponse, ReplyUpdate

router = APIRouter(
    prefix="/discussions/{discussion_id}/replies",
    tags=["replies"],
)


def _handle_service_error(exc: Exception) -> None:
    if isinstance(exc, DiscussionNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discussion not found.")
    if isinstance(exc, DiscussionLockedError):
        # AC-010.2: locked thread → 423 Locked
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="This discussion is locked and no longer accepts replies.",
        )
    if isinstance(exc, DiscussionHiddenError):
        # Opaque 404 — must not reveal hidden status to non-moderators (AC-012.3)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discussion not found.",
        )
    if isinstance(exc, ReplyNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reply not found.")
    if isinstance(exc, ReplyForbiddenError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorised to modify this reply.",
        )
    if isinstance(exc, ReplyHiddenError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reply not found.")
    if isinstance(exc, ReplyBodyTooShortError | ReplyBodyTooLongError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    raise exc


@router.post(
    "",
    response_model=ReplyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a reply on a discussion (AC-010, AC-012)",
)
async def create_reply(
    discussion_id: int,
    payload: ReplyCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ReplyResponse:
    try:
        reply = await reply_service.create_reply(
            db,
            discussion_id=discussion_id,
            author_id=current_user_id,
            body=payload.body,
            min_length=settings.reply_min_length,
            max_length=settings.reply_max_length,
        )
    except Exception as exc:
        _handle_service_error(exc)
    return ReplyResponse.model_validate(reply)


@router.get(
    "",
    response_model=list[ReplyResponse],
    status_code=status.HTTP_200_OK,
    summary="List visible replies for a discussion (AC-012.3 hide-state filtering)",
)
async def list_replies(
    discussion_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    is_moderator: bool = Depends(get_is_moderator),
) -> list[ReplyResponse]:
    try:
        replies_list = await reply_service.list_replies(
            db,
            discussion_id=discussion_id,
            include_hidden=is_moderator,  # AC-012.3 / AC-013.3
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        _handle_service_error(exc)
    return [ReplyResponse.model_validate(r) for r in replies_list]


@router.get(
    "/{reply_id}",
    response_model=ReplyResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a single reply",
)
async def get_reply(
    discussion_id: int,
    reply_id: int,
    db: AsyncSession = Depends(get_db),
    is_moderator: bool = Depends(get_is_moderator),
) -> ReplyResponse:
    try:
        reply = await reply_service.get_reply(
            db,
            discussion_id=discussion_id,
            reply_id=reply_id,
            include_hidden=is_moderator,
        )
    except Exception as exc:
        _handle_service_error(exc)
    return ReplyResponse.model_validate(reply)


@router.patch(
    "/{reply_id}",
    response_model=ReplyResponse,
    status_code=status.HTTP_200_OK,
    summary="Edit own reply (AC-013.2 edit authorisation)",
)
async def update_reply(
    discussion_id: int,
    reply_id: int,
    payload: ReplyUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ReplyResponse:
    try:
        reply = await reply_service.update_reply(
            db,
            discussion_id=discussion_id,
            reply_id=reply_id,
            requesting_user_id=current_user_id,
            new_body=payload.body,
            min_length=settings.reply_min_length,
            max_length=settings.reply_max_length,
        )
    except Exception as exc:
        _handle_service_error(exc)
    return ReplyResponse.model_validate(reply)

```

### `backend/app/services/__init__.py`
```python
# services package

```

### `backend/app/services/discussion/exceptions.py`
```python
from __future__ import annotations

"""Domain exceptions for the discussion/reply service.

Each exception maps to a specific HTTP status code via the global exception handler,
keeping the service layer free of FastAPI concerns.
"""


class DiscussionNotFoundError(Exception):
    def __init__(self, discussion_id: int) -> None:
        self.discussion_id = discussion_id
        super().__init__(f"Discussion {discussion_id} not found.")


class DiscussionLockedError(Exception):
    """Raised when a reply is attempted on a locked discussion (AC-012)."""

    def __init__(self, discussion_id: int) -> None:
        self.discussion_id = discussion_id
        super().__init__(f"Discussion {discussion_id} is locked and does not accept new replies.")


class DiscussionHiddenError(Exception):
    """Raised when a reply is attempted on a hidden discussion (AC-012)."""

    def __init__(self, discussion_id: int) -> None:
        self.discussion_id = discussion_id
        super().__init__(f"Discussion {discussion_id} is hidden.")


class ReplyNotFoundError(Exception):
    def __init__(self, reply_id: int) -> None:
        self.reply_id = reply_id
        super().__init__(f"Reply {reply_id} not found.")


class ReplyForbiddenError(Exception):
    """Raised when a user attempts to edit a reply they do not own (AC-013)."""

    def __init__(self, reply_id: int) -> None:
        self.reply_id = reply_id
        super().__init__(f"Not authorised to modify reply {reply_id}.")


class ReplyHiddenError(Exception):
    """Raised when editing a hidden reply is attempted."""

    def __init__(self, reply_id: int) -> None:
        self.reply_id = reply_id
        super().__init__(f"Reply {reply_id} is hidden and cannot be edited.")


class ReplyBodyTooShortError(Exception):
    def __init__(self, min_length: int) -> None:
        self.min_length = min_length
        super().__init__(f"Reply body must be at least {min_length} character(s).")


class ReplyBodyTooLongError(Exception):
    def __init__(self, max_length: int) -> None:
        self.max_length = max_length
        super().__init__(f"Reply body must not exceed {max_length} characters.")

```

### `backend/app/services/discussion/replies.py`
```python
from __future__ import annotations

# Reply service — business rules for creating, editing, and hiding replies.
# AC-010:   Reply creation with length validation.
# AC-012:   Reject replies on locked/hidden discussions.
# AC-012.3: Hidden items excluded from non-moderator views (via visibility module).
# AC-013:   Edit authorisation — only the reply author may edit.
# AC-013.2: Non-author edit raises ReplyForbiddenError → HTTP 403.
# AC-013.3: Moderators receive unfiltered result sets (include_hidden=True).
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discussion import Discussion, Reply
from app.models.enums import DiscussionStatus, ReplyStatus
from app.services.discussion.exceptions import (
    DiscussionHiddenError,
    DiscussionLockedError,
    DiscussionNotFoundError,
    ReplyBodyTooLongError,
    ReplyBodyTooShortError,
    ReplyForbiddenError,
    ReplyHiddenError,
    ReplyNotFoundError,
)
from app.services.discussion.visibility import (
    apply_reply_visibility,
    is_discussion_visible,
    is_reply_visible,
)


def _utcnow() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_discussion_or_404(
    db: AsyncSession,
    discussion_id: int,
    *,
    include_hidden: bool = True,
) -> Discussion:
    """Fetch a Discussion by PK; apply visibility filter when *include_hidden* is False.

    Raises:
        DiscussionNotFoundError: row absent.
        DiscussionHiddenError:   row is hidden and caller is not a moderator.
    """
    result = await db.execute(select(Discussion).where(Discussion.id == discussion_id))
    discussion = result.scalar_one_or_none()
    if discussion is None:
        raise DiscussionNotFoundError(discussion_id)
    if not is_discussion_visible(discussion, include_hidden=include_hidden):
        raise DiscussionHiddenError(discussion_id)
    return discussion


async def _get_reply_or_404(
    db: AsyncSession,
    reply_id: int,
    discussion_id: int,
    *,
    include_hidden: bool = True,
) -> Reply:
    """Fetch a Reply by PK scoped to *discussion_id*; apply visibility when requested.

    Raises:
        ReplyNotFoundError: row absent or (when include_hidden=False) hidden.
    """
    result = await db.execute(
        select(Reply).where(Reply.id == reply_id, Reply.discussion_id == discussion_id)
    )
    reply = result.scalar_one_or_none()
    if reply is None:
        raise ReplyNotFoundError(reply_id)
    if not is_reply_visible(reply, include_hidden=include_hidden):
        raise ReplyNotFoundError(reply_id)
    return reply


def _assert_discussion_accepts_replies(discussion: Discussion) -> None:
    """AC-012: Raise if the discussion is locked or hidden."""
    if discussion.status == DiscussionStatus.LOCKED:
        raise DiscussionLockedError(discussion.id)
    if discussion.is_hidden or discussion.status == DiscussionStatus.HIDDEN:
        raise DiscussionHiddenError(discussion.id)


def _assert_reply_visible_for_edit(reply: Reply) -> None:
    """Prevent editing a hidden reply — service guard independent of caller role."""
    if reply.is_hidden or reply.status == ReplyStatus.HIDDEN:
        raise ReplyHiddenError(reply.id)


def _assert_is_author(reply: Reply, user_id: int) -> None:
    """AC-013.2: Raise ReplyForbiddenError (→ 403) when caller is not the reply author."""
    if reply.author_id != user_id:
        raise ReplyForbiddenError(reply.id)


def _validate_body(body: str, min_length: int, max_length: int) -> None:
    """Programmatic length guard (mirrors Pydantic schema validation for service-layer callers)."""
    stripped = body.strip()
    if len(stripped) < min_length:
        raise ReplyBodyTooShortError(min_length)
    if len(body) > max_length:
        raise ReplyBodyTooLongError(max_length)


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


async def create_reply(
    db: AsyncSession,
    *,
    discussion_id: int,
    author_id: int,
    body: str,
    min_length: int = 1,
    max_length: int = 10_000,
) -> Reply:
    """Create a new reply on a discussion.

    Raises:
        DiscussionNotFoundError: discussion does not exist.
        DiscussionLockedError:   discussion is locked (AC-012) → 423.
        DiscussionHiddenError:   discussion is hidden (AC-012) → 404.
        ReplyBodyTooShortError:  body is empty/blank (AC-010).
        ReplyBodyTooLongError:   body exceeds max_length (AC-010).
    """
    _validate_body(body, min_length, max_length)

    discussion = await _get_discussion_or_404(db, discussion_id)
    _assert_discussion_accepts_replies(discussion)  # AC-012

    reply = Reply(
        discussion_id=discussion_id,
        author_id=author_id,
        body=body,
        status=ReplyStatus.VISIBLE,
        is_hidden=False,
    )
    db.add(reply)
    await db.commit()
    await db.refresh(reply)
    return reply


async def update_reply(
    db: AsyncSession,
    *,
    discussion_id: int,
    reply_id: int,
    requesting_user_id: int,
    new_body: str,
    min_length: int = 1,
    max_length: int = 10_000,
) -> Reply:
    """Edit an existing reply.

    Only the reply's own author may edit (AC-013.2).  Moderator role grants
    list/read visibility but NOT edit permission on behalf of another user.

    Raises:
        DiscussionNotFoundError: parent discussion does not exist.
        DiscussionLockedError:   discussion is locked — edits blocked (AC-012) → 423.
        ReplyNotFoundError:      reply absent in this discussion.
        ReplyHiddenError:        reply is hidden — cannot edit.
        ReplyForbiddenError:     caller is not the reply author (AC-013.2) → 403.
        ReplyBodyTooShortError / ReplyBodyTooLongError: length validation (AC-010).
    """
    _validate_body(new_body, min_length, max_length)

    discussion = await _get_discussion_or_404(db, discussion_id)
    _assert_discussion_accepts_replies(discussion)  # locked threads block edits too

    # Fetch reply without visibility filter — hidden replies exist but cannot be edited
    result = await db.execute(
        select(Reply).where(Reply.id == reply_id, Reply.discussion_id == discussion_id)
    )
    reply = result.scalar_one_or_none()
    if reply is None:
        raise ReplyNotFoundError(reply_id)

    _assert_reply_visible_for_edit(reply)         # hidden → 404
    _assert_is_author(reply, requesting_user_id)  # AC-013.2: non-author → 403

    reply.body = new_body
    reply.updated_at = _utcnow()
    await db.commit()
    await db.refresh(reply)
    return reply


async def get_reply(
    db: AsyncSession,
    *,
    discussion_id: int,
    reply_id: int,
    include_hidden: bool = False,
) -> Reply:
    """Fetch a single reply.

    Args:
        include_hidden: When True (moderator) hidden replies are returned.
                        When False (default) a hidden reply raises ReplyNotFoundError.

    Raises:
        DiscussionNotFoundError: parent discussion absent.
        ReplyNotFoundError:      reply absent or hidden (when include_hidden=False).
    """
    # AC-012.3: a non-moderator must not be able to read replies on a hidden discussion.
    await _get_discussion_or_404(db, discussion_id, include_hidden=include_hidden)
    return await _get_reply_or_404(db, reply_id, discussion_id, include_hidden=include_hidden)


async def list_replies(
    db: AsyncSession,
    *,
    discussion_id: int,
    include_hidden: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[Reply]:
    """Return paginated replies for a discussion.

    AC-012.3: When include_hidden=False (non-moderator) hidden replies are excluded.
    AC-013.3: When include_hidden=True (moderator)  all replies are returned.
    AC-012.3: Hidden discussion is opaque 404 for non-moderators.

    Raises:
        DiscussionNotFoundError: parent discussion absent.
        DiscussionHiddenError:   discussion is hidden and caller is not a moderator.
    """
    # AC-012.3: hidden discussion is opaque 404 for non-moderators; moderators can list freely.
    await _get_discussion_or_404(db, discussion_id, include_hidden=include_hidden)

    stmt = select(Reply).where(Reply.discussion_id == discussion_id)
    stmt = apply_reply_visibility(stmt, include_hidden=include_hidden)
    stmt = stmt.order_by(Reply.created_at.asc()).limit(limit).offset(offset)

    result = await db.execute(stmt)
    return list(result.scalars().all())

```

### `backend/app/services/discussion/schemas.py`
```python
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.config import get_settings
from app.models.enums import ReplyStatus

_settings = get_settings()


class ReplyCreate(BaseModel):
    """Payload for POST /discussions/{id}/replies (AC-010)."""

    body: str = Field(
        ...,
        min_length=_settings.reply_min_length,
        max_length=_settings.reply_max_length,
        description="Reply text content.",
    )

    @field_validator("body")
    @classmethod
    def body_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Reply body must not be blank or whitespace only.")
        return v


class ReplyUpdate(BaseModel):
    """Payload for PATCH /discussions/{id}/replies/{reply_id} (AC-013 edit auth)."""

    body: str = Field(
        ...,
        min_length=_settings.reply_min_length,
        max_length=_settings.reply_max_length,
        description="Updated reply text content.",
    )

    @field_validator("body")
    @classmethod
    def body_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Reply body must not be blank or whitespace only.")
        return v


class ReplyResponse(BaseModel):
    """Read representation of a reply."""

    model_config = {"from_attributes": True}

    id: int
    discussion_id: int
    author_id: int
    body: str
    status: ReplyStatus
    is_hidden: bool
    created_at: datetime
    updated_at: datetime

```

### `backend/app/services/discussion/visibility.py`
```python
from __future__ import annotations

"""Visibility filtering helpers for discussions and replies.

AC-012.3: Hidden discussions/replies must be excluded from non-moderator views.
AC-013.3: Moderators receive the full unfiltered set (include_hidden=True).

These are pure filter functions operating on SQLAlchemy Select statements so
they stay decoupled from HTTP concerns and are independently testable.
"""

from sqlalchemy import Select

from app.models.discussion import Discussion, Reply
from app.models.enums import DiscussionStatus, ReplyStatus


def apply_discussion_visibility(
    stmt: Select[tuple[Discussion]],
    *,
    include_hidden: bool,
) -> Select[tuple[Discussion]]:
    """Restrict a Discussion query to visible rows unless caller is a moderator.

    - Excludes rows where ``Discussion.is_hidden`` is True.
    - Excludes rows where ``Discussion.status == DiscussionStatus.HIDDEN``.

    Args:
        stmt: An existing ``select(Discussion)`` statement to filter.
        include_hidden: When True (moderator path) no filter is applied.

    Returns:
        The (possibly filtered) statement.
    """
    if include_hidden:
        return stmt
    return stmt.where(
        Discussion.is_hidden.is_(False),
        Discussion.status != DiscussionStatus.HIDDEN,
    )


def apply_reply_visibility(
    stmt: Select[tuple[Reply]],
    *,
    include_hidden: bool,
) -> Select[tuple[Reply]]:
    """Restrict a Reply query to visible rows unless caller is a moderator.

    - Excludes rows where ``Reply.is_hidden`` is True.
    - Excludes rows where ``Reply.status == ReplyStatus.HIDDEN``.

    Args:
        stmt: An existing ``select(Reply)`` statement to filter.
        include_hidden: When True (moderator path) no filter is applied.

    Returns:
        The (possibly filtered) statement.
    """
    if include_hidden:
        return stmt
    return stmt.where(
        Reply.is_hidden.is_(False),
        Reply.status == ReplyStatus.VISIBLE,
    )


def is_discussion_visible(discussion: Discussion, *, include_hidden: bool) -> bool:
    """Return True when *discussion* should be surfaced to the caller.

    Used for single-object checks after a fetch (e.g. get-by-id paths).
    """
    if include_hidden:
        return True
    return not discussion.is_hidden and discussion.status != DiscussionStatus.HIDDEN


def is_reply_visible(reply: Reply, *, include_hidden: bool) -> bool:
    """Return True when *reply* should be surfaced to the caller."""
    if include_hidden:
        return True
    return not reply.is_hidden and reply.status == ReplyStatus.VISIBLE

```

### `backend/pyproject.toml`
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "discussion-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi==0.115.5",
    "uvicorn[standard]==0.32.1",
    "sqlalchemy[asyncio]==2.0.36",
    "alembic==1.14.0",
    "asyncpg==0.30.0",
    "pydantic==2.10.3",
    "pydantic-settings==2.6.1",
    "python-jose[cryptography]==3.3.0",
    "passlib[bcrypt]==1.7.4",
    "python-multipart==0.0.19",
    "httpx==0.28.1",
]

[project.optional-dependencies]
dev = [
    "pytest==8.3.4",
    "pytest-asyncio==0.24.0",
    "pytest-cov==6.0.0",
    "anyio[trio]==4.7.0",
    "aiosqlite==0.20.0",
    "ruff==0.8.4",
    "mypy==1.13.0",
    "types-python-jose==3.3.4.20240106",
    "types-passlib==1.7.7.20240819",
]

[tool.hatch.build.targets.wheel]
packages = ["app"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
# "function" scope gives each test its own event loop.  The per-test setup_db
# fixture uses aiosqlite which binds its background thread to the creating loop;
# a session-scoped loop clears _test_session_factory._current between tests and
# breaks any test that calls _test_session_factory() after the first teardown.
# (VER-004)
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
markers = [
    "user_id(n): override the authenticated user_id injected into the test-app fixture",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "C4", "SIM"]
# B008: Depends() in defaults is idiomatic FastAPI — not a defect
ignore = ["E501", "B008"]

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true
plugins = ["pydantic.mypy"]

```

### `backend/tests/conftest.py`
```python
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

```

### `backend/tests/routers/test_reply_router.py`
```python
from __future__ import annotations

# HTTP integration tests for the reply router.
# AC-010 (creation/length), AC-010.2/VER-002 (lock-state 423), AC-012 (hidden-state 404),
# AC-013 (edit auth 403)
# Uses HTTPX ASGITransport + SQLite in-memory DB via conftest overrides.

import pytest
from httpx import ASGITransport
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.models.discussion import Discussion
from app.models.enums import DiscussionStatus
from tests.conftest import _make_app, _test_session_factory, make_discussion


# ─── POST /api/v1/discussions/{id}/replies ─────────────────────────────────


@pytest.mark.asyncio
async def test_create_reply_returns_201(client: AsyncClient) -> None:
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)

    resp = await client.post(
        f"/api/v1/discussions/{discussion.id}/replies",
        json={"body": "Great post!"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["body"] == "Great post!"
    assert data["author_id"] == 1  # default fixture user
    assert data["status"] == "visible"
    assert data["is_hidden"] is False


@pytest.mark.asyncio
async def test_create_reply_blank_body_returns_422(client: AsyncClient) -> None:
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)

    resp = await client.post(
        f"/api/v1/discussions/{discussion.id}/replies",
        json={"body": "   "},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_reply_unknown_discussion_returns_404(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/discussions/9999/replies", json={"body": "Hi"})
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.user_id(1)
async def test_create_reply_locked_discussion_returns_423(client: AsyncClient) -> None:
    # AC-010.2 / VER-002: Locked discussion → 423 Locked
    async with _test_session_factory() as db:
        discussion = await make_discussion(db, status=DiscussionStatus.LOCKED)

    resp = await client.post(
        f"/api/v1/discussions/{discussion.id}/replies",
        json={"body": "Trying to reply"},
    )
    assert resp.status_code == 423
    assert "locked" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_reply_hidden_discussion_returns_404(client: AsyncClient) -> None:
    # AC-012: Hidden discussion → opaque 404 (must not disclose hidden status)
    async with _test_session_factory() as db:
        discussion = await make_discussion(db, status=DiscussionStatus.HIDDEN)

    resp = await client.post(
        f"/api/v1/discussions/{discussion.id}/replies",
        json={"body": "Trying to reply"},
    )
    assert resp.status_code == 404
    assert "hidden" not in resp.json()["detail"].lower()


# ─── PATCH /api/v1/discussions/{id}/replies/{reply_id} ─────────────────────


@pytest.mark.asyncio
async def test_update_reply_by_owner_returns_200(client: AsyncClient) -> None:
    # AC-013: Reply author can edit their own reply
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)

    create_resp = await client.post(
        f"/api/v1/discussions/{discussion.id}/replies",
        json={"body": "original"},
    )
    reply_id = create_resp.json()["id"]

    patch_resp = await client.patch(
        f"/api/v1/discussions/{discussion.id}/replies/{reply_id}",
        json={"body": "edited"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["body"] == "edited"


@pytest.mark.asyncio
async def test_update_reply_by_non_owner_returns_403(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    # AC-013: Non-author receives 403 Forbidden
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)

    app_user1 = _make_app(user_id=1)
    async with AsyncClient(transport=ASGITransport(app=app_user1), base_url="http://test") as c1:
        create_resp = await c1.post(
            f"/api/v1/discussions/{discussion.id}/replies",
            json={"body": "owner reply"},
        )
    reply_id = create_resp.json()["id"]

    app_user2 = _make_app(user_id=2)
    async with AsyncClient(transport=ASGITransport(app=app_user2), base_url="http://test") as c2:
        patch_resp = await c2.patch(
            f"/api/v1/discussions/{discussion.id}/replies/{reply_id}",
            json={"body": "hijack"},
        )
    assert patch_resp.status_code == 403


@pytest.mark.asyncio
async def test_update_reply_on_locked_discussion_returns_423(client: AsyncClient) -> None:
    # AC-010.2 / VER-002: Editing a reply when discussion becomes locked → 423
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)
    discussion_id = discussion.id

    create_resp = await client.post(
        f"/api/v1/discussions/{discussion_id}/replies",
        json={"body": "original"},
    )
    reply_id = create_resp.json()["id"]

    async with _test_session_factory() as db:
        result = await db.execute(select(Discussion).where(Discussion.id == discussion_id))
        d = result.scalar_one()
        d.status = DiscussionStatus.LOCKED
        await db.commit()

    patch_resp = await client.patch(
        f"/api/v1/discussions/{discussion_id}/replies/{reply_id}",
        json={"body": "edit after lock"},
    )
    assert patch_resp.status_code == 423


# ─── GET replies ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_replies_returns_200(client: AsyncClient) -> None:
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)

    await client.post(f"/api/v1/discussions/{discussion.id}/replies", json={"body": "reply 1"})
    await client.post(f"/api/v1/discussions/{discussion.id}/replies", json={"body": "reply 2"})

    resp = await client.get(f"/api/v1/discussions/{discussion.id}/replies")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_single_reply_returns_200(client: AsyncClient) -> None:
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)

    create_resp = await client.post(
        f"/api/v1/discussions/{discussion.id}/replies", json={"body": "solo"}
    )
    reply_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/discussions/{discussion.id}/replies/{reply_id}")
    assert resp.status_code == 200
    assert resp.json()["body"] == "solo"


@pytest.mark.asyncio
async def test_get_nonexistent_reply_returns_404(client: AsyncClient) -> None:
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)

    resp = await client.get(f"/api/v1/discussions/{discussion.id}/replies/9999")
    assert resp.status_code == 404

```

### `backend/tests/routers/test_visibility_router.py`
```python
from __future__ import annotations

"""HTTP integration tests for hide-state filtering and edit authorisation.

Covers:
    AC-010.2 / VER-002 — locked thread → 423 Locked
    AC-012.3           — hidden replies excluded from non-moderator list/get
    AC-013.2           — non-author edit → 403 Forbidden
    AC-013.3           — moderator sees hidden replies in list and get

All tests that create their own AsyncClient (instead of using the `client`
fixture) must declare `setup_db` as a parameter so pytest-asyncio runs the
DB setup fixture before the test body.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.models.enums import DiscussionStatus, ReplyStatus
from tests.conftest import _make_app, _test_session_factory, make_discussion, make_reply


# ─── AC-010.2 / VER-002 ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reply_to_locked_thread_returns_423(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    """VER-002: Posting a reply to a locked discussion must return 423 Locked."""
    async with _test_session_factory() as db:
        discussion = await make_discussion(db, status=DiscussionStatus.LOCKED)

    app = _make_app(user_id=1)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/discussions/{discussion.id}/replies",
            json={"body": "Trying to reply to locked thread"},
        )

    assert resp.status_code == 423, resp.text
    assert "locked" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_edit_reply_on_locked_thread_returns_423(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    """VER-002: Editing a reply while discussion is locked must also return 423."""
    async with _test_session_factory() as db:
        open_discussion = await make_discussion(db, status=DiscussionStatus.OPEN)
        reply = await make_reply(db, open_discussion, author_id=1)
        open_discussion.status = DiscussionStatus.LOCKED
        await db.commit()

    app = _make_app(user_id=1)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.patch(
            f"/api/v1/discussions/{open_discussion.id}/replies/{reply.id}",
            json={"body": "edit after lock"},
        )

    assert resp.status_code == 423, resp.text


# ─── AC-012.3: hidden replies excluded from non-moderator views ────────────


@pytest.mark.asyncio
async def test_list_replies_excludes_hidden_for_regular_user(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    """AC-012.3: Regular user does not see hidden replies in list endpoint."""
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)
        visible_r = await make_reply(db, discussion, body="visible reply")
        hidden_r = await make_reply(
            db, discussion, body="hidden reply",
            status=ReplyStatus.HIDDEN, is_hidden=True,
        )

    app = _make_app(user_id=1, is_moderator=False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(f"/api/v1/discussions/{discussion.id}/replies")

    assert resp.status_code == 200
    ids = [r["id"] for r in resp.json()]
    assert visible_r.id in ids
    assert hidden_r.id not in ids


@pytest.mark.asyncio
async def test_get_hidden_reply_returns_404_for_regular_user(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    """AC-012.3: GET on a hidden reply returns 404 for non-moderators."""
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)
        hidden_r = await make_reply(
            db, discussion, body="hidden",
            status=ReplyStatus.HIDDEN, is_hidden=True,
        )

    app = _make_app(user_id=1, is_moderator=False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            f"/api/v1/discussions/{discussion.id}/replies/{hidden_r.id}"
        )

    assert resp.status_code == 404, resp.text


# ─── AC-013.2: non-author edit → 403 ──────────────────────────────────────


@pytest.mark.asyncio
async def test_edit_reply_by_non_author_returns_403(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    """AC-013.2: A user who is not the reply author receives 403 Forbidden."""
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)
        reply = await make_reply(db, discussion, author_id=1)

    app_user2 = _make_app(user_id=2)
    async with AsyncClient(
        transport=ASGITransport(app=app_user2), base_url="http://test"
    ) as client:
        resp = await client.patch(
            f"/api/v1/discussions/{discussion.id}/replies/{reply.id}",
            json={"body": "attempted hijack"},
        )

    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_edit_reply_by_author_returns_200(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    """AC-013.2 sanity: The reply author can edit successfully."""
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)
        reply = await make_reply(db, discussion, author_id=7)

    app_owner = _make_app(user_id=7)
    async with AsyncClient(
        transport=ASGITransport(app=app_owner), base_url="http://test"
    ) as client:
        resp = await client.patch(
            f"/api/v1/discussions/{discussion.id}/replies/{reply.id}",
            json={"body": "edited by owner"},
        )

    assert resp.status_code == 200
    assert resp.json()["body"] == "edited by owner"


@pytest.mark.asyncio
async def test_moderator_cannot_edit_on_behalf_of_another_user(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    """AC-013.2: Moderator role grants visibility only — not edit on another's reply."""
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)
        reply = await make_reply(db, discussion, author_id=1)

    # Moderator is user 99 (different from author 1)
    app_mod = _make_app(user_id=99, is_moderator=True)
    async with AsyncClient(
        transport=ASGITransport(app=app_mod), base_url="http://test"
    ) as client:
        resp = await client.patch(
            f"/api/v1/discussions/{discussion.id}/replies/{reply.id}",
            json={"body": "moderator override"},
        )

    assert resp.status_code == 403, resp.text


# ─── AC-013.3: moderator receives hidden items ─────────────────────────────


@pytest.mark.asyncio
async def test_list_replies_includes_hidden_for_moderator(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    """AC-013.3: Moderator sees hidden replies in list endpoint."""
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)
        visible_r = await make_reply(db, discussion, body="visible")
        hidden_r = await make_reply(
            db, discussion, body="hidden",
            status=ReplyStatus.HIDDEN, is_hidden=True,
        )

    app_mod = _make_app(user_id=1, is_moderator=True)
    async with AsyncClient(
        transport=ASGITransport(app=app_mod), base_url="http://test"
    ) as client:
        resp = await client.get(f"/api/v1/discussions/{discussion.id}/replies")

    assert resp.status_code == 200
    ids = [r["id"] for r in resp.json()]
    assert visible_r.id in ids
    assert hidden_r.id in ids


@pytest.mark.asyncio
async def test_get_hidden_reply_returns_200_for_moderator(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    """AC-013.3: Moderator can fetch a hidden reply by ID."""
    async with _test_session_factory() as db:
        discussion = await make_discussion(db)
        hidden_r = await make_reply(
            db, discussion, body="hidden content",
            status=ReplyStatus.HIDDEN, is_hidden=True,
        )

    app_mod = _make_app(user_id=1, is_moderator=True)
    async with AsyncClient(
        transport=ASGITransport(app=app_mod), base_url="http://test"
    ) as client:
        resp = await client.get(
            f"/api/v1/discussions/{discussion.id}/replies/{hidden_r.id}"
        )

    assert resp.status_code == 200, resp.text
    assert resp.json()["body"] == "hidden content"
    assert resp.json()["is_hidden"] is True


@pytest.mark.asyncio
async def test_hidden_discussion_returns_404_for_non_moderator(
    setup_db: async_sessionmaker[AsyncSession],
) -> None:
    """AC-012.3: Hidden discussion is opaque 404 for regular users."""
    async with _test_session_factory() as db:
        hidden_d = await make_discussion(db, status=DiscussionStatus.HIDDEN)

    app = _make_app(user_id=1, is_moderator=False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(f"/api/v1/discussions/{hidden_d.id}/replies")

    assert resp.status_code == 404, resp.text
    assert "hidden" not in resp.json()["detail"].lower()

```

### `backend/tests/services/test_replies_service.py`
```python
from __future__ import annotations
# Unit tests for app.services.discussion.replies
# Covers: AC-010 (length), AC-012 (lock/hide rejection), AC-013 (edit auth)
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enums import DiscussionStatus, ReplyStatus
from app.services.discussion import replies as svc
from app.services.discussion.exceptions import (
    DiscussionHiddenError,
    DiscussionLockedError,
    DiscussionNotFoundError,
    ReplyBodyTooLongError,
    ReplyBodyTooShortError,
    ReplyForbiddenError,
    ReplyHiddenError,
    ReplyNotFoundError,
)
from tests.conftest import make_discussion


# ─── AC-010: reply creation + length validation ────────────────────────────


@pytest.mark.asyncio
async def test_create_reply_success(db: AsyncSession) -> None:
    discussion = await make_discussion(db)
    reply = await svc.create_reply(
        db, discussion_id=discussion.id, author_id=42, body="Hello world"
    )
    assert reply.id is not None
    assert reply.body == "Hello world"
    assert reply.author_id == 42
    assert reply.status == ReplyStatus.VISIBLE
    assert reply.is_hidden is False


@pytest.mark.asyncio
async def test_create_reply_blank_body_raises(db: AsyncSession) -> None:
    discussion = await make_discussion(db)
    with pytest.raises(ReplyBodyTooShortError):
        await svc.create_reply(
            db, discussion_id=discussion.id, author_id=1, body="   ", min_length=1
        )


@pytest.mark.asyncio
async def test_create_reply_body_too_long_raises(db: AsyncSession) -> None:
    discussion = await make_discussion(db)
    with pytest.raises(ReplyBodyTooLongError):
        await svc.create_reply(
            db,
            discussion_id=discussion.id,
            author_id=1,
            body="x" * 101,
            max_length=100,
        )


@pytest.mark.asyncio
async def test_create_reply_unknown_discussion_raises(db: AsyncSession) -> None:
    with pytest.raises(DiscussionNotFoundError):
        await svc.create_reply(db, discussion_id=9999, author_id=1, body="Hi")


# ─── AC-012: lock-state rejection ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_reply_on_locked_discussion_raises(db: AsyncSession) -> None:
    """AC-012: Posting a reply to a LOCKED discussion must raise DiscussionLockedError."""
    discussion = await make_discussion(db, status=DiscussionStatus.LOCKED)
    with pytest.raises(DiscussionLockedError):
        await svc.create_reply(db, discussion_id=discussion.id, author_id=1, body="Hi")


@pytest.mark.asyncio
async def test_create_reply_on_hidden_discussion_raises(db: AsyncSession) -> None:
    """AC-012: Posting a reply to a HIDDEN discussion must raise DiscussionHiddenError."""
    discussion = await make_discussion(db, status=DiscussionStatus.HIDDEN)
    with pytest.raises(DiscussionHiddenError):
        await svc.create_reply(db, discussion_id=discussion.id, author_id=1, body="Hi")


@pytest.mark.asyncio
async def test_create_reply_on_is_hidden_discussion_raises(db: AsyncSession) -> None:
    """AC-012: is_hidden flag also blocks replies."""
    discussion = await make_discussion(db, is_hidden=True)
    with pytest.raises(DiscussionHiddenError):
        await svc.create_reply(db, discussion_id=discussion.id, author_id=1, body="Hi")


@pytest.mark.asyncio
async def test_open_discussion_accepts_replies(db: AsyncSession) -> None:
    """Sanity: OPEN discussion allows replies."""
    discussion = await make_discussion(db, status=DiscussionStatus.OPEN)
    reply = await svc.create_reply(db, discussion_id=discussion.id, author_id=5, body="Works")
    assert reply.id is not None


# ─── AC-012: edit on locked discussion also blocked ────────────────────────


@pytest.mark.asyncio
async def test_update_reply_on_locked_discussion_raises(db: AsyncSession) -> None:
    """Editing a reply while the discussion is locked must also be rejected."""
    discussion = await make_discussion(db)
    reply = await svc.create_reply(db, discussion_id=discussion.id, author_id=1, body="original")

    # Lock the discussion
    discussion.status = DiscussionStatus.LOCKED
    await db.commit()

    with pytest.raises(DiscussionLockedError):
        await svc.update_reply(
            db,
            discussion_id=discussion.id,
            reply_id=reply.id,
            requesting_user_id=1,
            new_body="edited",
        )


# ─── AC-013: edit authorisation ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_reply_by_author_succeeds(db: AsyncSession) -> None:
    """AC-013: The reply author can edit their own reply."""
    discussion = await make_discussion(db)
    reply = await svc.create_reply(db, discussion_id=discussion.id, author_id=7, body="v1")

    updated = await svc.update_reply(
        db,
        discussion_id=discussion.id,
        reply_id=reply.id,
        requesting_user_id=7,
        new_body="v2",
    )
    assert updated.body == "v2"


@pytest.mark.asyncio
async def test_update_reply_by_non_author_raises_forbidden(db: AsyncSession) -> None:
    """AC-013: A user who is NOT the author receives 403/ReplyForbiddenError."""
    discussion = await make_discussion(db)
    reply = await svc.create_reply(db, discussion_id=discussion.id, author_id=7, body="v1")

    with pytest.raises(ReplyForbiddenError):
        await svc.update_reply(
            db,
            discussion_id=discussion.id,
            reply_id=reply.id,
            requesting_user_id=99,  # different user
            new_body="attempted hijack",
        )


@pytest.mark.asyncio
async def test_update_hidden_reply_raises(db: AsyncSession) -> None:
    """Editing a hidden reply is rejected."""

    discussion = await make_discussion(db)
    reply = await svc.create_reply(db, discussion_id=discussion.id, author_id=1, body="v1")

    # Hide the reply
    reply.status = ReplyStatus.HIDDEN
    reply.is_hidden = True
    await db.commit()

    with pytest.raises(ReplyHiddenError):
        await svc.update_reply(
            db,
            discussion_id=discussion.id,
            reply_id=reply.id,
            requesting_user_id=1,
            new_body="edit attempt",
        )


@pytest.mark.asyncio
async def test_update_reply_not_found_raises(db: AsyncSession) -> None:
    discussion = await make_discussion(db)
    with pytest.raises(ReplyNotFoundError):
        await svc.update_reply(
            db,
            discussion_id=discussion.id,
            reply_id=9999,
            requesting_user_id=1,
            new_body="nope",
        )


# ─── list / get helpers ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_replies_excludes_hidden(db: AsyncSession) -> None:

    discussion = await make_discussion(db)
    r1 = await svc.create_reply(db, discussion_id=discussion.id, author_id=1, body="visible")
    r2 = await svc.create_reply(db, discussion_id=discussion.id, author_id=1, body="hidden")

    r2.status = ReplyStatus.HIDDEN
    r2.is_hidden = True
    await db.commit()

    results = await svc.list_replies(db, discussion_id=discussion.id)
    ids = [r.id for r in results]
    assert r1.id in ids
    assert r2.id not in ids


@pytest.mark.asyncio
async def test_list_replies_pagination(db: AsyncSession) -> None:
    discussion = await make_discussion(db)
    for i in range(5):
        await svc.create_reply(db, discussion_id=discussion.id, author_id=1, body=f"reply {i}")

    page1 = await svc.list_replies(db, discussion_id=discussion.id, limit=3, offset=0)
    page2 = await svc.list_replies(db, discussion_id=discussion.id, limit=3, offset=3)
    assert len(page1) == 3
    assert len(page2) == 2

```

### `backend/tests/services/test_visibility_service.py`
```python
from __future__ import annotations

"""Unit tests for app.services.discussion.visibility.

Covers:
    AC-012.3 — hidden discussions/replies excluded from non-moderator views.
    AC-013.3 — moderator receives unfiltered sets (include_hidden=True).
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discussion import Discussion, Reply
from app.models.enums import DiscussionStatus, ReplyStatus
from app.services.discussion.visibility import (
    apply_discussion_visibility,
    apply_reply_visibility,
    is_discussion_visible,
    is_reply_visible,
)
from tests.conftest import make_discussion, make_reply


# ─── is_discussion_visible ─────────────────────────────────────────────────


def _open_discussion() -> Discussion:
    d = Discussion(
        id=1, title="t", body="b", author_id=1,
        status=DiscussionStatus.OPEN, is_hidden=False,
    )
    return d


def _hidden_status_discussion() -> Discussion:
    d = Discussion(
        id=2, title="t", body="b", author_id=1,
        status=DiscussionStatus.HIDDEN, is_hidden=False,
    )
    return d


def _hidden_flag_discussion() -> Discussion:
    d = Discussion(
        id=3, title="t", body="b", author_id=1,
        status=DiscussionStatus.OPEN, is_hidden=True,
    )
    return d


class TestIsDiscussionVisible:
    def test_open_visible_to_non_moderator(self) -> None:
        assert is_discussion_visible(_open_discussion(), include_hidden=False) is True

    def test_open_visible_to_moderator(self) -> None:
        assert is_discussion_visible(_open_discussion(), include_hidden=True) is True

    def test_hidden_status_invisible_to_non_moderator(self) -> None:
        # AC-012.3
        assert is_discussion_visible(_hidden_status_discussion(), include_hidden=False) is False

    def test_hidden_status_visible_to_moderator(self) -> None:
        # AC-013.3
        assert is_discussion_visible(_hidden_status_discussion(), include_hidden=True) is True

    def test_is_hidden_flag_invisible_to_non_moderator(self) -> None:
        # AC-012.3
        assert is_discussion_visible(_hidden_flag_discussion(), include_hidden=False) is False

    def test_is_hidden_flag_visible_to_moderator(self) -> None:
        # AC-013.3
        assert is_discussion_visible(_hidden_flag_discussion(), include_hidden=True) is True


# ─── is_reply_visible ──────────────────────────────────────────────────────


def _visible_reply() -> Reply:
    return Reply(
        id=1, discussion_id=1, author_id=1, body="x",
        status=ReplyStatus.VISIBLE, is_hidden=False,
    )


def _hidden_status_reply() -> Reply:
    return Reply(
        id=2, discussion_id=1, author_id=1, body="x",
        status=ReplyStatus.HIDDEN, is_hidden=False,
    )


def _hidden_flag_reply() -> Reply:
    return Reply(
        id=3, discussion_id=1, author_id=1, body="x",
        status=ReplyStatus.VISIBLE, is_hidden=True,
    )


class TestIsReplyVisible:
    def test_visible_reply_accessible_to_non_moderator(self) -> None:
        assert is_reply_visible(_visible_reply(), include_hidden=False) is True

    def test_hidden_status_reply_inaccessible_to_non_moderator(self) -> None:
        # AC-012.3
        assert is_reply_visible(_hidden_status_reply(), include_hidden=False) is False

    def test_hidden_status_reply_accessible_to_moderator(self) -> None:
        # AC-013.3
        assert is_reply_visible(_hidden_status_reply(), include_hidden=True) is True

    def test_hidden_flag_reply_inaccessible_to_non_moderator(self) -> None:
        # AC-012.3
        assert is_reply_visible(_hidden_flag_reply(), include_hidden=False) is False

    def test_hidden_flag_reply_accessible_to_moderator(self) -> None:
        # AC-013.3
        assert is_reply_visible(_hidden_flag_reply(), include_hidden=True) is True


# ─── apply_discussion_visibility (DB query filter) ─────────────────────────


@pytest.mark.asyncio
async def test_apply_discussion_visibility_excludes_hidden_status(db: AsyncSession) -> None:
    """AC-012.3: HIDDEN-status discussions absent from non-moderator query."""
    open_d = await make_discussion(db, status=DiscussionStatus.OPEN)
    hidden_d = await make_discussion(db, status=DiscussionStatus.HIDDEN)

    stmt = apply_discussion_visibility(select(Discussion), include_hidden=False)
    result = await db.execute(stmt)
    ids = [r.id for r in result.scalars().all()]

    assert open_d.id in ids
    assert hidden_d.id not in ids


@pytest.mark.asyncio
async def test_apply_discussion_visibility_excludes_is_hidden_flag(db: AsyncSession) -> None:
    """AC-012.3: is_hidden=True discussions absent from non-moderator query."""
    visible_d = await make_discussion(db, is_hidden=False)
    hidden_d = await make_discussion(db, is_hidden=True)

    stmt = apply_discussion_visibility(select(Discussion), include_hidden=False)
    result = await db.execute(stmt)
    ids = [r.id for r in result.scalars().all()]

    assert visible_d.id in ids
    assert hidden_d.id not in ids


@pytest.mark.asyncio
async def test_apply_discussion_visibility_includes_hidden_for_moderator(
    db: AsyncSession,
) -> None:
    """AC-013.3: Moderator query returns hidden discussions too."""
    open_d = await make_discussion(db, status=DiscussionStatus.OPEN)
    hidden_d = await make_discussion(db, status=DiscussionStatus.HIDDEN)
    flag_d = await make_discussion(db, is_hidden=True)

    stmt = apply_discussion_visibility(select(Discussion), include_hidden=True)
    result = await db.execute(stmt)
    ids = [r.id for r in result.scalars().all()]

    assert open_d.id in ids
    assert hidden_d.id in ids
    assert flag_d.id in ids


# ─── apply_reply_visibility (DB query filter) ──────────────────────────────


@pytest.mark.asyncio
async def test_apply_reply_visibility_excludes_hidden(db: AsyncSession) -> None:
    """AC-012.3: hidden replies absent from non-moderator list."""
    discussion = await make_discussion(db)
    visible_r = await make_reply(db, discussion)
    hidden_r = await make_reply(db, discussion, status=ReplyStatus.HIDDEN, is_hidden=True)

    stmt = apply_reply_visibility(
        select(Reply).where(Reply.discussion_id == discussion.id),
        include_hidden=False,
    )
    result = await db.execute(stmt)
    ids = [r.id for r in result.scalars().all()]

    assert visible_r.id in ids
    assert hidden_r.id not in ids


@pytest.mark.asyncio
async def test_apply_reply_visibility_includes_hidden_for_moderator(db: AsyncSession) -> None:
    """AC-013.3: Moderator list includes hidden replies."""
    discussion = await make_discussion(db)
    visible_r = await make_reply(db, discussion)
    hidden_r = await make_reply(db, discussion, status=ReplyStatus.HIDDEN, is_hidden=True)

    stmt = apply_reply_visibility(
        select(Reply).where(Reply.discussion_id == discussion.id),
        include_hidden=True,
    )
    result = await db.execute(stmt)
    ids = [r.id for r in result.scalars().all()]

    assert visible_r.id in ids
    assert hidden_r.id in ids

```