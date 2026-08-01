# Implementation Report

Fix the remaining 8 issues:

## Verification
- `python3 -c "
import os, sys
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in sorted(dirs) if d not in ('__pycache__','.git','.venv','node_modules','.mypy_cache')]
    for f in sorted(files):
        print(os.path.join(root, f))
"` → exit 0
- `pip install -q "fastapi==0.111.1" "uvicorn[standard]==0.30.1" "pydantic==2.7.4" "pydantic-settings==2.3.4" "sqlalchemy==2.0.31" "alembic==1.13.2" "python-jose[cryptography]==3.3.0" "passlib[bcrypt]==1.7.4" "python-multipart==0.0.9" "markupsafe==2.1.5" "greenlet==3.0.3" "pytest==8.2.2" "pytest-asyncio==0.23.7" "httpx==0.27.0" "aiosqlite==0.20.0" "types-passlib==1.7.7.20240327" "types-python-jose==3.3.4.20240106" "pytest-cov==5.0.0"` → exit 0
- `pip install -q "fastapi>=0.115.0" "uvicorn[standard]>=0.32.1" "pydantic>=2.10.3" "pydantic-settings>=2.6.1" "starlette>=0.41.3" "python-multipart>=0.0.10" "greenlet>=3.1.1"` → exit 0
- `python3 -c "import fastapi, pydantic, sqlalchemy, alembic, markupsafe; print('fastapi', fastapi.__version__, 'pydantic', pydantic.__version__, 'sqla', sqlalchemy.__version__, 'alembic', alembic.__version__)"` → exit 0
- `ruff check app/ tests/ --select E,F,I,UP,B,S,ANN --ignore ANN101,ANN102,S105,S106,ANN201,ANN001,ANN002,ANN003,ANN202,ANN204,ANN205,ANN206,S101` → exit 2
- `ruff check app/ tests/ --select E,F,I,UP,B --ignore S101` → exit 1
- `ruff check app/ tests/ --select E,F,I,UP,B --ignore S101` → exit 1
- `ruff check app/ tests/ --select E,F,I,UP,B --ignore S101` → exit 1

## Generated Files

### `backend/.env.example`
```text
DATABASE_URL=postgresql+asyncpg://postgres:changeme@localhost:5432/appdb
SECRET_KEY=change-me-in-production-use-at-least-32-random-bytes
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

```

### `backend/alembic.ini`
```text
# Alembic configuration file
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

# Async SQLAlchemy URL — overridden at runtime by env.py reading app config
sqlalchemy.url = sqlite+aiosqlite:///./test.db

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
"""Alembic env.py — async SQLAlchemy 2.0 pattern."""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import Base + all models so autogenerate sees metadata
from app.core.database import Base  # noqa: F401
import app.models  # noqa: F401  registers all ORM models

# Alembic Config object
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    from app.core.config import settings  # noqa: PLC0415

    return settings.database_url


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = get_url()
    connectable = async_engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


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

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}

```

### `backend/alembic/versions/0001_initial.py`
```python
"""Initial schema — users table with profile columns.

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("location", sa.String(100), nullable=True),
        sa.Column("website_url", sa.String(2048), nullable=True),
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
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")

```

### `backend/app/__init__.py`
```python
"""Package root."""

```

### `backend/app/core/__init__.py`
```python
"""Package root."""

```

### `backend/app/core/config.py`
```python
"""Application configuration validated at startup via pydantic-settings."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./test.db",
        description="Async SQLAlchemy database URL",
    )

    # JWT
    secret_key: str = Field(..., min_length=32, description="HS256 signing secret")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, ge=1)

    @field_validator("secret_key")
    @classmethod
    def secret_key_not_default(cls, v: str) -> str:
        if v == "change-me-in-production-use-at-least-32-random-bytes":
            import warnings  # noqa: PLC0415

            warnings.warn(
                "SECRET_KEY is set to the example default — rotate before production.",
                stacklevel=2,
            )
        return v


settings = Settings()

```

### `backend/app/core/database.py`
```python
"""Async SQLAlchemy engine and session factory."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields a transactional async session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

```

