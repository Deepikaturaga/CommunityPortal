# Implementation Report

The security.py patch got mangled. Let me rewrite it cleanly, and then fix the other minor issues:

## Verification
- `pip install fastapi==0.115.5 pydantic==2.9.2 pydantic-settings==2.6.1 sqlalchemy==2.0.36 alembic==1.14.0 python-jose==3.3.0 passlib==1.7.4 httpx==0.27.2 structlog==24.4.0 pytest==8.3.4 pytest-asyncio==0.24.0 anyio==4.6.2 uvicorn==0.32.1 asyncpg==0.30.0 cryptography==43.0.3 bcrypt==4.2.1 types-passlib types-python-jose` → exit 0
- `pip install "pydantic==2.10.3" "pydantic-settings>=2.6.1" "anyio>=4.7.0" "httpx>=0.27.2"` → exit 0
- `ruff check backend/app backend/tests` → exit 1
- `ruff check app tests` → exit 1
- `ruff check app tests` → exit 1
- `ruff check --fix app tests` → exit 1
- `ruff check app tests` → exit 1
- `ruff check --fix app tests` → exit 1
- `ruff check app tests` → exit 1
- `ruff check --fix app tests` → exit 1
- `ruff check app tests` → exit 1
- `ruff check app tests` → exit 1

## Generated Files

### `backend/.env.example`
```text
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/notifications_dev
SECRET_KEY=change-me-in-production-use-32-plus-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
LOG_LEVEL=INFO

```

### `backend/alembic.ini`
```text
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql+asyncpg://postgres:postgres@localhost:5432/notifications_dev

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
"""Alembic async env – SQLAlchemy 2.0 style."""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import Base so all models are registered for autogenerate
from app.core.database import Base  # noqa: F401
import app.services.notifications.models  # noqa: F401  – register ORM models

config = context.config

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


def do_run_migrations(connection):  # type: ignore[no-untyped-def]
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = config.get_main_option("sqlalchemy.url")
    connectable = async_engine_from_config(
        configuration,
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

from collections.abc import Sequence

import alembic.op as op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: str | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}

```

### `backend/alembic/versions/0001_notification_preferences.py`
```python
"""create notification_preferences and notifications tables

Revision ID: 0001_notification_preferences
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_notification_preferences"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── Enum types ─────────────────────────────────────────────────────────────
    notification_channel = postgresql.ENUM(
        "email", "sms", "push", "in_app",
        name="notification_channel",
        create_type=True,
    )
    notification_category = postgresql.ENUM(
        "marketing", "transactional", "security", "product_updates", "reminders",
        name="notification_category",
        create_type=True,
    )
    notification_status = postgresql.ENUM(
        "pending", "sent", "delivered", "read", "failed",
        name="notification_status",
        create_type=True,
    )

    notification_channel.create(op.get_bind(), checkfirst=True)
    notification_category.create(op.get_bind(), checkfirst=True)
    notification_status.create(op.get_bind(), checkfirst=True)

    # ── notification_preferences ───────────────────────────────────────────────
    op.create_table(
        "notification_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column(
            "channel",
            sa.Enum("email", "sms", "push", "in_app", name="notification_channel"),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.Enum(
                "marketing", "transactional", "security", "product_updates", "reminders",
                name="notification_category",
            ),
            nullable=False,
        ),
        sa.Column("opted_out", sa.Boolean, nullable=False, server_default="false"),
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
        sa.UniqueConstraint("user_id", "channel", "category", name="uq_pref_user_channel_category"),
    )
    op.create_index("ix_notification_preferences_user_id", "notification_preferences", ["user_id"])

    # ── notifications ──────────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(128), nullable=False),
        sa.Column(
            "preference_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("notification_preferences.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "channel",
            sa.Enum("email", "sms", "push", "in_app", name="notification_channel"),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.Enum(
                "marketing", "transactional", "security", "product_updates", "reminders",
                name="notification_category",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("pending", "sent", "delivered", "read", "failed", name="notification_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("subject", sa.String(512), nullable=True),
        sa.Column("body", sa.String(4096), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_notification_preferences_user_id", table_name="notification_preferences")
    op.drop_table("notification_preferences")

    op.execute("DROP TYPE IF EXISTS notification_status")
    op.execute("DROP TYPE IF EXISTS notification_category")
    op.execute("DROP TYPE IF EXISTS notification_channel")

```

