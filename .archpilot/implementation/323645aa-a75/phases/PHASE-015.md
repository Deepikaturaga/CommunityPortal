# Implementation Report

Good — down to 32 errors (16 remain after auto-fixes). The B008 warnings are expected FastAPI patterns (Depends in defaults); let's suppress them. The B904 `raise from` warnings are easy fixes. Let me also check what fixed automatically:

## Verification
- `python3 -c "
import os, json
result = []
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in {'.git','__pycache__','.mypy_cache','.ruff_cache','node_modules','.venv','venv'}]
    for f in files:
        result.append(os.path.join(root, f))
result.sort()
print('\n'.join(result[:120]))
"` → exit 0
- `python3 -c "
import os
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in {'.git','__pycache__','.mypy_cache','.ruff_cache','node_modules','.venv','venv'}]
    for f in sorted(files):
        print(os.path.join(root, f))
"` → exit 0
- `python3 -c "import sys; print(sys.version)"` → exit 0
- `pip show fastapi pydantic sqlalchemy alembic boto3 mypy ruff pytest pytest-asyncio httpx` → exit 0
- `pip show fastapi pydantic-settings asyncpg aiosqlite moto` → exit 0
- `pip show moto botocore` → exit 0
- `pip show python-jose passlib python-multipart` → exit 0
- `pip install -e backend/ --quiet` → exit 2
- `pip install -e backend/ --quiet 2>&1` → exit 1
- `pip install -e backend/ --quiet` → exit 0
- `ruff check backend/app backend/tests` → exit 1
- `ruff check backend/app backend/tests --fix` → exit 1
- `ruff check backend/app backend/tests --fix` → exit 1
- `ruff check backend/app backend/tests --fix` → exit 1

## Generated Files

### `backend/.env.example`
```text
# Backend environment — copy to .env and fill in real values
# Never commit a populated .env file

# ── Application ────────────────────────────────────────────
APP_ENV=development
SECRET_KEY=CHANGE_ME_use_openssl_rand_hex_32
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ── Database ───────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/appdb

# ── AWS / S3 ───────────────────────────────────────────────
AWS_REGION=us-east-1
S3_AVATAR_BUCKET=your-private-avatar-bucket
AVATAR_PRESIGN_PUT_EXPIRES_SECONDS=300
AVATAR_PRESIGN_GET_EXPIRES_SECONDS=900
AVATAR_MAX_SIZE_BYTES=5242880

# Leave blank in production — boto3 uses IAM roles / instance metadata
# Only populate for local overrides with aws-vault / localstack
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_ENDPOINT_URL=

```

### `backend/alembic.ini`
```text
# Alembic configuration — managed by backend/alembic/

[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = %(DATABASE_URL)s

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
"""Alembic env — async SQLAlchemy setup for autogenerate."""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ── Import all models so autogenerate can detect them ─────────────────────────
import app.models  # noqa: F401 — side-effect import registers metadata
from app.core.database import Base

# ── Alembic Config ─────────────────────────────────────────────────────────────
config = context.config

# Override sqlalchemy.url from environment (set in CI / docker-compose)
database_url = os.environ.get("DATABASE_URL") or os.environ.get("TEST_DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
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
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
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
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}

```

### `backend/alembic/versions/0001_initial_schema.py`
```python
"""Initial schema: users + media_assets tables.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2025-01-01 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── assetstatus enum ───────────────────────────────────────────────────────
    assetstatus = postgresql.ENUM(
        "pending", "confirmed", "deleted", name="assetstatus", create_type=False
    )
    assetstatus.create(op.get_bind(), checkfirst=True)

    # ── media_assets ───────────────────────────────────────────────────────────
    op.create_table(
        "media_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_type", sa.String(length=64), nullable=False, server_default="avatar"),
        sa.Column("s3_key", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("declared_size_bytes", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "confirmed", "deleted", name="assetstatus"),
            nullable=False,
            server_default="pending",
        ),
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
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("s3_key"),
    )
    op.create_index("ix_media_assets_owner_id", "media_assets", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_media_assets_owner_id", table_name="media_assets")
    op.drop_table("media_assets")
    sa.Enum(name="assetstatus").drop(op.get_bind(), checkfirst=True)
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

```

### `backend/app/__init__.py`
```python
"""App package init."""

```

### `backend/app/core/__init__.py`
```python
"""Core package init."""

```

### `backend/app/core/config.py`
```python
"""Application configuration — validated at startup via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────
    app_env: Literal["development", "testing", "production"] = "development"
    secret_key: str = Field(..., min_length=32)
    access_token_expire_minutes: int = Field(30, gt=0)

    # ── Database ───────────────────────────────────────────
    database_url: str = Field(..., pattern=r"^(postgresql|sqlite)")

    # ── AWS / S3 ───────────────────────────────────────────
    aws_region: str = "us-east-1"
    s3_avatar_bucket: str = Field(..., min_length=3)

    # Time-limited presigned URLs (seconds)
    avatar_presign_put_expires_seconds: int = Field(300, ge=60, le=900)
    avatar_presign_get_expires_seconds: int = Field(900, ge=60, le=3600)

    # Hard upload cap (default 5 MiB)
    avatar_max_size_bytes: int = Field(5_242_880, ge=1, le=20_971_520)

    # Optional overrides — must be absent/empty in production (IAM roles used)
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_endpoint_url: str = ""  # LocalStack / testing override

    @field_validator("secret_key")
    @classmethod
    def _secret_key_not_default(cls, v: str) -> str:
        if v.lower().startswith("change_me"):
            raise ValueError("secret_key must be changed from the default placeholder")
        return v

    @model_validator(mode="after")
    def _prod_must_not_have_static_creds(self) -> "Settings":
        if self.app_env == "production" and (
            self.aws_access_key_id or self.aws_secret_access_key
        ):
            raise ValueError(
                "Static AWS credentials must not be set in production; use IAM roles."
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton settings instance (cached after first call)."""
    return Settings()

```