### `backend/app/core/security.py`
```python
"""JWT creation and verification utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    """Return a signed JWT access token for *subject* (user UUID as string)."""
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify *token*; raises JWTError on any failure."""
    return jwt.decode(  # type: ignore[no-any-return]
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )


__all__ = ["create_access_token", "decode_access_token", "JWTError"]

```

### `backend/app/dependencies/__init__.py`
```python
"""Package root."""

```

### `backend/app/dependencies/auth.py`
```python
"""FastAPI dependency: resolve the current authenticated user from the Bearer token."""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

_bearer = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validate the Bearer JWT and return the corresponding active User row.

    Raises HTTP 401 for invalid/expired tokens and HTTP 403 for inactive accounts.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(credentials.credentials)
        sub: str | None = payload.get("sub")
        if sub is None:
            raise credentials_exception
        user_id = uuid.UUID(sub)
    except (JWTError, ValueError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user: User | None = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive account",
        )
    return user

```

### `backend/app/main.py`
```python
"""ASGI application entrypoint — canonical app.main:app."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings  # validates config at import time
from app.core.database import engine, Base
from app.services.profile.router import router as profile_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create tables on startup (dev/test); close engine on shutdown."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Member API",
    version="1.0.0",
    lifespan=lifespan,
    # Never expose internal tracebacks in responses
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url=None,
)

# CORS — restrictive by default; override via env/settings in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],       # explicit origins only — no wildcard
    allow_credentials=True,
    allow_methods=["GET", "PUT", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# ── Global error handler — never leak internal details ────────────────────────
@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred."},
    )


# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(profile_router, prefix="/api/v1")


# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/healthz", include_in_schema=False)
async def healthz() -> dict[str, str]:
    return {"status": "ok"}

```

### `backend/app/models/__init__.py`
```python
"""Re-export all models so Alembic autogenerate sees them."""

from app.models.user import User  # noqa: F401

__all__ = ["User"]

```

### `backend/app/models/user.py`
```python
"""User ORM model — canonical identity entity (PHASE-011 / TASK-021)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


class User(Base):
    """Registered member account."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(254), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- profile fields (COMP-002 / IF-003) ---
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"

```

### `backend/app/services/__init__.py`
```python
"""Package root."""

```

### `backend/app/services/profile/__init__.py`
```python
"""Profile service package."""

from app.services.profile.router import router
from app.services.profile.service import get_profile, update_profile

__all__ = ["router", "get_profile", "update_profile"]

```

### `backend/app/services/profile/router.py`
```python
"""Profile router — GET/PUT /api/v1/profile (COMP-002 / IF-003)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.profile.schemas import ProfileResponse, ProfileUpdateRequest
from app.services.profile.service import get_profile, update_profile

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get(
    "",
    response_model=ProfileResponse,
    summary="Get own profile",
    status_code=status.HTTP_200_OK,
)
async def read_profile(
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> ProfileResponse:
    """
    Return the authenticated member's own profile.

    AC-007.x: Only the token-owning member may read their profile.
    A valid token is required; 401 is returned for missing/invalid tokens.
    """
    user = await get_profile(current_user)
    return ProfileResponse.model_validate(user)


@router.put(
    "",
    response_model=ProfileResponse,
    summary="Update own profile",
    status_code=status.HTTP_200_OK,
)
async def write_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ProfileResponse:
    """
    Update the authenticated member's own profile.

    AC-007.x: Self-only — the identity in the JWT governs which row is
    updated; no cross-user path parameter is accepted by this endpoint.
    """
    updated = await update_profile(current_user, payload, db)
    return ProfileResponse.model_validate(updated)

```