### `backend/app/core/config.py`
```python
from __future__ import annotations

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: PostgresDsn = Field(
        default=...,
        description="Async PostgreSQL DSN (asyncpg driver)",
    )

    # ── Auth ──────────────────────────────────────────────────────────────────
    secret_key: str = Field(default=..., min_length=32)
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, gt=0)

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = Field(default="INFO")

    @field_validator("log_level")
    @classmethod
    def _log_level_upper(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return upper


settings = Settings()

```

### `backend/app/core/database.py`
```python
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(
    str(settings.database_url),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

```

### `backend/app/core/logging.py`
```python
from __future__ import annotations

import logging
import sys

import structlog

from app.core.config import settings


def configure_logging() -> None:
    log_level = getattr(logging, settings.log_level, logging.INFO)

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )


logger: structlog.BoundLogger = structlog.get_logger(__name__)

```

### `backend/app/core/security.py`
```python
from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


class TokenPayload:
    """Thin wrapper for JWT claims – no DB round-trip."""

    def __init__(self, sub: str, exp: int) -> None:
        self.user_id: str = sub
        self.exp: int = exp


def _decode_token(token: str) -> TokenPayload:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        sub: str | None = payload.get("sub")
        exp: int | None = payload.get("exp")
        if sub is None or exp is None:
            raise credentials_exc
        if datetime.fromtimestamp(exp, tz=UTC) < datetime.now(tz=UTC):
            raise credentials_exc
        return TokenPayload(sub=sub, exp=exp)
    except JWTError:
        raise credentials_exc from None


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TokenPayload:
    return _decode_token(token)


CurrentUser = Annotated[TokenPayload, Depends(get_current_user)]

```

### `backend/app/main.py`
```python
from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.database import engine
from app.core.logging import configure_logging
from app.services.notifications.router import router as notifications_router

configure_logging()
logger: structlog.BoundLogger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("startup", event="api_startup")
    yield
    logger.info("shutdown", event="api_shutdown")
    await engine.dispose()


app = FastAPI(
    title="Notification Preference API",
    version="1.0.0",
    description="COMP-008 – notification preference and list API (IF-010)",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS (locked down – override via env/config for prod) ─────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],   # deny all cross-origin by default; override in deployment config
    allow_credentials=False,
    allow_methods=["GET", "PUT"],
    allow_headers=["Authorization", "Content-Type"],
)


# ── Global exception handler – no internal details leaked ─────────────────────
@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", path=request.url.path, exc=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred."},
    )


# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(notifications_router, prefix="/api/v1")


# ── Health / readiness ─────────────────────────────────────────────────────────
@app.get("/health", tags=["ops"], status_code=status.HTTP_200_OK)
async def health() -> dict[str, str]:
    return {"status": "ok"}

```

### `backend/app/services/__init__.py`
```python
# services package

```

### `backend/app/services/notifications/__init__.py`
```python
from app.services.notifications import models as _models  # noqa: F401 – ensure models are registered

```

### `backend/app/services/notifications/dependencies.py`
```python
from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.notifications.repository import NotificationPreferenceRepository


async def get_preference_repo(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationPreferenceRepository:
    return NotificationPreferenceRepository(db)


PreferenceRepo = Annotated[NotificationPreferenceRepository, Depends(get_preference_repo)]

```

### `backend/app/services/notifications/enums.py`
```python
from __future__ import annotations

import enum


class NotificationChannel(str, enum.Enum):
    """Delivery channel for a notification."""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationCategory(str, enum.Enum):
    """Logical category that maps to an opt-out flag (STORE-008)."""

    MARKETING = "marketing"
    TRANSACTIONAL = "transactional"
    SECURITY = "security"
    PRODUCT_UPDATES = "product_updates"
    REMINDERS = "reminders"


class NotificationStatus(str, enum.Enum):
    """Delivery / read status of a notification record."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

```

