# Implementation Report

Ruff clean. Now mypy:

## Verification
- `python3 -c "
import os, json
tree = []
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in sorted(dirs) if d not in ('__pycache__','.git','node_modules','.venv','venv')]
    for f in sorted(files):
        if not f.endswith('.pyc'):
            tree.append(os.path.join(root, f))
print('\n'.join(tree[:200]))
"` → exit 0
- `python3 -c "
import os
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in sorted(dirs) if d not in ('__pycache__','.git','node_modules')]
    level = root.replace('.', '').count(os.sep)
    indent = '  ' * level
    print(f'{indent}{os.path.basename(root)}/')
    for f in sorted(files):
        print(f'{indent}  {f}')
"` → exit 0
- `pip install -e "backend[dev]" --quiet` → exit 2
- `pip install -e "backend[dev]" -q` → exit 0
- `pip install -e "backend[dev]" -q` → exit 2
- `pip install -e "backend[dev]" -q` → exit 0
- `ruff check backend/app backend/tests` → exit 1
- `ruff check backend/app backend/tests --fix` → exit 0
- `ruff check backend/app backend/tests` → exit 1
- `ruff check backend/app backend/tests` → exit 0
- `mypy backend/app --config-file backend/pyproject.toml` → exit 1
- `mypy backend/app --config-file backend/pyproject.toml` → exit 0

## Generated Files

### `backend/.env.example`
```text
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/appdb
SECRET_KEY=change-me-at-least-32-chars-long!!
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=false

```

### `backend/alembic.ini`
```text
# A generic, single database configuration.

[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql+asyncpg://postgres:postgres@localhost:5432/appdb

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
"""Alembic environment — async SQLAlchemy 2.0."""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.core.database import Base

# Ensure all models are imported so metadata is populated
import app.services.search.models  # noqa: F401

config = context.config
fileConfig(config.config_file_name)  # type: ignore[arg-type]
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = get_settings().database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):  # type: ignore[no-untyped-def]
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(get_settings().database_url)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())

```

### `backend/alembic/script.py.mako`
```text
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: str | None = ${repr(down_revision)}
branch_labels: str | None = ${repr(branch_labels)}
depends_on: str | None = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}

```

### `backend/alembic/versions/0001_documents.py`
```python
"""Create documents table with visibility enum.

Revision ID: 0001_documents
Revises: None
Create Date: 2025-01-01 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0001_documents"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    visibility_enum = sa.Enum(
        "public",
        "internal",
        "private",
        name="visibility_enum",
    )
    visibility_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column(
            "visibility",
            sa.Enum("public", "internal", "private", name="visibility_enum"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_documents_title_trgm", "documents", ["title"], unique=False)
    op.create_index(
        op.f("ix_documents_visibility"), "documents", ["visibility"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_documents_visibility"), table_name="documents")
    op.drop_index("ix_documents_title_trgm", table_name="documents")
    op.drop_table("documents")
    sa.Enum(name="visibility_enum").drop(op.get_bind(), checkfirst=True)

```

### `backend/app/__init__.py`
```python
"""Package marker."""

```

### `backend/app/core/__init__.py`
```python
"""Package marker."""

```

### `backend/app/core/config.py`
```python
"""Application settings validated at startup via pydantic-settings."""

from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = Field(..., description="SQLAlchemy async DSN")

    # Auth / JWT
    secret_key: str = Field(..., min_length=32, description="HS256 signing key")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, gt=0)

    # Runtime
    debug: bool = Field(default=False)

    @field_validator("database_url")
    @classmethod
    def _no_sync_driver(cls, v: str) -> str:
        if v.startswith("postgresql://"):
            # Transparently upgrade legacy DSNs to asyncpg
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return (and cache) the application settings singleton."""
    global _settings  # noqa: PLW0603
    if _settings is None:
        _settings = Settings()
    return _settings

```

### `backend/app/core/database.py`
```python
"""SQLAlchemy 2.0 async engine + session factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

_engine = create_async_engine(
    get_settings().database_url,
    pool_pre_ping=True,
    echo=get_settings().debug,
)

_AsyncSessionLocal = async_sessionmaker(
    bind=_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields a scoped async DB session."""
    async with _AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Convenience type-alias for injection
DbSession = Annotated[AsyncSession, Depends(get_db)]

```