### `backend/app/services/profile/schemas.py`
```python
"""Pydantic schemas for the member profile resource (IF-003 / COMP-002)."""
import uuid
from datetime import datetime
from typing import Annotated

from markupsafe import escape
from pydantic import BaseModel, ConfigDict, Field, field_validator


def _html_escape(value: str | None) -> str | None:
    """Context-appropriate output encoding for free-text fields (VER-010)."""
    if value is None:
        return None
    return str(escape(value))


class ProfileResponse(BaseModel):
    """Read-only representation of a member's own profile (AC-007.x)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: Annotated[str | None, Field(default=None)]
    bio: Annotated[str | None, Field(default=None)]
    location: Annotated[str | None, Field(default=None)]
    website_url: Annotated[str | None, Field(default=None)]
    created_at: datetime
    updated_at: datetime

    @field_validator("display_name", "bio", "location", mode="after")
    @classmethod
    def encode_free_text(cls, v: str | None) -> str | None:
        """HTML-escape free-text fields before returning to callers (VER-010)."""
        return _html_escape(v)


class ProfileUpdateRequest(BaseModel):
    """Partial update payload for PUT /api/v1/profile."""

    display_name: Annotated[
        str | None,
        Field(default=None, max_length=100, description="Visible name (≤100 chars)"),
    ]
    bio: Annotated[
        str | None,
        Field(default=None, max_length=2000, description="Free-text biography (≤2000 chars)"),
    ]
    location: Annotated[
        str | None,
        Field(default=None, max_length=100, description="Location string (≤100 chars)"),
    ]
    website_url: Annotated[
        str | None,
        Field(default=None, max_length=2048, description="Personal website URL (≤2048 chars)"),
    ]

    @field_validator("website_url", mode="after")
    @classmethod
    def validate_website_url(cls, v: str | None) -> str | None:
        """Reject URLs with non-http(s) schemes to prevent javascript: injection."""
        if v is None:
            return v
        lower = v.strip().lower()
        if lower and not (lower.startswith("https://") or lower.startswith("http://")):

            raise ValueError("website_url must start with http:// or https://")
        return v

```

### `backend/app/services/profile/service.py`
```python
"""Profile service — business logic layer for COMP-002 (IF-003)."""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.profile.schemas import ProfileUpdateRequest


async def get_profile(user: User) -> User:
    """
    Return the user record for self-profile view.

    Authorization is enforced at the router layer; this layer trusts
    that the supplied user is already the authenticated principal.
    """
    return user


async def update_profile(
    user: User,
    payload: ProfileUpdateRequest,
    db: AsyncSession,
) -> User:
    """
    Apply *payload* to *user* and flush to the database.

    Only explicitly supplied (non-None) fields are updated so that a
    partial PUT does not accidentally clear existing data.
    """
    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user, field, value)

    user.updated_at = datetime.now(tz=UTC)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user

```

### `backend/pyproject.toml`
```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.1",
    "pydantic>=2.10.3",
    "pydantic-settings>=2.6.1",
    "sqlalchemy==2.0.31",
    "alembic==1.13.2",
    "asyncpg==0.29.0",
    "python-jose[cryptography]==3.3.0",
    "passlib[bcrypt]==1.7.4",
    "python-multipart>=0.0.10",
    "markupsafe>=2.1.5",
    "greenlet>=3.1.1",
]

[project.optional-dependencies]
dev = [
    "pytest==8.2.2",
    "pytest-asyncio==0.23.7",
    "httpx==0.27.0",
    "pytest-cov==5.0.0",
    "ruff==0.5.0",
    "mypy==1.10.1",
    "aiosqlite==0.20.0",
    "types-passlib==1.7.7.20240327",
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
ignore = ["ANN101", "ANN102", "S105", "S106"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]
ignore_missing_imports = false

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

```

### `backend/tests/__init__.py`
```python
"""Package marker for tests."""

```

### `backend/tests/conftest.py`
```python
"""Shared pytest fixtures for the backend test suite."""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.user import User

# ── In-memory SQLite for tests ────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _create_tables() -> AsyncGenerator[None, None]:
    """Create all tables once per test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a transactional session that is rolled back after each test."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture()
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTPX async client wired to the FastAPI app with the test DB session."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ── User helpers ──────────────────────────────────────────────────────────────


def _make_user(**kwargs: Any) -> User:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "email": f"user-{uuid.uuid4().hex[:8]}@example.com",
        "hashed_password": "hashed-placeholder",
        "is_active": True,
        "display_name": None,
        "bio": None,
        "location": None,
        "website_url": None,
        "created_at": datetime.now(tz=UTC),
        "updated_at": datetime.now(tz=UTC),
    }
    defaults.update(kwargs)
    return User(**defaults)


@pytest_asyncio.fixture()
async def user_alice(db_session: AsyncSession) -> User:
    u = _make_user(email="alice@example.com", display_name="Alice")
    db_session.add(u)
    await db_session.flush()
    return u


@pytest_asyncio.fixture()
async def user_bob(db_session: AsyncSession) -> User:
    u = _make_user(email="bob@example.com", display_name="Bob")
    db_session.add(u)
    await db_session.flush()
    return u


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(subject=str(user.id))
    return {"Authorization": f"Bearer {token}"}

```