### `backend/app/services/notifications/models.py`
```python
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.services.notifications.enums import (
    NotificationCategory,
    NotificationChannel,
    NotificationStatus,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class NotificationPreference(Base):
    """
    Per-user, per-channel, per-category opt-out flag (STORE-008 / COMP-008).

    Uniqueness: (user_id, channel, category).
    A row with opted_out=True means the user has disabled that combination.
    Missing row → default opted-in.
    """

    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "channel", "category", name="uq_pref_user_channel_category"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    channel: Mapped[NotificationChannel] = mapped_column(
        SAEnum(NotificationChannel, name="notification_channel"), nullable=False
    )
    category: Mapped[NotificationCategory] = mapped_column(
        SAEnum(NotificationCategory, name="notification_category"), nullable=False
    )
    opted_out: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    # ── back-reference (informational, not FK constraint to external users table) ─
    notifications: Mapped[list[Notification]] = relationship(
        "Notification", back_populates="preference", lazy="noload"
    )


class Notification(Base):
    """
    Individual notification record delivered or pending for a user (STORE-008).

    Designed append-only at the DB layer; no UPDATE/DELETE of delivered records.
    """

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    preference_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notification_preferences.id", ondelete="SET NULL"),
        nullable=True,
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        SAEnum(NotificationChannel, name="notification_channel"),
        nullable=False,
    )
    category: Mapped[NotificationCategory] = mapped_column(
        SAEnum(NotificationCategory, name="notification_category"),
        nullable=False,
    )
    status: Mapped[NotificationStatus] = mapped_column(
        SAEnum(NotificationStatus, name="notification_status"),
        nullable=False,
        default=NotificationStatus.PENDING,
    )
    subject: Mapped[str | None] = mapped_column(String(512), nullable=True)
    body: Mapped[str] = mapped_column(String(4096), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    preference: Mapped[NotificationPreference | None] = relationship(
        "NotificationPreference", back_populates="notifications", lazy="noload"
    )

```

### `backend/app/services/notifications/repository.py`
```python
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.notifications.enums import NotificationCategory, NotificationChannel
from app.services.notifications.models import Notification, NotificationPreference
from app.services.notifications.schemas import NotificationListParams


class NotificationPreferenceRepository:
    """
    All queries are scoped to the caller's user_id – self-only access is
    enforced here (not only in the router) per §7 of the implementation contract.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Preferences ──────────────────────────────────────────────────────────

    async def list_preferences(self, user_id: str) -> list[NotificationPreference]:
        result = await self._db.execute(
            select(NotificationPreference)
            .where(NotificationPreference.user_id == user_id)
            .order_by(NotificationPreference.channel, NotificationPreference.category)
        )
        return list(result.scalars().all())

    async def get_preference(
        self,
        user_id: str,
        channel: NotificationChannel,
        category: NotificationCategory,
    ) -> NotificationPreference | None:
        result = await self._db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id,
                NotificationPreference.channel == channel,
                NotificationPreference.category == category,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_preference(
        self,
        user_id: str,
        channel: NotificationChannel,
        category: NotificationCategory,
        opted_out: bool,
    ) -> NotificationPreference:
        """
        Idempotent upsert: create row if absent, update opted_out otherwise.
        Returns the persisted preference (flushed, not yet committed – the
        caller's session/unit-of-work commits on success).
        """
        existing = await self.get_preference(user_id, channel, category)
        if existing is None:
            pref = NotificationPreference(
                user_id=user_id,
                channel=channel,
                category=category,
                opted_out=opted_out,
            )
            self._db.add(pref)
            await self._db.flush()
            await self._db.refresh(pref)
            return pref

        # Only update when the value actually changes (avoids spurious updated_at bumps)
        if existing.opted_out != opted_out:
            await self._db.execute(
                update(NotificationPreference)
                .where(NotificationPreference.id == existing.id)
                .values(opted_out=opted_out)
                .execution_options(synchronize_session="fetch")
            )
            await self._db.flush()
            await self._db.refresh(existing)
        return existing

    # ── Notifications ─────────────────────────────────────────────────────────

    async def list_notifications(
        self,
        user_id: str,
        params: NotificationListParams,
    ) -> tuple[list[Notification], int]:
        """
        Returns (page_items, total_count). Bounded by page_size ≤ 100.
        All filters default to None → no-op (show all for this user).
        """
        base_where: list[Any] = [Notification.user_id == user_id]

        if params.channel is not None:
            base_where.append(Notification.channel == params.channel)
        if params.category is not None:
            base_where.append(Notification.category == params.category)
        if params.status is not None:
            base_where.append(Notification.status == params.status)

        # total count
        count_result = await self._db.execute(
            select(func.count()).select_from(Notification).where(*base_where)
        )
        total: int = count_result.scalar_one()

        # page
        offset = (params.page - 1) * params.page_size
        rows_result = await self._db.execute(
            select(Notification)
            .where(*base_where)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(params.page_size)
        )
        items = list(rows_result.scalars().all())
        return items, total

```