### `backend/app/core/database.py`
```python
"""Async SQLAlchemy engine + session factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


def _build_engine() -> "sqlalchemy.ext.asyncio.AsyncEngine":  # type: ignore[name-defined]
    settings = get_settings()
    connect_args: dict[str, object] = {}
    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_async_engine(
        settings.database_url,
        echo=settings.app_env == "development",
        pool_pre_ping=True,
        connect_args=connect_args,
    )


engine = _build_engine()

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

```

### `backend/app/core/security.py`
```python
"""Security utilities: JWT encoding/decoding, password hashing."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def create_access_token(subject: str | int, extra_claims: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(UTC),
        **(extra_claims or {}),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc

```

### `backend/app/dependencies/__init__.py`
```python
"""Dependencies package."""

```

### `backend/app/dependencies/auth.py`
```python
"""FastAPI authentication dependencies.

get_current_user — validates Bearer JWT and returns the authenticated User.
"""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
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
    """Validate Bearer JWT and return the corresponding active User.

    Raises HTTP 401 for invalid/expired tokens.
    Raises HTTP 403 for inactive accounts.
    """
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        raw_sub = payload.get("sub")
        if raw_sub is None:
            raise ValueError("Missing 'sub' claim")
        user_id = uuid.UUID(str(raw_sub))
    except (ValueError, Exception) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive account.",
        )
    return user

```

### `backend/app/main.py`
```python
"""FastAPI application entry-point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import engine
from app.routers.media_router import router as media_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Validate settings at startup — raises on bad config
    get_settings()
    yield
    # Graceful shutdown: dispose the async engine connection pool
    await engine.dispose()


app = FastAPI(
    title="Backend API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── Global exception handlers ──────────────────────────────────────────────────


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a generic 500 without leaking internals (OWASP A05)."""
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


# ── Routers ────────────────────────────────────────────────────────────────────

app.include_router(media_router, prefix="/api/v1")


# ── Health / readiness ─────────────────────────────────────────────────────────


@app.get("/health", tags=["ops"], include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}

```

### `backend/app/models/__init__.py`
```python
"""Models package — import all ORM models here so Alembic autogenerate sees them."""

from app.models.media_asset import AssetStatus, MediaAsset  # noqa: F401
from app.models.user import User  # noqa: F401

__all__ = ["User", "MediaAsset", "AssetStatus"]

```

### `backend/app/models/media_asset.py`
```python
"""MediaAsset ORM model — tracks S3 objects (e.g., user avatars)."""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AssetStatus(str, enum.Enum):
    """Lifecycle of a media asset upload."""

    pending = "pending"      # Presigned URL issued; upload not yet confirmed
    confirmed = "confirmed"  # Client confirmed PUT succeeded
    deleted = "deleted"      # Soft-deleted; S3 object will be expired by lifecycle rule


class MediaAsset(Base):
    """Persisted record for every issued presigned upload slot."""

    __tablename__ = "media_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Logical purpose — 'avatar' is the only value defined so far; extensible.
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False, default="avatar")
    # S3 object key — deterministic, never contains PII
    s3_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    # Declared size (bytes) from the upload request — not yet verified from S3 ETag
    declared_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[AssetStatus] = mapped_column(
        Enum(AssetStatus, name="assetstatus"), nullable=False, default=AssetStatus.pending
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    owner: Mapped["User"] = relationship("User", back_populates="media_assets")  # noqa: F821

```

### `backend/app/models/user.py`
```python
"""User ORM model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationship to media assets owned by this user
    media_assets: Mapped[list["MediaAsset"]] = relationship(  # noqa: F821
        "MediaAsset", back_populates="owner", cascade="all, delete-orphan"
    )

```

### `backend/app/routers/__init__.py`
```python
"""Routers package."""

```