### `backend/tests/test_profile.py`
```python
"""
Profile endpoint tests — TASK-025 / AC-007.x

Covers:
  VER-004  403 on cross-user access (self-only enforcement)
  VER-010  Free-text fields are output-encoded (XSS characters escaped)
"""

import uuid

import pytest
from httpx import AsyncClient

from app.models.user import User
from tests.conftest import auth_headers

# ── GET /api/v1/profile ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_profile_unauthenticated(client: AsyncClient) -> None:
    """No token → 403 (HTTPBearer auto_error returns 403 when no credentials)."""
    response = await client.get("/api/v1/profile")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_profile_invalid_token(client: AsyncClient) -> None:
    """Malformed token → 401."""
    response = await client.get(
        "/api/v1/profile",
        headers={"Authorization": "Bearer not.a.valid.jwt"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_profile_returns_own_data(client: AsyncClient, user_alice: User) -> None:
    """Authenticated user receives their own profile data."""
    response = await client.get("/api/v1/profile", headers=auth_headers(user_alice))
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(user_alice.id)
    assert data["email"] == user_alice.email
    assert data["display_name"] == "Alice"


@pytest.mark.asyncio
async def test_get_profile_does_not_expose_password_hash(
    client: AsyncClient, user_alice: User
) -> None:
    """Response must not contain the hashed password (OWASP A02)."""
    response = await client.get("/api/v1/profile", headers=auth_headers(user_alice))
    body = response.text
    assert "hashed_password" not in body
    assert "hashed-placeholder" not in body


# ── VER-004: 403 on cross-user access ─────────────────────────────────────────
#
# The endpoint has NO path parameter — the identity is taken exclusively from
# the JWT.  A user cannot supply another user's ID via the URL.  The tests
# below verify the architectural enforcement:
#   a) Alice with Alice's token sees Alice's data; Bob with Bob's token sees Bob's.
#   b) A token bearing an unknown UUID yields 401 (no such user).
#   c) A token bearing an inactive user's UUID yields 403.


@pytest.mark.asyncio
async def test_cross_user_access_impossible_no_path_param(
    client: AsyncClient, user_alice: User, user_bob: User
) -> None:
    """
    VER-004: There is no cross-user path parameter.

    Each principal can only ever see/edit their own profile.
    Alice with Alice's token gets Alice; Bob with Bob's token gets Bob.
    """
    r_alice = await client.get("/api/v1/profile", headers=auth_headers(user_alice))
    r_bob = await client.get("/api/v1/profile", headers=auth_headers(user_bob))

    assert r_alice.status_code == 200
    assert r_bob.status_code == 200
    assert r_alice.json()["id"] != r_bob.json()["id"]
    assert r_alice.json()["email"] == "alice@example.com"
    assert r_bob.json()["email"] == "bob@example.com"


@pytest.mark.asyncio
async def test_unknown_user_id_in_token_returns_401(client: AsyncClient) -> None:
    """VER-004: Token for non-existent user ID → 401."""
    from app.core.security import create_access_token  # noqa: PLC0415

    ghost_token = create_access_token(subject=str(uuid.uuid4()))
    response = await client.get(
        "/api/v1/profile",
        headers={"Authorization": f"Bearer {ghost_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_inactive_user_returns_403(
    client: AsyncClient,
    db_session: AsyncSession,
    user_alice: User,
) -> None:
    """VER-004: Inactive account → 403 (not 200)."""
    user_alice.is_active = False
    db_session.add(user_alice)
    await db_session.flush()

    response = await client.get("/api/v1/profile", headers=auth_headers(user_alice))
    assert response.status_code == 403


# ── VER-010: Free-text output encoding ────────────────────────────────────────


@pytest.mark.asyncio
async def test_xss_payload_in_display_name_is_escaped(
    client: AsyncClient, user_alice: User
) -> None:
    """VER-010: <script> in display_name must be HTML-escaped in the response."""
    payload = {"display_name": "<script>alert('xss')</script>"}
    put_resp = await client.put(
        "/api/v1/profile",
        json=payload,
        headers=auth_headers(user_alice),
    )
    assert put_resp.status_code == 200
    data = put_resp.json()
    assert "<script>" not in data["display_name"]
    assert "&lt;script&gt;" in data["display_name"]


@pytest.mark.asyncio
async def test_xss_payload_in_bio_is_escaped(
    client: AsyncClient, user_alice: User
) -> None:
    """VER-010: HTML metacharacters in bio are escaped."""
    bio = 'Hello <b>World</b> & "quotes" \'single\''
    put_resp = await client.put(
        "/api/v1/profile",
        json={"bio": bio},
        headers=auth_headers(user_alice),
    )
    assert put_resp.status_code == 200
    data = put_resp.json()
    assert "<b>" not in data["bio"]
    assert "&lt;b&gt;" in data["bio"]
    assert "&amp;" in data["bio"]


@pytest.mark.asyncio
async def test_xss_payload_in_location_is_escaped(
    client: AsyncClient, user_alice: User
) -> None:
    """VER-010: HTML in location is escaped."""
    put_resp = await client.put(
        "/api/v1/profile",
        json={"location": "<img src=x onerror=alert(1)>"},
        headers=auth_headers(user_alice),
    )
    assert put_resp.status_code == 200
    assert "<img" not in put_resp.json()["location"]


# ── PUT /api/v1/profile ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_put_profile_partial_update(client: AsyncClient, user_alice: User) -> None:
    """PUT with only some fields updates only those fields."""
    resp = await client.put(
        "/api/v1/profile",
        json={"bio": "I write Python."},
        headers=auth_headers(user_alice),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "Python" in data["bio"]
    assert data["display_name"] == "Alice"


@pytest.mark.asyncio
async def test_put_profile_invalid_website_scheme_rejected(
    client: AsyncClient, user_alice: User
) -> None:
    """VER-010: javascript: scheme must be rejected (422)."""
    resp = await client.put(
        "/api/v1/profile",
        json={"website_url": "javascript:alert(1)"},
        headers=auth_headers(user_alice),
    )
    assert resp.status_code == 422  # Pydantic validation error → 422


@pytest.mark.asyncio
async def test_put_profile_valid_website_url_accepted(
    client: AsyncClient, user_alice: User
) -> None:
    """https:// URLs are accepted."""
    resp = await client.put(
        "/api/v1/profile",
        json={"website_url": "https://alice.example.com"},
        headers=auth_headers(user_alice),
    )
    assert resp.status_code == 200
    assert resp.json()["website_url"] == "https://alice.example.com"


@pytest.mark.asyncio
async def test_put_profile_display_name_max_length(
    client: AsyncClient, user_alice: User
) -> None:
    """display_name > 100 chars → 422."""
    resp = await client.put(
        "/api/v1/profile",
        json={"display_name": "A" * 101},
        headers=auth_headers(user_alice),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_put_profile_bio_max_length(
    client: AsyncClient, user_alice: User
) -> None:
    """bio > 2000 chars → 422."""
    resp = await client.put(
        "/api/v1/profile",
        json={"bio": "B" * 2001},
        headers=auth_headers(user_alice),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_put_profile_unauthenticated_returns_403(client: AsyncClient) -> None:
    """No token on PUT → 403."""
    resp = await client.put("/api/v1/profile", json={"bio": "sneaky"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_after_put_reflects_changes(
    client: AsyncClient, user_alice: User
) -> None:
    """GET after PUT returns the updated values."""
    await client.put(
        "/api/v1/profile",
        json={"display_name": "Alice Updated", "location": "Berlin"},
        headers=auth_headers(user_alice),
    )
    get_resp = await client.get("/api/v1/profile", headers=auth_headers(user_alice))
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["display_name"] == "Alice Updated"
    assert data["location"] == "Berlin"

```