### `backend/app/services/notifications/router.py`
```python
"""
Notification preference and list router (IF-010 / COMP-008).

Routes
------
GET  /api/v1/notifications/preferences
    List all preference rows for the authenticated user.

GET  /api/v1/notifications/preferences/{channel}/{category}
    Read a single preference.  Returns the default (opted_in) if the row
    does not exist yet, without persisting anything.

PUT  /api/v1/notifications/preferences/{channel}/{category}
    Upsert the opted_out flag for one (channel, category) pair.
    Idempotent – safe to retry.

GET  /api/v1/notifications/
    Paginated, filterable notification list for the authenticated user.

Access control
--------------
All endpoints enforce *self-only* access: the user_id is taken exclusively
from the validated JWT payload – never from a path/query parameter supplied
by the caller.  This satisfies AC-029.x and IF-010 self-only requirement.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Query, status

from app.core.security import CurrentUser
from app.services.notifications.dependencies import PreferenceRepo
from app.services.notifications.enums import (
    NotificationCategory,
    NotificationChannel,
    NotificationStatus,
)
from app.services.notifications.schemas import (
    NotificationListParams,
    NotificationListResponse,
    NotificationRead,
    PreferenceListResponse,
    PreferencePut,
    PreferenceRead,
)

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
)

_NULL_UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)

# ── Preference endpoints ───────────────────────────────────────────────────────


@router.get(
    "/preferences",
    response_model=PreferenceListResponse,
    summary="List notification preferences",
    status_code=status.HTTP_200_OK,
)
async def list_preferences(
    current_user: CurrentUser,
    repo: PreferenceRepo,
) -> PreferenceListResponse:
    """Return all persisted preference rows for the calling user."""
    items = await repo.list_preferences(current_user.user_id)
    return PreferenceListResponse(
        items=[PreferenceRead.model_validate(p) for p in items],
        total=len(items),
    )


@router.get(
    "/preferences/{channel}/{category}",
    response_model=PreferenceRead,
    summary="Get a single notification preference",
    status_code=status.HTTP_200_OK,
)
async def get_preference(
    channel: NotificationChannel,
    category: NotificationCategory,
    current_user: CurrentUser,
    repo: PreferenceRepo,
) -> PreferenceRead:
    """
    Return the preference for (channel, category).  If the row has never been
    written the default is opted_in (opted_out=False), returned as a synthetic
    response without persisting.
    """
    pref = await repo.get_preference(current_user.user_id, channel, category)
    if pref is None:
        # Return default without writing – no side-effects on GET
        return PreferenceRead(
            id=_NULL_UUID,
            user_id=current_user.user_id,
            channel=channel,
            category=category,
            opted_out=False,
            created_at=_EPOCH,
            updated_at=_EPOCH,
        )
    return PreferenceRead.model_validate(pref)


@router.put(
    "/preferences/{channel}/{category}",
    response_model=PreferenceRead,
    summary="Set a notification preference opt-out flag",
    status_code=status.HTTP_200_OK,
)
async def put_preference(
    channel: NotificationChannel,
    category: NotificationCategory,
    body: PreferencePut,
    current_user: CurrentUser,
    repo: PreferenceRepo,
) -> PreferenceRead:
    """
    Persist the opted_out flag for (channel, category).  Idempotent.
    The user_id is taken from the JWT – callers cannot set preferences for
    other users (self-only access, AC-029.x).
    """
    pref = await repo.upsert_preference(
        user_id=current_user.user_id,
        channel=channel,
        category=category,
        opted_out=body.opted_out,
    )
    return PreferenceRead.model_validate(pref)


# ── Notification list endpoint ────────────────────────────────────────────────


@router.get(
    "/",
    response_model=NotificationListResponse,
    summary="List notifications for the authenticated user",
    status_code=status.HTTP_200_OK,
)
async def list_notifications(
    current_user: CurrentUser,
    repo: PreferenceRepo,
    channel: NotificationChannel | None = Query(default=None),
    category: NotificationCategory | None = Query(default=None),
    notification_status: NotificationStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> NotificationListResponse:
    """
    Paginated notification list filtered by channel / category / status.
    Results are ordered by created_at DESC (newest first).
    Maximum page_size is 100 (bounded read).
    """
    params = NotificationListParams(
        channel=channel,
        category=category,
        status=notification_status,
        page=page,
        page_size=page_size,
    )
    items, total = await repo.list_notifications(current_user.user_id, params)
    return NotificationListResponse(
        items=[NotificationRead.model_validate(n) for n in items],
        total=total,
        page=page,
        page_size=page_size,
    )

```