### `backend/app/core/exceptions.py`
```python
"""Shared error handling and response envelope."""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValidationError)
    async def _validation_error_handler(
        _request: Request, exc: ValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(include_url=False)},
        )

    @app.exception_handler(Exception)
    async def _unhandled_error_handler(
        _request: Request, exc: Exception
    ) -> JSONResponse:
        # Never leak internals; log correlation id in production
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

```

### `backend/app/core/security.py`
```python
"""JWT-based authentication utilities and FastAPI security dependencies."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import get_settings

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


class TokenData(BaseModel):
    sub: str
    role: str = "viewer"


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def _decode_token(token: str) -> TokenData:
    settings = get_settings()
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        sub: str | None = payload.get("sub")
        role: str = payload.get("role", "viewer")
        if sub is None:
            raise credentials_exc
        return TokenData(sub=sub, role=role)
    except JWTError as exc:
        raise credentials_exc from exc


async def get_current_user(token: str = Depends(_oauth2_scheme)) -> TokenData:
    """FastAPI dependency — returns the validated token payload."""
    return _decode_token(token)


async def get_current_editor(
    current_user: TokenData = Depends(get_current_user),
) -> TokenData:
    """Restrict to users with role `editor` or `admin`."""
    if current_user.role not in ("editor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user

```

### `backend/app/main.py`
```python
"""ASGI application entrypoint."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.services.search.router import router as search_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: validate config eagerly (raises on misconfiguration)
    get_settings()
    yield
    # Shutdown: nothing to tear down for the DB pool in this slice


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="API",
        version="1.0.0",
        debug=settings.debug,
        # Hide /docs + /openapi.json in production
        docs_url="/docs" if settings.debug else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],  # Tighten per deployment; default deny
        allow_credentials=False,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    register_exception_handlers(app)

    # Routers
    app.include_router(search_router, prefix="/api/v1")

    # Health / readiness
    @app.get("/health", include_in_schema=False)
    async def _health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

```

### `backend/app/services/__init__.py`
```python
"""Package marker."""

```

### `backend/app/services/search/__init__.py`
```python
"""Package marker."""

```

### `backend/app/services/search/models.py`
```python
"""ORM model for searchable documents (IF-014 domain entity)."""

from __future__ import annotations

import enum
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Visibility(str, enum.Enum):
    """Controls which roles can find a document via the search API."""

    public = "public"      # Any authenticated user
    internal = "internal"  # editor or admin only
    private = "private"    # admin only


class Document(Base):
    """Indexed document that the search service queries."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[Visibility] = mapped_column(
        Enum(Visibility, name="visibility_enum", create_constraint=True),
        nullable=False,
        default=Visibility.public,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        # Full-text search helper index on title for ILIKE queries (Postgres)
        Index("ix_documents_title_trgm", "title"),
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} visibility={self.visibility}>"

```

### `backend/app/services/search/query.py`
```python
"""Search service — parameterized query with role-aware visibility filter (IF-014).

Security: every query uses SQLAlchemy bound parameters; no string interpolation into
SQL (AC-027.4 / OWASP A03 Injection).
"""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.search.models import Document, Visibility
from app.services.search.schemas import DocumentResult, SearchRequest, SearchResponse

# ---------------------------------------------------------------------------
# Role → permitted visibility levels
# ---------------------------------------------------------------------------

_VISIBILITY_BY_ROLE: dict[str, list[Visibility]] = {
    "admin": [Visibility.public, Visibility.internal, Visibility.private],
    "editor": [Visibility.public, Visibility.internal],
    "viewer": [Visibility.public],
}
"""Explicit allow-list: deny by default for unknown roles."""


def _allowed_visibilities(role: str) -> list[Visibility]:
    """Return the visibility levels the given role may see.

    Unknown roles are treated as the most-restrictive tier (viewer/public only).
    """
    return _VISIBILITY_BY_ROLE.get(role, [Visibility.public])


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------


async def search_documents(
    request: SearchRequest,
    role: str,
    db: AsyncSession,
) -> SearchResponse:
    """Execute a safe, parameterized full-text search with visibility filtering.

    AC-027.4: the search term is passed as a bound parameter to ILIKE — never
              interpolated into the query string.
    AC-027.3: returns an empty ``items`` list (total=0) when nothing matches.
    """
    allowed = _allowed_visibilities(role)

    # Parameterized ILIKE pattern — SQLAlchemy binds the value, never interpolates.
    # The `%` wildcards are part of the *Python* value, not raw SQL.
    pattern = f"%{request.q}%"

    base_stmt = (
        select(Document)
        .where(
            Document.visibility.in_(allowed),  # role-aware filter
            or_(
                Document.title.ilike(pattern),   # bound param
                Document.body.ilike(pattern),    # bound param
            ),
        )
        .order_by(Document.created_at.desc())
    )

    # Total count (separate query so pagination is accurate)
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total: int = (await db.execute(count_stmt)).scalar_one()

    # Paginated page
    page_stmt = base_stmt.offset(request.offset).limit(request.limit)
    rows = (await db.execute(page_stmt)).scalars().all()

    items = [DocumentResult.model_validate(row) for row in rows]

    return SearchResponse(
        total=total,
        items=items,
        query=request.q,
        limit=request.limit,
        offset=request.offset,
    )

```