### `backend/app/routers/media_router.py`
```python
"""Media / avatar router - pre-signed URL endpoints (IF-013).

Routes:
  POST /api/v1/media/avatars/upload-url          - issue presigned PUT URL
  POST /api/v1/media/avatars/{asset_id}/confirm  - confirm successful PUT
  GET  /api/v1/media/avatars/{asset_id}/download-url - issue presigned GET URL
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status  # noqa: B008
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.media.s3_client import get_s3_client
from app.services.media.schemas import (
    AvatarConfirmResponse,
    AvatarGetResponse,
    AvatarUploadRequest,
    AvatarUploadResponse,
)
from app.services.media.service import MediaService

router = APIRouter(prefix="/media/avatars", tags=["media"])


def _build_service(
    db: AsyncSession = Depends(get_db),  # noqa: B008
    s3_client: object = Depends(get_s3_client),  # noqa: B008
) -> MediaService:
    return MediaService(db=db, s3_client=s3_client)


@router.post(
    "/upload-url",
    response_model=AvatarUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue a pre-signed PUT URL for avatar upload",
    description=(
        "Returns a time-limited, content-type-locked presigned POST URL targeting a "
        "private S3 bucket. The client must PUT/POST to the returned URL within the "
        "expiry window and then call /confirm to activate the asset."
    ),
)
async def request_avatar_upload_url(
    body: AvatarUploadRequest,
    current_user: User = Depends(get_current_user),  # noqa: B008
    service: MediaService = Depends(_build_service),  # noqa: B008
) -> AvatarUploadResponse:
    try:
        return await service.issue_avatar_upload_url(current_user.id, body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.post(
    "/{asset_id}/confirm",
    response_model=AvatarConfirmResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm a successful avatar upload",
    description=(
        "Transitions the asset from 'pending' to 'confirmed'. "
        "Call this after the S3 PUT/POST succeeds."
    ),
)
async def confirm_avatar_upload(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),  # noqa: B008
    service: MediaService = Depends(_build_service),  # noqa: B008
) -> AvatarConfirmResponse:
    try:
        return await service.confirm_avatar_upload(current_user.id, asset_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc


@router.get(
    "/{asset_id}/download-url",
    response_model=AvatarGetResponse,
    status_code=status.HTTP_200_OK,
    summary="Issue a pre-signed GET URL for avatar download",
    description=(
        "Returns a time-limited presigned GET URL. "
        "Only confirmed assets owned by the requesting user are accessible."
    ),
)
async def request_avatar_download_url(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),  # noqa: B008
    service: MediaService = Depends(_build_service),  # noqa: B008
) -> AvatarGetResponse:
    try:
        return await service.issue_avatar_get_url(current_user.id, asset_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc

```

### `backend/app/services/__init__.py`
```python
"""Services package."""

```

### `backend/app/services/media/__init__.py`
```python
"""Media services package."""

from app.services.media.service import MediaService  # noqa: F401
from app.services.media.schemas import (  # noqa: F401
    ALLOWED_CONTENT_TYPES,
    AvatarConfirmResponse,
    AvatarGetResponse,
    AvatarUploadRequest,
    AvatarUploadResponse,
)

```

### `backend/app/services/media/s3_client.py`
```python
"""S3 client factory — injectable, respects Settings.

Production: boto3 uses IAM instance role / ECS task role (no static creds).
Testing:    Caller injects a mock/stub via override_s3_client().
LocalStack: Set AWS_ENDPOINT_URL in environment.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING, Any

import boto3
from botocore.config import Config

from app.core.config import get_settings

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client  # only available when boto3-stubs[s3] is installed


def _make_s3_client() -> Any:
    """Build a real boto3 S3 client from settings."""
    settings = get_settings()

    kwargs: dict[str, Any] = {
        "region_name": settings.aws_region,
        "config": Config(
            signature_version="s3v4",
            retries={"max_attempts": 3, "mode": "standard"},
            connect_timeout=5,
            read_timeout=10,
        ),
    }
    # Static credentials only for local/CI overrides — production uses IAM roles
    if settings.aws_access_key_id:
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    if settings.aws_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_endpoint_url

    return boto3.client("s3", **kwargs)


# Module-level singleton — replaced in tests via dependency override
_s3_client: Any = None


def get_s3_client() -> Generator[Any, None, None]:
    """FastAPI dependency that yields the S3 client singleton."""
    global _s3_client  # noqa: PLW0603
    if _s3_client is None:
        _s3_client = _make_s3_client()
    yield _s3_client


def override_s3_client(client: Any) -> None:
    """Test helper — inject a pre-configured stub/mock."""
    global _s3_client  # noqa: PLW0603
    _s3_client = client


def reset_s3_client() -> None:
    """Test helper — restore the real factory."""
    global _s3_client  # noqa: PLW0603
    _s3_client = None

```