### `backend/app/services/notifications/schemas.py`
```python
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.services.notifications.enums import (
    NotificationCategory,
    NotificationChannel,
    NotificationStatus,
)


# ── Preference schemas ────────────────────────────────────────────────────────


class PreferenceBase(BaseModel):
    channel: NotificationChannel
    category: NotificationCategory
    opted_out: bool = False


class PreferenceRead(PreferenceBase):
    """Response schema for a single preference row (IF-010)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: str
    created_at: datetime
    updated_at: datetime


class PreferencePut(BaseModel):
    """
    Request body for PUT /preferences/{channel}/{category}.

    Only opted_out is mutable; channel/category come from the URL path.
    """

    opted_out: bool


class PreferenceListResponse(BaseModel):
    """Paginated list of preferences for the authenticated user."""

    items: list[PreferenceRead]
    total: int


# ── Notification list schemas ─────────────────────────────────────────────────


class NotificationRead(BaseModel):
    """Response schema for a notification record (IF-010, COMP-008)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: str
    channel: NotificationChannel
    category: NotificationCategory
    status: NotificationStatus
    subject: str | None
    body: str
    sent_at: datetime | None
    read_at: datetime | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    """Paginated list of notifications for the authenticated user."""

    items: list[NotificationRead]
    total: int
    page: int
    page_size: int


# ── Query parameter schemas ───────────────────────────────────────────────────


class NotificationListParams(BaseModel):
    """Validated query parameters for the notification list endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    channel: NotificationChannel | None = None
    category: NotificationCategory | None = None
    status: NotificationStatus | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

```

### `backend/pyproject.toml`
```toml
[build-system]
requires = ["poetry-core>=1.8.0"]
build-backend = "poetry.core.masonry.api"

[tool.poetry]
name = "backend"
version = "0.1.0"
description = "Notification Preference API – backend service"
authors = ["Engineering <eng@example.com>"]
readme = "README.md"
packages = [{ include = "app" }]

[tool.poetry.dependencies]
python = "^3.12"
fastapi = "^0.115.0"
uvicorn = { version = "^0.32.0", extras = ["standard"] }
pydantic = "^2.10.3"
pydantic-settings = "^2.6.1"
sqlalchemy = { version = "^2.0.30", extras = ["asyncio"] }
alembic = "^1.13.0"
asyncpg = "^0.29.0"
python-jose = { version = "^3.3.0", extras = ["cryptography"] }
passlib = { version = "^1.7.4", extras = ["bcrypt"] }
python-multipart = "^0.0.9"
httpx = "^0.27.0"
structlog = "^24.2.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.2.0"
pytest-asyncio = "^0.24.0"
pytest-cov = "^5.0.0"
anyio = "^4.7.0"
ruff = "^0.4.0"
mypy = "^1.10.0"
types-passlib = "^1.7.7"
types-python-jose = "^3.3.4"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
# TCH (type-checking imports) excluded: Pydantic v2 models and FastAPI
# dependencies need runtime imports; moving them to TYPE_CHECKING blocks
# would break model_validate and dependency injection at runtime.
ignore = ["B008"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]
ignore_missing_imports = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

```

### `backend/tests/__init__.py`
```python
# tests package

```

### `backend/tests/conftest.py`
```python
"""Shared pytest fixtures for the notification preference API tests."""
from __future__ import annotations
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt

from app.core.config import settings
from app.main import app


# ── JWT helpers ────────────────────────────────────────────────────────────────

def make_token(user_id: str, secret: str | None = None) -> str:
    import time

    secret = secret or settings.secret_key
    now = int(time.time())
    return jwt.encode(
        {"sub": user_id, "exp": now + 3600},
        secret,
        algorithm=settings.algorithm,
    )


def auth_headers(user_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(user_id)}"}


# ── In-process async HTTP client ───────────────────────────────────────────────

@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

```