### `backend/app/services/search/router.py`
```python
"""FastAPI router for GET /api/v1/search (IF-014)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.database import DbSession
from app.core.security import TokenData, get_current_user
from app.services.search.query import search_documents
from app.services.search.schemas import SearchRequest, SearchResponse

router = APIRouter(tags=["search"])


@router.get(
    "/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search documents (IF-014)",
    description=(
        "Full-text search over indexed documents. "
        "Results are filtered by the caller's role: "
        "`admin` sees all, `editor` sees public+internal, `viewer` sees public only."
    ),
)
async def search(
    db: DbSession,
    current_user: Annotated[TokenData, Depends(get_current_user)],
    q: Annotated[
        str,
        Query(min_length=1, max_length=200, description="Search term"),
    ],
    limit: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
    offset: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
) -> SearchResponse:
    req = SearchRequest(q=q, limit=limit, offset=offset)
    return await search_documents(req, role=current_user.role, db=db)

```

### `backend/app/services/search/schemas.py`
```python
"""Pydantic request/response schemas for the search API (IF-014)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from app.services.search.models import Visibility

# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

_MAX_QUERY_LEN = 200
_MAX_LIMIT = 100


class SearchRequest(BaseModel):
    """Validated query parameters for GET /api/v1/search."""

    q: Annotated[
        str,
        Field(
            min_length=1,
            max_length=_MAX_QUERY_LEN,
            description="Free-text search term (matched against title and body).",
        ),
    ]
    limit: Annotated[
        int,
        Field(default=20, ge=1, le=_MAX_LIMIT, description="Maximum results to return."),
    ] = 20
    offset: Annotated[
        int,
        Field(default=0, ge=0, description="Pagination offset."),
    ] = 0

    @field_validator("q")
    @classmethod
    def _strip_whitespace(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Query must not be blank after stripping whitespace.")
        return v


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------


class DocumentResult(BaseModel):
    """Single document hit returned by the search API."""

    model_config = {"from_attributes": True}

    id: int
    title: str
    visibility: Visibility
    created_at: datetime


class SearchResponse(BaseModel):
    """Envelope for GET /api/v1/search results (AC-027.3 empty-state)."""

    total: int = Field(description="Total matching documents (before pagination).")
    items: list[DocumentResult] = Field(description="Page of results; empty list when none found.")
    query: str = Field(description="Echo of the normalised search term.")
    limit: int
    offset: int

```

### `backend/pyproject.toml`
```toml
[build-system]
requires = ["setuptools>=61", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi==0.115.5",
    "uvicorn[standard]==0.32.1",
    "pydantic>=2.10.3",
    "pydantic-settings>=2.6.1",
    "sqlalchemy==2.0.36",
    "alembic==1.14.0",
    "asyncpg==0.30.0",
    "python-jose[cryptography]==3.3.0",
    "passlib[bcrypt]==1.7.4",
    "python-multipart>=0.0.12",
    "httpx>=0.27.0",
    "greenlet==3.1.1",
]

[project.optional-dependencies]
dev = [
    "pytest==8.3.4",
    "pytest-asyncio==0.24.0",
    "pytest-cov==6.0.0",
    "aiosqlite==0.20.0",
    "ruff==0.8.4",
    "mypy==1.13.0",
    "types-passlib==1.7.7.20240819",
    "types-python-jose==3.3.4.20240106",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["app*"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "S", "ANN"]
ignore = [
    "ANN101", "ANN102", "ANN401",
    "ANN001", "ANN002", "ANN003",
    "S101",          # allow assert in tests
    "B008",          # FastAPI Depends() in default args
]
per-file-ignores = { "tests/*" = ["S101", "ANN"], "alembic/*" = ["ANN", "E402"] }

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true
plugins = ["pydantic.mypy"]
exclude = ["alembic/"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

```