### `backend/app/services/media/schemas.py`
```python
"""Pydantic schemas for the media/avatar presigned-URL API.

Keeps request, response, and persistence models separate (IF-013).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

# ── Constants ──────────────────────────────────────────────────────────────────

#: Allowed MIME types for avatar uploads.
ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/gif"}
)

#: Hard cap — must not exceed Settings.avatar_max_size_bytes.
#: This value is used for schema validation (defaults to 5 MiB);
#: the authoritative limit comes from Settings at runtime.
_DEFAULT_MAX_SIZE_BYTES: int = 5_242_880  # 5 MiB


# ── Request schemas ────────────────────────────────────────────────────────────


class AvatarUploadRequest(BaseModel):
    """Body sent by the client to request a presigned PUT URL."""

    content_type: Annotated[str, Field(description="MIME type of the image to be uploaded")]
    size_bytes: Annotated[
        int,
        Field(gt=0, le=_DEFAULT_MAX_SIZE_BYTES, description="Declared file size in bytes"),
    ]

    @field_validator("content_type")
    @classmethod
    def _content_type_must_be_allowed(cls, v: str) -> str:
        normalised = v.strip().lower()
        if normalised not in ALLOWED_CONTENT_TYPES:
            raise ValueError(
                f"content_type '{v}' is not permitted. "
                f"Allowed: {sorted(ALLOWED_CONTENT_TYPES)}"
            )
        return normalised


# ── Response schemas ───────────────────────────────────────────────────────────


class AvatarUploadResponse(BaseModel):
    """Returned to the client after the presigned PUT URL is issued."""

    asset_id: uuid.UUID = Field(description="Opaque ID for this upload slot")
    upload_url: str = Field(description="Time-limited presigned PUT URL")
    expires_in_seconds: int = Field(description="Seconds until the presigned URL expires")
    s3_key: str = Field(description="S3 object key — needed to confirm the upload")
    content_type: str = Field(description="Content-Type the PUT request must use")
    max_size_bytes: int = Field(description="Maximum allowed Content-Length for the PUT")


class AvatarGetResponse(BaseModel):
    """Returned when the client requests a presigned GET (download) URL."""

    asset_id: uuid.UUID
    download_url: str = Field(description="Time-limited presigned GET URL")
    expires_in_seconds: int
    content_type: str


class AvatarConfirmResponse(BaseModel):
    """Returned after the client confirms a successful PUT."""

    asset_id: uuid.UUID
    status: str  # "confirmed"
    message: str

```

### `backend/app/services/media/service.py`
```python
"""Media service - pre-signed PUT/GET URL issuance, asset lifecycle.

Security invariants (AC: TASK-026):
  - Bucket NEVER has a public ACL. ACL param is intentionally absent from
    generate_presigned_url calls; access is purely via signed URLs.
  - URLs are time-limited (configurable, 60-900 s for PUT, 60-3600 s for GET).
  - Content-Type and Content-Length are bound inside the presigned conditions
    via a presigned POST policy (generate_presigned_post) so the caller cannot
    swap the content type or exceed the declared size after the URL is issued.
  - S3 key includes the authenticated user-id to prevent path traversal.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.media_asset import AssetStatus, MediaAsset
from app.services.media.schemas import (
    ALLOWED_CONTENT_TYPES,
    AvatarConfirmResponse,
    AvatarGetResponse,
    AvatarUploadRequest,
    AvatarUploadResponse,
)


def _build_s3_key(user_id: uuid.UUID, asset_id: uuid.UUID) -> str:
    """Return a deterministic, ownership-scoped S3 object key.

    Format: avatars/{user_id}/{asset_id}
    Contains no PII; scoped to the user so S3 bucket policies can
    enforce per-user prefix isolation.
    """
    return f"avatars/{user_id}/{asset_id}"


class MediaService:
    """Domain service for media asset lifecycle operations."""

    def __init__(self, db: AsyncSession, s3_client: Any) -> None:
        self._db = db
        self._s3 = s3_client

    # ── PUT (upload) ───────────────────────────────────────────────────────────

    async def issue_avatar_upload_url(
        self,
        user_id: uuid.UUID,
        request: AvatarUploadRequest,
    ) -> AvatarUploadResponse:
        """Issue a time-limited presigned POST for avatar upload.

        Uses generate_presigned_post so that content-type AND size constraints
        are embedded in the S3 policy document that AWS validates server-side.
        The client cannot bypass them after signing.

        AC compliance:
          - Private bucket: no ACL field in conditions; bucket default (private) applies.
          - No public ACL: ACL is explicitly excluded from presigned conditions.
          - Time-limited URL: ExpiresIn = settings.avatar_presign_put_expires_seconds.
          - Content-type validation: locked to the declared content_type.
          - Size validation: locked to [1, declared_size_bytes].
        """
        settings = get_settings()

        # Runtime size check (belt-and-suspenders on top of Pydantic schema validator)
        if request.size_bytes > settings.avatar_max_size_bytes:
            raise ValueError(
                f"size_bytes {request.size_bytes} exceeds maximum "
                f"{settings.avatar_max_size_bytes} bytes."
            )

        if request.content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError(f"content_type '{request.content_type}' is not permitted.")

        asset_id = uuid.uuid4()
        s3_key = _build_s3_key(user_id, asset_id)

        # Persist the pending record BEFORE calling S3 so the DB row always
        # exists when we return the presigned URL to the client.
        asset = MediaAsset(
            id=asset_id,
            owner_id=user_id,
            asset_type="avatar",
            s3_key=s3_key,
            content_type=request.content_type,
            declared_size_bytes=request.size_bytes,
            status=AssetStatus.pending,
        )
        self._db.add(asset)
        await self._db.commit()
        await self._db.refresh(asset)

        # Generate presigned POST -- conditions enforce content-type + size
        presigned = self._s3.generate_presigned_post(
            Bucket=settings.s3_avatar_bucket,
            Key=s3_key,
            Fields={"Content-Type": request.content_type},
            Conditions=[
                {"Content-Type": request.content_type},
                ["content-length-range", 1, request.size_bytes],
                # No ACL condition -> bucket default private ACL applies
            ],
            ExpiresIn=settings.avatar_presign_put_expires_seconds,
        )

        return AvatarUploadResponse(
            asset_id=asset_id,
            upload_url=presigned["url"],
            expires_in_seconds=settings.avatar_presign_put_expires_seconds,
            s3_key=s3_key,
            content_type=request.content_type,
            max_size_bytes=request.size_bytes,
        )

    # ── GET (download) ─────────────────────────────────────────────────────────

    async def issue_avatar_get_url(
        self,
        user_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> AvatarGetResponse:
        """Issue a time-limited presigned GET URL for an owned, confirmed asset.

        Enforces resource-ownership: the requesting user must own the asset.
        Only confirmed assets are accessible (pending/deleted are rejected).
        """
        settings = get_settings()
        asset = await self._get_owned_confirmed_asset(user_id, asset_id)

        presigned_url: str = self._s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.s3_avatar_bucket,
                "Key": asset.s3_key,
                "ResponseContentType": asset.content_type,
            },
            ExpiresIn=settings.avatar_presign_get_expires_seconds,
        )

        return AvatarGetResponse(
            asset_id=asset.id,
            download_url=presigned_url,
            expires_in_seconds=settings.avatar_presign_get_expires_seconds,
            content_type=asset.content_type,
        )

    # ── Confirm ────────────────────────────────────────────────────────────────

    async def confirm_avatar_upload(
        self,
        user_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> AvatarConfirmResponse:
        """Transition a pending asset to confirmed after the client PUT to S3.

        State machine: pending -> confirmed (only legal transition from pending).
        """
        asset = await self._get_owned_asset(user_id, asset_id)

        if asset.status != AssetStatus.pending:
            raise ValueError(
                f"Asset {asset_id} cannot be confirmed from status '{asset.status.value}'. "
                "Only pending assets may be confirmed."
            )

        asset.status = AssetStatus.confirmed
        asset.updated_at = datetime.now(UTC)
        await self._db.commit()
        await self._db.refresh(asset)

        return AvatarConfirmResponse(
            asset_id=asset.id,
            status="confirmed",
            message="Avatar upload confirmed successfully.",
        )

    # ── Internal helpers ───────────────────────────────────────────────────────

    async def _get_owned_asset(
        self, user_id: uuid.UUID, asset_id: uuid.UUID
    ) -> MediaAsset:
        result = await self._db.execute(
            select(MediaAsset).where(
                MediaAsset.id == asset_id,
                MediaAsset.owner_id == user_id,
            )
        )
        asset = result.scalar_one_or_none()
        if asset is None:
            raise LookupError(f"Asset {asset_id} not found for user {user_id}.")
        return asset

    async def _get_owned_confirmed_asset(
        self, user_id: uuid.UUID, asset_id: uuid.UUID
    ) -> MediaAsset:
        asset = await self._get_owned_asset(user_id, asset_id)
        if asset.status != AssetStatus.confirmed:
            raise PermissionError(
                f"Asset {asset_id} is not confirmed (status: {asset.status.value})."
            )
        return asset

```