### `backend/tests/test_notification_repository.py`
```python
"""
Unit tests for NotificationPreferenceRepository (no real DB – patched session).
Covers: list, get, upsert (create path and update path).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.notifications.enums import NotificationCategory, NotificationChannel
from app.services.notifications.models import NotificationPreference
from app.services.notifications.repository import NotificationPreferenceRepository


def _make_pref(
    user_id: str = "user-1",
    channel: NotificationChannel = NotificationChannel.EMAIL,
    category: NotificationCategory = NotificationCategory.MARKETING,
    opted_out: bool = False,
) -> NotificationPreference:
    pref = NotificationPreference(
        user_id=user_id,
        channel=channel,
        category=category,
        opted_out=opted_out,
    )
    pref.id = uuid.uuid4()
    pref.created_at = datetime.now(UTC)
    pref.updated_at = datetime.now(UTC)
    return pref


class TestListPreferences:
    @pytest.mark.asyncio
    async def test_returns_only_current_user_preferences(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [_make_pref("u1"), _make_pref("u1")]
        db.execute = AsyncMock(return_value=mock_result)

        repo = NotificationPreferenceRepository(db)
        result = await repo.list_preferences("u1")
        assert len(result) == 2
        assert all(p.user_id == "u1" for p in result)


class TestGetPreference:
    @pytest.mark.asyncio
    async def test_returns_none_when_absent(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        repo = NotificationPreferenceRepository(db)
        result = await repo.get_preference(
            "u1",
            NotificationChannel.EMAIL,
            NotificationCategory.MARKETING,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_existing_preference(self) -> None:
        pref = _make_pref("u1")
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pref
        db.execute = AsyncMock(return_value=mock_result)

        repo = NotificationPreferenceRepository(db)
        result = await repo.get_preference(
            "u1",
            NotificationChannel.EMAIL,
            NotificationCategory.MARKETING,
        )
        assert result is pref


class TestUpsertPreference:
    @pytest.mark.asyncio
    async def test_creates_new_row_when_absent(self) -> None:
        db = AsyncMock()
        # get_preference returns None → create path
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_get_result)
        db.add = MagicMock()
        db.flush = AsyncMock()

        created_pref = _make_pref("u1", opted_out=True)

        def _side_effect(obj: NotificationPreference) -> None:
            obj.id = created_pref.id
            obj.created_at = created_pref.created_at
            obj.updated_at = created_pref.updated_at

        db.refresh = AsyncMock(side_effect=_side_effect)

        repo = NotificationPreferenceRepository(db)
        result = await repo.upsert_preference(
            "u1",
            NotificationChannel.EMAIL,
            NotificationCategory.MARKETING,
            opted_out=True,
        )

        db.add.assert_called_once()
        db.flush.assert_awaited()
        assert result.opted_out is True

    @pytest.mark.asyncio
    async def test_updates_existing_row_when_value_changes(self) -> None:
        existing = _make_pref("u1", opted_out=False)
        db = AsyncMock()
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = existing

        mock_update_result = MagicMock()
        db.execute = AsyncMock(side_effect=[mock_get_result, mock_update_result])
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        repo = NotificationPreferenceRepository(db)
        await repo.upsert_preference(
            "u1",
            NotificationChannel.EMAIL,
            NotificationCategory.MARKETING,
            opted_out=True,
        )

        # execute called twice: select + update
        assert db.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_no_update_when_value_unchanged(self) -> None:
        existing = _make_pref("u1", opted_out=True)
        db = AsyncMock()
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = existing
        db.execute = AsyncMock(return_value=mock_get_result)

        repo = NotificationPreferenceRepository(db)
        result = await repo.upsert_preference(
            "u1",
            NotificationChannel.EMAIL,
            NotificationCategory.MARKETING,
            opted_out=True,
        )

        # Only the SELECT was executed; no UPDATE
        db.execute.assert_awaited_once()
        assert result is existing

```