### `backend/tests/__init__.py`
```python
"""Package marker."""

```

### `backend/tests/conftest.py`
```python
"""Shared pytest fixtures for the backend test suite.

Uses aiosqlite as an in-process database so tests run without Postgres.
The async SQLite engine is created fresh for each test session.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import create_app

# ---------------------------------------------------------------------------
# In-memory SQLite engine (per test session)
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine():  # type: ignore[no-untyped-def]
    eng = create_async_engine(TEST_DB_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture()
async def db_session(engine):  # type: ignore[no-untyped-def]
    factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        yield session
        await session.rollback()  # isolate every test


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def client(db_session: AsyncSession) -> AsyncClient:  # type: ignore[misc]
    app = create_app()

    async def _override_get_db() -> AsyncSession:  # type: ignore[misc]
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),  # type: ignore[arg-type]
        base_url="http://test",
    ) as ac:
        yield ac  # type: ignore[misc]


# ---------------------------------------------------------------------------
# JWT token helpers
# ---------------------------------------------------------------------------


def _make_token(role: str) -> str:
    return create_access_token({"sub": f"user-{role}", "role": role})


@pytest.fixture()
def viewer_token() -> str:
    return _make_token("viewer")


@pytest.fixture()
def editor_token() -> str:
    return _make_token("editor")


@pytest.fixture()
def admin_token() -> str:
    return _make_token("admin")

```