### `backend/pyproject.toml`
```toml
[build-system]
requires = ["setuptools>=68,<70", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.141.1",
    "pydantic>=2.13.4",
    "pydantic-settings>=2.14.2",
    "sqlalchemy>=2.0.31",
    "alembic>=1.13.2",
    "asyncpg>=0.30.0",
    "aiosqlite>=0.20.0",
    "boto3>=1.35.95",
    "botocore>=1.35.99",
    "python-jose[cryptography]>=3.3.0",
    "passlib>=1.7.4",
    "python-multipart>=0.0.32",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.2",
    "pytest-asyncio>=0.23.7",
    "mypy>=1.13.0",
    "ruff>=0.8.4",
    "boto3-stubs[s3]",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --tb=short"

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "C4", "SIM", "RUF"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]
ignore_missing_imports = true

[tool.setuptools.packages.find]
where = ["."]
include = ["app*"]

```

### `backend/tests/__init__.py`
```python
"""Tests package."""

```

### `backend/tests/conftest.py`
```python
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

```

### `backend/tests/test_media_router.py`
```python
"""Integration tests for the media router -- HTTP layer via HTTPX ASGITransport.

VER-021 coverage (HTTP endpoints):
  - POST /upload-url -> 201, presigned URL returned
  - POST /upload-url -> 401/403 without token
  - POST /upload-url -> 422 for bad content-type
  - POST /upload-url -> 422 for oversized size_bytes
  - POST /{asset_id}/confirm -> 200 pending -> confirmed
  - POST /{asset_id}/confirm -> 404 unknown asset
  - POST /{asset_id}/confirm -> 409 already confirmed
  - GET  /{asset_id}/download-url -> 200 for confirmed asset
  - GET  /{asset_id}/download-url -> 403 for pending asset
  - GET  /{asset_id}/download-url -> 404 unknown asset
  - Cross-user: another user cannot GET our download URL
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app as _app
from app.models.media_asset import AssetStatus, MediaAsset
from app.models.user import User
from app.services.media.s3_client import get_s3_client
from app.services.media.service import _build_s3_key


# ── Helpers ────────────────────────────────────────────────────────────────────


async def _make_confirmed_asset(
    db: AsyncSession, user: User, content_type: str = "image/jpeg"
) -> MediaAsset:
    asset_id = uuid.uuid4()
    asset = MediaAsset(
        id=asset_id,
        owner_id=user.id,
        asset_type="avatar",
        s3_key=_build_s3_key(user.id, asset_id),
        content_type=content_type,
        declared_size_bytes=200_000,
        status=AssetStatus.confirmed,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


async def _make_pending_asset(db: AsyncSession, user: User) -> MediaAsset:
    asset_id = uuid.uuid4()
    asset = MediaAsset(
        id=asset_id,
        owner_id=user.id,
        asset_type="avatar",
        s3_key=_build_s3_key(user.id, asset_id),
        content_type="image/jpeg",
        declared_size_bytes=100_000,
        status=AssetStatus.pending,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


# ── Upload URL tests ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upload_url_returns_201(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/media/avatars/upload-url",
        json={"content_type": "image/jpeg", "size_bytes": 500_000},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "upload_url" in body
    assert "asset_id" in body
    assert body["expires_in_seconds"] == 300
    assert body["content_type"] == "image/jpeg"


@pytest.mark.asyncio
async def test_upload_url_requires_auth(
    db_session: AsyncSession,
    mock_s3: MagicMock,
) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_app),
        base_url="http://testserver",
    ) as ac:
        resp = await ac.post(
            "/api/v1/media/avatars/upload-url",
            json={"content_type": "image/jpeg", "size_bytes": 100_000},
        )
    assert resp.status_code in {401, 403}


@pytest.mark.asyncio
async def test_upload_url_rejects_invalid_content_type(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/media/avatars/upload-url",
        json={"content_type": "application/pdf", "size_bytes": 500_000},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_upload_url_rejects_oversized_file(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/media/avatars/upload-url",
        json={"content_type": "image/jpeg", "size_bytes": 99_999_999},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_upload_url_response_has_no_public_acl(
    client: AsyncClient, mock_s3: MagicMock
) -> None:
    """Ensure no ACL-related field is propagated back to the client."""
    await client.post(
        "/api/v1/media/avatars/upload-url",
        json={"content_type": "image/jpeg", "size_bytes": 500_000},
    )
    call_kwargs = mock_s3.generate_presigned_post.call_args[1]
    conditions = call_kwargs.get("Conditions", [])
    for cond in conditions:
        if isinstance(cond, dict):
            assert "acl" not in {k.lower() for k in cond}


# ── Confirm tests ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_confirm_pending_asset_returns_200(
    client: AsyncClient, db_session: AsyncSession, test_user: User
) -> None:
    asset = await _make_pending_asset(db_session, test_user)
    resp = await client.post(f"/api/v1/media/avatars/{asset.id}/confirm")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "confirmed"
    assert uuid.UUID(body["asset_id"]) == asset.id


@pytest.mark.asyncio
async def test_confirm_unknown_asset_returns_404(client: AsyncClient) -> None:
    resp = await client.post(f"/api/v1/media/avatars/{uuid.uuid4()}/confirm")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_confirm_already_confirmed_returns_409(
    client: AsyncClient, db_session: AsyncSession, test_user: User
) -> None:
    asset = await _make_confirmed_asset(db_session, test_user)
    resp = await client.post(f"/api/v1/media/avatars/{asset.id}/confirm")
    assert resp.status_code == 409


# ── Download URL tests ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_download_url_confirmed_asset_returns_200(
    client: AsyncClient, db_session: AsyncSession, test_user: User
) -> None:
    asset = await _make_confirmed_asset(db_session, test_user)
    resp = await client.get(f"/api/v1/media/avatars/{asset.id}/download-url")
    assert resp.status_code == 200
    body = resp.json()
    assert "download_url" in body
    assert body["expires_in_seconds"] == 900


@pytest.mark.asyncio
async def test_download_url_pending_asset_returns_403(
    client: AsyncClient, db_session: AsyncSession, test_user: User
) -> None:
    asset = await _make_pending_asset(db_session, test_user)
    resp = await client.get(f"/api/v1/media/avatars/{asset.id}/download-url")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_download_url_unknown_asset_returns_404(client: AsyncClient) -> None:
    resp = await client.get(f"/api/v1/media/avatars/{uuid.uuid4()}/download-url")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_download_url_cross_user_denied(
    db_session: AsyncSession,
    mock_s3: MagicMock,
) -> None:
    """Another authenticated user must not access a different user's asset."""
    owner = User(
        id=uuid.uuid4(),
        email="owner@example.com",
        hashed_password=hash_password("pw"),
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    attacker = User(
        id=uuid.uuid4(),
        email="attacker@example.com",
        hashed_password=hash_password("pw"),
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add_all([owner, attacker])
    await db_session.commit()

    asset = await _make_confirmed_asset(db_session, owner)

    async def _db_override() -> Any:
        yield db_session

    def _s3_override() -> Any:
        yield mock_s3

    _app.dependency_overrides[get_db] = _db_override
    _app.dependency_overrides[get_s3_client] = _s3_override

    attacker_token = create_access_token(str(attacker.id))
    async with AsyncClient(
        transport=ASGITransport(app=_app),
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {attacker_token}"},
    ) as ac:
        resp = await ac.get(f"/api/v1/media/avatars/{asset.id}/download-url")

    _app.dependency_overrides.clear()
    assert resp.status_code == 404, "Cross-user asset access must return 404"

```