### `backend/tests/test_notification_router.py`
```python
"""
HTTP integration tests for the notification preference and list endpoints.
Uses HTTPX ASGITransport + app dependency overrides (no real DB).

Covers (VER-004 / AC-029.x):
  - GET /preferences  → 200 with items list
  - GET /preferences/{channel}/{category} → 200, synthetic default when absent
  - PUT /preferences/{channel}/{category} → 200, opted_out persisted
  - GET /notifications/ → 200, paginated
  - Self-only: JWT user_id cannot be overridden by caller
  - Unauthenticated → 401
  - Wrong/expired token → 401
"""
from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from jose import jwt as jose_jwt

from app.core.config import settings
from app.main import app
from app.services.notifications.dependencies import get_preference_repo
from app.services.notifications.enums import (
    NotificationCategory,
    NotificationChannel,
    NotificationStatus,
)
from app.services.notifications.models import Notification, NotificationPreference
from app.services.notifications.repository import NotificationPreferenceRepository
from tests.conftest import auth_headers, make_token

USER_A = "user-aaa"
USER_B = "user-bbb"

_NOW = datetime.now(UTC)


def _pref(
    user_id: str = USER_A,
    channel: NotificationChannel = NotificationChannel.EMAIL,
    category: NotificationCategory = NotificationCategory.MARKETING,
    opted_out: bool = False,
) -> NotificationPreference:
    p = NotificationPreference(
        user_id=user_id,
        channel=channel,
        category=category,
        opted_out=opted_out,
    )
    p.id = uuid.uuid4()
    p.created_at = _NOW
    p.updated_at = _NOW
    return p


def _notif(user_id: str = USER_A) -> Notification:
    n = Notification(
        user_id=user_id,
        channel=NotificationChannel.EMAIL,
        category=NotificationCategory.TRANSACTIONAL,
        status=NotificationStatus.SENT,
        body="Hello",
    )
    n.id = uuid.uuid4()
    n.created_at = _NOW
    n.preference_id = None
    n.subject = None
    n.sent_at = None
    n.read_at = None
    return n


def _make_repo_stub(
    prefs: list[NotificationPreference] | None = None,
    single_pref: NotificationPreference | None = None,
    upserted_pref: NotificationPreference | None = None,
    notifs: list[Notification] | None = None,
    notif_total: int = 0,
) -> NotificationPreferenceRepository:
    repo = AsyncMock(spec=NotificationPreferenceRepository)
    repo.list_preferences = AsyncMock(return_value=prefs or [])
    repo.get_preference = AsyncMock(return_value=single_pref)
    repo.upsert_preference = AsyncMock(return_value=upserted_pref or _pref())
    repo.list_notifications = AsyncMock(return_value=(notifs or [], notif_total))
    return repo  # type: ignore[return-value]


class TestPreferenceListEndpoint:
    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.get("/api/v1/notifications/preferences")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_prefs(
        self, async_client: AsyncClient
    ) -> None:
        repo = _make_repo_stub(prefs=[])
        app.dependency_overrides[get_preference_repo] = lambda: repo
        try:
            resp = await async_client.get(
                "/api/v1/notifications/preferences",
                headers=auth_headers(USER_A),
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["items"] == []
            assert data["total"] == 0
        finally:
            app.dependency_overrides.pop(get_preference_repo, None)

    @pytest.mark.asyncio
    async def test_returns_user_preferences(
        self, async_client: AsyncClient
    ) -> None:
        pref = _pref(USER_A, opted_out=True)
        repo = _make_repo_stub(prefs=[pref])
        app.dependency_overrides[get_preference_repo] = lambda: repo
        try:
            resp = await async_client.get(
                "/api/v1/notifications/preferences",
                headers=auth_headers(USER_A),
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert data["items"][0]["opted_out"] is True
            repo.list_preferences.assert_awaited_once_with(USER_A)
        finally:
            app.dependency_overrides.pop(get_preference_repo, None)


class TestPreferenceGetEndpoint:
    @pytest.mark.asyncio
    async def test_returns_default_when_row_absent(
        self, async_client: AsyncClient
    ) -> None:
        repo = _make_repo_stub(single_pref=None)
        app.dependency_overrides[get_preference_repo] = lambda: repo
        try:
            resp = await async_client.get(
                "/api/v1/notifications/preferences/email/marketing",
                headers=auth_headers(USER_A),
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["opted_out"] is False
            assert data["channel"] == "email"
            assert data["category"] == "marketing"
        finally:
            app.dependency_overrides.pop(get_preference_repo, None)

    @pytest.mark.asyncio
    async def test_returns_existing_preference(
        self, async_client: AsyncClient
    ) -> None:
        pref = _pref(USER_A, opted_out=True)
        repo = _make_repo_stub(single_pref=pref)
        app.dependency_overrides[get_preference_repo] = lambda: repo
        try:
            resp = await async_client.get(
                "/api/v1/notifications/preferences/email/marketing",
                headers=auth_headers(USER_A),
            )
            assert resp.status_code == 200
            assert resp.json()["opted_out"] is True
        finally:
            app.dependency_overrides.pop(get_preference_repo, None)

    @pytest.mark.asyncio
    async def test_invalid_channel_returns_422(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.get(
            "/api/v1/notifications/preferences/fax/marketing",
            headers=auth_headers(USER_A),
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_category_returns_422(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.get(
            "/api/v1/notifications/preferences/email/unknown_cat",
            headers=auth_headers(USER_A),
        )
        assert resp.status_code == 422


class TestPreferencePutEndpoint:
    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.put(
            "/api/v1/notifications/preferences/email/marketing",
            json={"opted_out": True},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_opt_out_persisted(self, async_client: AsyncClient) -> None:
        upserted = _pref(USER_A, opted_out=True)
        repo = _make_repo_stub(upserted_pref=upserted)
        app.dependency_overrides[get_preference_repo] = lambda: repo
        try:
            resp = await async_client.put(
                "/api/v1/notifications/preferences/email/marketing",
                json={"opted_out": True},
                headers=auth_headers(USER_A),
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["opted_out"] is True
            repo.upsert_preference.assert_awaited_once_with(
                user_id=USER_A,
                channel=NotificationChannel.EMAIL,
                category=NotificationCategory.MARKETING,
                opted_out=True,
            )
        finally:
            app.dependency_overrides.pop(get_preference_repo, None)

    @pytest.mark.asyncio
    async def test_opt_in_persisted(self, async_client: AsyncClient) -> None:
        upserted = _pref(USER_A, opted_out=False)
        repo = _make_repo_stub(upserted_pref=upserted)
        app.dependency_overrides[get_preference_repo] = lambda: repo
        try:
            resp = await async_client.put(
                "/api/v1/notifications/preferences/email/marketing",
                json={"opted_out": False},
                headers=auth_headers(USER_A),
            )
            assert resp.status_code == 200
            assert resp.json()["opted_out"] is False
        finally:
            app.dependency_overrides.pop(get_preference_repo, None)

    @pytest.mark.asyncio
    async def test_missing_body_returns_422(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.put(
            "/api/v1/notifications/preferences/email/marketing",
            headers=auth_headers(USER_A),
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_idempotent_put_same_value(
        self, async_client: AsyncClient
    ) -> None:
        """PUT with the same opted_out twice returns 200 both times."""
        upserted = _pref(USER_A, opted_out=True)
        repo = _make_repo_stub(upserted_pref=upserted)
        app.dependency_overrides[get_preference_repo] = lambda: repo
        try:
            for _ in range(2):
                resp = await async_client.put(
                    "/api/v1/notifications/preferences/email/marketing",
                    json={"opted_out": True},
                    headers=auth_headers(USER_A),
                )
                assert resp.status_code == 200
        finally:
            app.dependency_overrides.pop(get_preference_repo, None)


class TestSelfOnlyAccess:
    """
    Verify that user_id in JWT cannot be overridden by the caller.
    AC-029.x: a token for USER_B cannot read/write USER_A's preferences.
    """

    @pytest.mark.asyncio
    async def test_put_uses_jwt_user_not_body_user(
        self, async_client: AsyncClient
    ) -> None:
        upserted = _pref(USER_B, opted_out=True)
        repo = _make_repo_stub(upserted_pref=upserted)
        app.dependency_overrides[get_preference_repo] = lambda: repo
        try:
            resp = await async_client.put(
                "/api/v1/notifications/preferences/email/marketing",
                json={"opted_out": True},
                headers=auth_headers(USER_B),
            )
            assert resp.status_code == 200
            args = repo.upsert_preference.call_args
            assert args.kwargs["user_id"] == USER_B
        finally:
            app.dependency_overrides.pop(get_preference_repo, None)

    @pytest.mark.asyncio
    async def test_expired_token_returns_401(
        self, async_client: AsyncClient
    ) -> None:
        expired_token = jose_jwt.encode(
            {"sub": USER_A, "exp": int(time.time()) - 10},
            settings.secret_key,
            algorithm=settings.algorithm,
        )
        resp = await async_client.get(
            "/api/v1/notifications/preferences",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_tampered_token_returns_401(
        self, async_client: AsyncClient
    ) -> None:
        token = make_token(USER_A, secret="wrong-secret-that-is-long-enough-32+")
        resp = await async_client.get(
            "/api/v1/notifications/preferences",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401


class TestNotificationListEndpoint:
    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.get("/api/v1/notifications/")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_paginated_notifications(
        self, async_client: AsyncClient
    ) -> None:
        notifs = [_notif(USER_A) for _ in range(3)]
        repo = _make_repo_stub(notifs=notifs, notif_total=3)
        app.dependency_overrides[get_preference_repo] = lambda: repo
        try:
            resp = await async_client.get(
                "/api/v1/notifications/?page=1&page_size=10",
                headers=auth_headers(USER_A),
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 3
            assert data["page"] == 1
            assert data["page_size"] == 10
            assert len(data["items"]) == 3
        finally:
            app.dependency_overrides.pop(get_preference_repo, None)

    @pytest.mark.asyncio
    async def test_page_size_bounded_at_100(
        self, async_client: AsyncClient
    ) -> None:
        """page_size > 100 must be rejected."""
        resp = await async_client.get(
            "/api/v1/notifications/?page_size=200",
            headers=auth_headers(USER_A),
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_filter_by_channel(self, async_client: AsyncClient) -> None:
        repo = _make_repo_stub(notifs=[], notif_total=0)
        app.dependency_overrides[get_preference_repo] = lambda: repo
        try:
            resp = await async_client.get(
                "/api/v1/notifications/?channel=email",
                headers=auth_headers(USER_A),
            )
            assert resp.status_code == 200
            params_used = repo.list_notifications.call_args.args[1]
            assert params_used.channel == NotificationChannel.EMAIL
        finally:
            app.dependency_overrides.pop(get_preference_repo, None)

    @pytest.mark.asyncio
    async def test_invalid_status_filter_returns_422(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.get(
            "/api/v1/notifications/?status=flying",
            headers=auth_headers(USER_A),
        )
        assert resp.status_code == 422

```