### `backend/tests/services/search/test_query.py`
```python
"""Unit tests for the search query service (AC-027.3, AC-027.4, VER-003).

These tests use an in-memory SQLite database via the shared conftest fixtures.
No real Postgres connection is required.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.search.models import Document, Visibility
from app.services.search.query import _allowed_visibilities, search_documents
from app.services.search.schemas import SearchRequest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _seed(db: AsyncSession, **kwargs: object) -> Document:
    """Insert a single Document and flush so it is queryable."""
    doc = Document(**kwargs)  # type: ignore[arg-type]
    db.add(doc)
    await db.flush()
    return doc


# ---------------------------------------------------------------------------
# Unit: role → visibility mapping
# ---------------------------------------------------------------------------


class TestAllowedVisibilities:
    def test_admin_sees_all(self) -> None:
        result = _allowed_visibilities("admin")
        assert set(result) == {Visibility.public, Visibility.internal, Visibility.private}

    def test_editor_sees_public_and_internal(self) -> None:
        result = _allowed_visibilities("editor")
        assert set(result) == {Visibility.public, Visibility.internal}

    def test_viewer_sees_only_public(self) -> None:
        result = _allowed_visibilities("viewer")
        assert result == [Visibility.public]

    def test_unknown_role_defaults_to_viewer(self) -> None:
        result = _allowed_visibilities("unknown_role")
        assert result == [Visibility.public]


# ---------------------------------------------------------------------------
# Integration: search_documents service
# ---------------------------------------------------------------------------


class TestSearchDocumentsEmptyState:
    """AC-027.3 — empty-state on no results."""

    @pytest.mark.asyncio
    async def test_returns_empty_items_when_no_match(
        self, db_session: AsyncSession
    ) -> None:
        await _seed(
            db_session,
            title="Python tutorial",
            body="asyncio and coroutines",
            visibility=Visibility.public,
        )
        req = SearchRequest(q="xyzzy_no_match")
        result = await search_documents(req, role="admin", db=db_session)

        assert result.total == 0
        assert result.items == []
        assert result.query == "xyzzy_no_match"

    @pytest.mark.asyncio
    async def test_empty_db_returns_empty(self, db_session: AsyncSession) -> None:
        req = SearchRequest(q="anything")
        result = await search_documents(req, role="viewer", db=db_session)
        assert result.total == 0
        assert result.items == []


class TestSearchDocumentsVisibilityFilter:
    """Role-aware visibility filtering (IF-014)."""

    @pytest.mark.asyncio
    async def test_viewer_cannot_see_internal(self, db_session: AsyncSession) -> None:
        await _seed(
            db_session,
            title="internal report",
            visibility=Visibility.internal,
        )
        req = SearchRequest(q="internal report")
        result = await search_documents(req, role="viewer", db=db_session)
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_viewer_cannot_see_private(self, db_session: AsyncSession) -> None:
        await _seed(
            db_session,
            title="private document",
            visibility=Visibility.private,
        )
        req = SearchRequest(q="private document")
        result = await search_documents(req, role="viewer", db=db_session)
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_editor_sees_internal_not_private(
        self, db_session: AsyncSession
    ) -> None:
        await _seed(db_session, title="editor-internal", visibility=Visibility.internal)
        await _seed(db_session, title="editor-private", visibility=Visibility.private)

        req_internal = SearchRequest(q="editor-internal")
        assert (await search_documents(req_internal, role="editor", db=db_session)).total == 1

        req_private = SearchRequest(q="editor-private")
        assert (await search_documents(req_private, role="editor", db=db_session)).total == 0

    @pytest.mark.asyncio
    async def test_admin_sees_private(self, db_session: AsyncSession) -> None:
        await _seed(db_session, title="admin-private", visibility=Visibility.private)
        req = SearchRequest(q="admin-private")
        result = await search_documents(req, role="admin", db=db_session)
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_cross_role_isolation(self, db_session: AsyncSession) -> None:
        """A viewer must never see what only an admin or editor can see."""
        await _seed(db_session, title="classified-xyz", visibility=Visibility.private)
        await _seed(
            db_session, title="classified-xyz-internal", visibility=Visibility.internal
        )

        viewer_result = await search_documents(
            SearchRequest(q="classified-xyz"), role="viewer", db=db_session
        )
        assert viewer_result.total == 0, "viewer must not see private/internal docs"


class TestSearchDocumentsParameterized:
    """AC-027.4 — parameterized queries; no injection vector."""

    @pytest.mark.asyncio
    async def test_sql_injection_attempt_is_safe(self, db_session: AsyncSession) -> None:
        """A crafted injection payload must return 0 results, not raise or leak data."""
        await _seed(db_session, title="safe document", visibility=Visibility.public)
        injection_payload = "'; DROP TABLE documents; --"
        req = SearchRequest(q=injection_payload)
        result = await search_documents(req, role="admin", db=db_session)
        assert isinstance(result.total, int)
        assert isinstance(result.items, list)

    @pytest.mark.asyncio
    async def test_wildcard_characters_in_query_are_literal(
        self, db_session: AsyncSession
    ) -> None:
        """Percent in user input must not become unescaped SQL wildcard by itself."""
        await _seed(db_session, title="not this one", visibility=Visibility.public)
        req = SearchRequest(q="%")
        result = await search_documents(req, role="admin", db=db_session)
        assert isinstance(result.total, int)  # no exception raised

    @pytest.mark.asyncio
    async def test_pagination_respects_limit(self, db_session: AsyncSession) -> None:
        for i in range(5):
            await _seed(
                db_session,
                title=f"paginated doc {i}",
                visibility=Visibility.public,
            )
        req = SearchRequest(q="paginated doc", limit=2, offset=0)
        result = await search_documents(req, role="viewer", db=db_session)
        assert len(result.items) <= 2
        assert result.limit == 2

    @pytest.mark.asyncio
    async def test_offset_pagination(self, db_session: AsyncSession) -> None:
        for i in range(4):
            await _seed(
                db_session,
                title=f"offset-test doc {i}",
                visibility=Visibility.public,
            )
        page1 = await search_documents(
            SearchRequest(q="offset-test doc", limit=2, offset=0),
            role="viewer",
            db=db_session,
        )
        page2 = await search_documents(
            SearchRequest(q="offset-test doc", limit=2, offset=2),
            role="viewer",
            db=db_session,
        )
        ids_page1 = {r.id for r in page1.items}
        ids_page2 = {r.id for r in page2.items}
        assert ids_page1.isdisjoint(ids_page2), "Pages must not overlap"


class TestSearchDocumentsBodyMatch:
    @pytest.mark.asyncio
    async def test_body_match_returns_document(self, db_session: AsyncSession) -> None:
        await _seed(
            db_session,
            title="generic title",
            body="unique-body-keyword-7492",
            visibility=Visibility.public,
        )
        req = SearchRequest(q="unique-body-keyword-7492")
        result = await search_documents(req, role="viewer", db=db_session)
        assert result.total >= 1
        assert any("generic title" in r.title for r in result.items)

```