### `backend/tests/test_media_schemas.py`
```python
"""Schema validation unit tests — AvatarUploadRequest.

VER-021: content-type allow-list and size-limit validations.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.services.media.schemas import ALLOWED_CONTENT_TYPES, AvatarUploadRequest


@pytest.mark.parametrize("ct", sorted(ALLOWED_CONTENT_TYPES))
def test_allowed_content_types_accepted(ct: str) -> None:
    req = AvatarUploadRequest(content_type=ct, size_bytes=100_000)
    assert req.content_type == ct


@pytest.mark.parametrize(
    "ct",
    ["application/pdf", "text/html", "image/tiff", "image/bmp", "application/octet-stream"],
)
def test_disallowed_content_types_rejected(ct: str) -> None:
    with pytest.raises(ValidationError, match="not permitted"):
        AvatarUploadRequest(content_type=ct, size_bytes=100_000)


def test_content_type_normalised_to_lowercase() -> None:
    req = AvatarUploadRequest(content_type="Image/JPEG", size_bytes=1000)
    assert req.content_type == "image/jpeg"


def test_size_zero_rejected() -> None:
    with pytest.raises(ValidationError):
        AvatarUploadRequest(content_type="image/jpeg", size_bytes=0)


def test_size_at_max_accepted() -> None:
    req = AvatarUploadRequest(content_type="image/jpeg", size_bytes=5_242_880)
    assert req.size_bytes == 5_242_880


def test_size_above_max_rejected() -> None:
    with pytest.raises(ValidationError):
        AvatarUploadRequest(content_type="image/jpeg", size_bytes=5_242_881)


def test_negative_size_rejected() -> None:
    with pytest.raises(ValidationError):
        AvatarUploadRequest(content_type="image/jpeg", size_bytes=-1)

```