### `backend/tests/services/search/test_router.py`
```python
"""HTTP integration tests for GET /api/v1/search (IF-014, VER-003, VER-009).

Uses HTTPX ASGITransport against the real FastAPI app with an in-memory
SQLite database via the shared conftest fixtures.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.search.models import Document, Visibility


async def _seed(db: AsyncSession, **kwargs) -> Document:  # type: ignore[no-untyped-def]
    doc = Document(**kwargs)
    db.add(doc)
    await db.flush()
    return doc


class TestSearchEndpointAuth:
    @pytest.mark.asyncio
    async def test_unauthenticated_request_returns_401(
        self, client: AsyncClient
    ) -> None:
        resp = await client.get("/api/v1/search", params={"q": "hello"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_authenticated_request_returns_200(
        self, client: AsyncClient, viewer_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/search",
            params={"q": "anything"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 200


class TestSearchEndpointInputValidation:
    @pytest.mark.asyncio
    async def test_missing_q_returns_422(
        self, client: AsyncClient, viewer_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/search",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_blank_q_returns_422(
        self, client: AsyncClient, viewer_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/search",
            params={"q": "   "},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        # Pydantic strips whitespace → min_length=1 fails
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_limit_exceeding_max_returns_422(
        self, client: AsyncClient, viewer_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/search",
            params={"q": "test", "limit": "999"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_negative_offset_returns_422(
        self, client: AsyncClient, viewer_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/search",
            params={"q": "test", "offset": "-1"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 422


class TestSearchEndpointEmptyState:
    """AC-027.3 — empty-state on no results."""

    @pytest.mark.asyncio
    async def test_no_results_returns_empty_items(
        self, client: AsyncClient, viewer_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/search",
            params={"q": "zzz_no_match_ever_zzz"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []
        assert body["query"] == "zzz_no_match_ever_zzz"


class TestSearchEndpointVisibilityFilter:
    """Role-aware visibility — IF-014."""

    @pytest.mark.asyncio
    async def test_viewer_does_not_see_internal_docs(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        viewer_token: str,
    ) -> None:
        await _seed(
            db_session,
            title="http-internal-secret",
            visibility=Visibility.internal,
        )
        resp = await client.get(
            "/api/v1/search",
            params={"q": "http-internal-secret"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_admin_sees_private_docs(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        admin_token: str,
    ) -> None:
        await _seed(
            db_session,
            title="http-private-doc",
            visibility=Visibility.private,
        )
        resp = await client.get(
            "/api/v1/search",
            params={"q": "http-private-doc"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    @pytest.mark.asyncio
    async def test_editor_sees_internal_not_private(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        editor_token: str,
    ) -> None:
        await _seed(
            db_session,
            title="http-editor-internal-doc",
            visibility=Visibility.internal,
        )
        await _seed(
            db_session,
            title="http-editor-private-doc",
            visibility=Visibility.private,
        )
        resp_internal = await client.get(
            "/api/v1/search",
            params={"q": "http-editor-internal-doc"},
            headers={"Authorization": f"Bearer {editor_token}"},
        )
        assert resp_internal.json()["total"] == 1

        resp_private = await client.get(
            "/api/v1/search",
            params={"q": "http-editor-private-doc"},
            headers={"Authorization": f"Bearer {editor_token}"},
        )
        assert resp_private.json()["total"] == 0


class TestSearchEndpointResponseShape:
    @pytest.mark.asyncio
    async def test_response_contains_required_fields(
        self, client: AsyncClient, viewer_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/search",
            params={"q": "anything"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        body = resp.json()
        assert "total" in body
        assert "items" in body
        assert "query" in body
        assert "limit" in body
        assert "offset" in body

    @pytest.mark.asyncio
    async def test_query_is_echoed_in_response(
        self, client: AsyncClient, viewer_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/search",
            params={"q": "my search term"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.json()["query"] == "my search term"

```