### `backend/tests/test_media_service.py`
```python
"""Unit tests for MediaService -- no HTTP layer, direct service calls.

VER-021 coverage:
  - Presigned POST issued with correct bucket / key / content-type conditions
  - Private bucket: no ACL field in presigned conditions
  - Time-limited URL: ExpiresIn matches settings
  - Content-type validation rejects disallowed types
  - Size validation rejects oversized declarations
  - GET URL only issued for confirmed, owned assets
  - Cross-user access denied (ownership predicate)
  - State machine: only pending->confirmed is legal
  - State machine: confirmed->confirmed is rejected
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.media_asset import AssetStatus, MediaAsset
from app.models.user import User
from app.services.media.schemas import AvatarUploadRequest
from app.services.media.service import MediaService, _build_s3_key


# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_s3_mock() -> MagicMock:
    m = MagicMock()
    m.generate_presigned_post.return_value = {
        "url": "https://bucket.s3.amazonaws.com/",
        "fields": {"key": "k", "Content-Type": "image/jpeg"},
    }
    m.generate_presigned_url.return_value = "https://bucket.s3.amazonaws.com/key?sig=x"
    return m


async def _create_user(db: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@example.com",
        hashed_password=hash_password("pw"),
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _create_asset(
    db: AsyncSession,
    owner_id: uuid.UUID,
    status: AssetStatus = AssetStatus.pending,
) -> MediaAsset:
    asset_id = uuid.uuid4()
    asset = MediaAsset(
        id=asset_id,
        owner_id=owner_id,
        asset_type="avatar",
        s3_key=_build_s3_key(owner_id, asset_id),
        content_type="image/jpeg",
        declared_size_bytes=100_000,
        status=status,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


# ── Tests: issue_avatar_upload_url ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_issue_upload_url_success(db_session: AsyncSession) -> None:
    s3 = _make_s3_mock()
    user = await _create_user(db_session)
    svc = MediaService(db=db_session, s3_client=s3)
    req = AvatarUploadRequest(content_type="image/jpeg", size_bytes=500_000)

    resp = await svc.issue_avatar_upload_url(user.id, req)

    assert resp.upload_url == "https://bucket.s3.amazonaws.com/"
    assert resp.content_type == "image/jpeg"
    assert resp.expires_in_seconds == 300
    assert resp.max_size_bytes == 500_000


@pytest.mark.asyncio
async def test_issue_upload_url_presigned_post_called_with_correct_params(
    db_session: AsyncSession,
) -> None:
    s3 = _make_s3_mock()
    user = await _create_user(db_session)
    svc = MediaService(db=db_session, s3_client=s3)
    req = AvatarUploadRequest(content_type="image/png", size_bytes=1_000_000)

    await svc.issue_avatar_upload_url(user.id, req)

    s3.generate_presigned_post.assert_called_once()
    call_kwargs = s3.generate_presigned_post.call_args[1]

    assert call_kwargs["Bucket"] == "test-avatar-bucket"
    assert call_kwargs["Fields"]["Content-Type"] == "image/png"
    assert call_kwargs["ExpiresIn"] == 300

    # AC: no ACL in conditions -> bucket default (private) applies
    conditions = call_kwargs["Conditions"]
    for cond in conditions:
        if isinstance(cond, dict):
            assert "acl" not in {k.lower() for k in cond}, (
                "ACL must not be present in presigned conditions (bucket must stay private)"
            )


@pytest.mark.asyncio
async def test_issue_upload_url_persists_pending_asset(db_session: AsyncSession) -> None:
    s3 = _make_s3_mock()
    user = await _create_user(db_session)
    svc = MediaService(db=db_session, s3_client=s3)
    req = AvatarUploadRequest(content_type="image/webp", size_bytes=200_000)

    resp = await svc.issue_avatar_upload_url(user.id, req)

    result = await db_session.execute(
        select(MediaAsset).where(MediaAsset.id == resp.asset_id)
    )
    asset = result.scalar_one()
    assert asset.status == AssetStatus.pending
    assert asset.owner_id == user.id
    assert asset.content_type == "image/webp"


@pytest.mark.asyncio
async def test_issue_upload_url_rejects_disallowed_content_type(
    db_session: AsyncSession,
) -> None:
    with pytest.raises(ValidationError, match="not permitted"):
        AvatarUploadRequest(content_type="application/pdf", size_bytes=1000)


@pytest.mark.asyncio
async def test_issue_upload_url_rejects_oversized_file(db_session: AsyncSession) -> None:
    with pytest.raises(ValidationError):
        AvatarUploadRequest(content_type="image/jpeg", size_bytes=6_000_000)


@pytest.mark.asyncio
async def test_issue_upload_url_s3_key_scoped_to_user(db_session: AsyncSession) -> None:
    s3 = _make_s3_mock()
    user = await _create_user(db_session)
    svc = MediaService(db=db_session, s3_client=s3)
    req = AvatarUploadRequest(content_type="image/jpeg", size_bytes=100_000)

    resp = await svc.issue_avatar_upload_url(user.id, req)

    assert resp.s3_key.startswith(f"avatars/{user.id}/"), (
        "S3 key must be scoped to the owning user"
    )


# ── Tests: issue_avatar_get_url ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_issue_get_url_success(db_session: AsyncSession) -> None:
    s3 = _make_s3_mock()
    user = await _create_user(db_session)
    asset = await _create_asset(db_session, user.id, status=AssetStatus.confirmed)
    svc = MediaService(db=db_session, s3_client=s3)

    resp = await svc.issue_avatar_get_url(user.id, asset.id)

    assert "https://" in resp.download_url
    assert resp.expires_in_seconds == 900
    s3.generate_presigned_url.assert_called_once()
    call_kwargs = s3.generate_presigned_url.call_args[1]
    assert call_kwargs["Params"]["Bucket"] == "test-avatar-bucket"
    assert call_kwargs["Params"]["Key"] == asset.s3_key


@pytest.mark.asyncio
async def test_get_url_rejects_pending_asset(db_session: AsyncSession) -> None:
    s3 = _make_s3_mock()
    user = await _create_user(db_session)
    asset = await _create_asset(db_session, user.id, status=AssetStatus.pending)
    svc = MediaService(db=db_session, s3_client=s3)

    with pytest.raises(PermissionError, match="not confirmed"):
        await svc.issue_avatar_get_url(user.id, asset.id)


@pytest.mark.asyncio
async def test_get_url_denied_for_wrong_user(db_session: AsyncSession) -> None:
    """Cross-user access must be denied (ownership predicate)."""
    s3 = _make_s3_mock()
    owner = await _create_user(db_session)
    attacker = await _create_user(db_session)
    asset = await _create_asset(db_session, owner.id, status=AssetStatus.confirmed)
    svc = MediaService(db=db_session, s3_client=s3)

    with pytest.raises(LookupError):
        await svc.issue_avatar_get_url(attacker.id, asset.id)


# ── Tests: confirm_avatar_upload ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_confirm_transitions_pending_to_confirmed(db_session: AsyncSession) -> None:
    s3 = _make_s3_mock()
    user = await _create_user(db_session)
    asset = await _create_asset(db_session, user.id, status=AssetStatus.pending)
    svc = MediaService(db=db_session, s3_client=s3)

    resp = await svc.confirm_avatar_upload(user.id, asset.id)

    assert resp.status == "confirmed"

    result = await db_session.execute(select(MediaAsset).where(MediaAsset.id == asset.id))
    refreshed = result.scalar_one()
    assert refreshed.status == AssetStatus.confirmed


@pytest.mark.asyncio
async def test_confirm_already_confirmed_is_rejected(db_session: AsyncSession) -> None:
    """State machine: confirmed -> confirmed is an illegal transition."""
    s3 = _make_s3_mock()
    user = await _create_user(db_session)
    asset = await _create_asset(db_session, user.id, status=AssetStatus.confirmed)
    svc = MediaService(db=db_session, s3_client=s3)

    with pytest.raises(ValueError, match="cannot be confirmed from status"):
        await svc.confirm_avatar_upload(user.id, asset.id)


@pytest.mark.asyncio
async def test_confirm_denied_for_wrong_user(db_session: AsyncSession) -> None:
    """Confirm must be rejected when user does not own the asset."""
    s3 = _make_s3_mock()
    owner = await _create_user(db_session)
    attacker = await _create_user(db_session)
    asset = await _create_asset(db_session, owner.id, status=AssetStatus.pending)
    svc = MediaService(db=db_session, s3_client=s3)

    with pytest.raises(LookupError):
        await svc.confirm_avatar_upload(attacker.id, asset.id)

```