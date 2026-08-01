# Implementation Report

Also fix event_bus.py (remove unused `Any`):

## Verification
- `python3 -c "
import os, json
result = []
for root, dirs, files in os.walk('backend'):
    dirs[:] = [d for d in dirs if d not in ('__pycache__','.mypy_cache','.ruff_cache','node_modules','.venv','venv')]
    for f in sorted(files):
        result.append(os.path.join(root, f))
print('\n'.join(sorted(result)[:200]))
"` → exit 0
- `python3 -c "
import os
result = []
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('__pycache__','.mypy_cache','.ruff_cache','node_modules','.venv','venv','.git')]
    for f in sorted(files):
        result.append(os.path.join(root, f))
print('\n'.join(sorted(result)[:250]))
"` → exit 0
- `pip install -q "fastapi>=0.111.0" "pydantic>=2.7.0" "pydantic-settings>=2.3.0" "sqlalchemy[asyncio]>=2.0.30" "opensearch-py>=2.6.0" "structlog>=24.1.0" "aiosqlite>=0.20.0" "pytest>=8.2.0" "pytest-asyncio>=0.23.7" "anyio>=4.4.0" "ruff>=0.4.7" "mypy>=1.10.0" "types-passlib>=1.7.7"` → exit 0
- `ruff check app/ tests/ --select E,F,I,UP,B --ignore E501` → exit 1
- `ruff check app/ tests/ --select E,F,I,UP,B --ignore E501 --fix` → exit 0
- `ruff check app/ tests/ --select E,F,I,UP,B --ignore E501` → exit 1
- `ruff check app/ tests/ --select E,F,I,UP,B --ignore E501 --fix` → exit 0
- `ruff check app/ tests/ --select E,F,I,UP,B --ignore E501` → exit 1
- `ruff check app/ tests/ --select E,F,I,UP,B --ignore E501 --fix` → exit 1

## Generated Files

### `backend/.env.example`
```text
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/appdb
OPENSEARCH_URL=http://localhost:9200
OPENSEARCH_INDEX_PREFIX=content
OPENSEARCH_USERNAME=
OPENSEARCH_PASSWORD=
SECRET_KEY=change-me-in-production
ENVIRONMENT=development
LOG_LEVEL=INFO

```

### `backend/alembic.ini`
```text
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql+asyncpg://user:password@localhost:5432/appdb

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
qualname = alembic.runtime.migration

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
"""Alembic environment configuration for async SQLAlchemy."""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import get_settings
from app.core.database import Base

# Import all models so Alembic can see their metadata.
import app.models.content  # noqa: F401

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Override sqlalchemy.url from app settings so .env is authoritative.
cfg = get_settings()
config.set_main_option("sqlalchemy.url", cfg.database_url)


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

### `backend/alembic/versions/0001_initial.py`
```python
"""create content_items and processed_events tables

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_items",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("body", sa.Text, nullable=True),
        sa.Column("author_id", sa.String(36), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "pending_review",
                "approved",
                "hidden",
                "deleted",
                name="contentstatus",
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_content_items_entity_type", "content_items", ["entity_type"])
    op.create_index("ix_content_items_author_id", "content_items", ["author_id"])

    op.create_table(
        "processed_events",
        sa.Column("id", sa.String(36), primary_key=True, nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_unique_constraint(
        "uq_processed_event_key",
        "processed_events",
        ["entity_type", "entity_id", "version"],
    )


def downgrade() -> None:
    op.drop_table("processed_events")
    op.drop_index("ix_content_items_author_id", table_name="content_items")
    op.drop_index("ix_content_items_entity_type", table_name="content_items")
    op.drop_table("content_items")
    op.execute("DROP TYPE IF EXISTS contentstatus")

```

### `backend/app/__init__.py`
```python

```

### `backend/app/core/__init__.py`
```python

```

### `backend/app/core/config.py`
```python
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ────────────────────────────────────────────────────────────────────
    environment: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # ── Database ───────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/appdb"
    )

    # ── OpenSearch ─────────────────────────────────────────────────────────────
    opensearch_url: str = Field(default="http://localhost:9200")
    opensearch_index_prefix: str = Field(default="content")
    opensearch_username: str = Field(default="")
    opensearch_password: SecretStr = Field(default=SecretStr(""))

    # ── Security ───────────────────────────────────────────────────────────────
    secret_key: SecretStr = Field(default=SecretStr("change-me-in-production"))

    @field_validator("secret_key", mode="after")
    @classmethod
    def _secret_key_not_default_in_prod(cls, v: SecretStr, info: object) -> SecretStr:
        # Validate at startup; actual enforcement happens in lifespan.
        return v

    @property
    def opensearch_index_content(self) -> str:
        return f"{self.opensearch_index_prefix}_items"

    @property
    def opensearch_index_processed_events(self) -> str:
        return f"{self.opensearch_index_prefix}_processed_events"


@lru_cache
def get_settings() -> Settings:
    return Settings()

```

### `backend/app/core/database.py`
```python
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

_settings = get_settings()

engine = create_async_engine(
    _settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db_session() -> AsyncSession:  # type: ignore[return]
    """FastAPI dependency for a scoped async DB session."""
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

import structlog


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog for JSON structured output."""
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level, logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.ExceptionRenderer(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level, logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    return structlog.get_logger(name)

```

### `backend/app/domain/__init__.py`
```python

```

### `backend/app/domain/content_status.py`
```python
from __future__ import annotations

from enum import StrEnum


class ContentStatus(StrEnum):
    """Lifecycle statuses for a content item (AC-027.5)."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    HIDDEN = "hidden"
    DELETED = "deleted"


# Statuses that are allowed to appear in the public search index (AC-027.5).
INDEXABLE_STATUSES: frozenset[ContentStatus] = frozenset({ContentStatus.APPROVED})

# Legal status transitions.  Any edge not in this map is forbidden.
ALLOWED_TRANSITIONS: dict[ContentStatus, frozenset[ContentStatus]] = {
    ContentStatus.DRAFT: frozenset(
        {ContentStatus.PENDING_REVIEW, ContentStatus.DELETED}
    ),
    ContentStatus.PENDING_REVIEW: frozenset(
        {ContentStatus.APPROVED, ContentStatus.HIDDEN, ContentStatus.DELETED}
    ),
    ContentStatus.APPROVED: frozenset({ContentStatus.HIDDEN, ContentStatus.DELETED}),
    ContentStatus.HIDDEN: frozenset({ContentStatus.APPROVED, ContentStatus.DELETED}),
    ContentStatus.DELETED: frozenset(),  # terminal
}


def is_valid_transition(from_status: ContentStatus, to_status: ContentStatus) -> bool:
    return to_status in ALLOWED_TRANSITIONS.get(from_status, frozenset())

```

### `backend/app/domain/events.py`
```python
from __future__ import annotations

from enum import StrEnum


class ContentEventType(StrEnum):
    """Domain event types emitted on content lifecycle changes (IF-017)."""

    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    APPROVED = "approved"
    HIDDEN = "hidden"

```

### `backend/app/main.py`
```python
from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.event_bus import get_event_bus
from app.services.search.indexer import create_indexer
from app.services.search.subscriber import register_search_subscriber

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    cfg = get_settings()
    configure_logging(cfg.log_level)

    if cfg.environment == "production" and (
        cfg.secret_key.get_secret_value() == "change-me-in-production"
    ):
        raise RuntimeError("SECRET_KEY must be changed in production")

    # Bootstrap search indexer and wire subscriber.
    indexer = await create_indexer(cfg)
    bus = get_event_bus()
    register_search_subscriber(bus, indexer)

    logger.info("app.startup", environment=cfg.environment)
    yield

    # Graceful shutdown.
    await indexer._os.close()
    logger.info("app.shutdown")


def create_app() -> FastAPI:
    cfg = get_settings()
    app = FastAPI(
        title="Content API",
        version="1.0.0",
        docs_url="/api/docs" if cfg.environment != "production" else None,
        redoc_url="/api/redoc" if cfg.environment != "production" else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if cfg.environment == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ────────────────────────────────────────────────────────────────
    from app.routers import health  # noqa: PLC0415

    app.include_router(health.router, prefix="/api")

    return app


app = create_app()

```

### `backend/app/models/__init__.py`
```python

```

### `backend/app/models/content.py`
```python
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import sqlalchemy
from sqlalchemy import DateTime, Enum, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.domain.content_status import ContentStatus


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


class ContentItem(Base):
    """Canonical content item entity.

    Owned by PHASE-021 / TASK-033.  Re-declared here so migration and tests
    work in a self-contained manner when prior phases are not present.
    """

    __tablename__ = "content_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, name="contentstatus"),
        nullable=False,
        default=ContentStatus.DRAFT,
    )
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<ContentItem id={self.id!r} status={self.status!r} version={self.version}>"


class ProcessedEvent(Base):
    """Idempotency ledger for search indexing events.

    Keyed by (entity_type, entity_id, version) to guarantee exactly-once
    processing (TASK-049 idempotency requirement).
    """

    __tablename__ = "processed_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    version: Mapped[int] = mapped_column(nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "entity_type", "entity_id", "version", name="uq_processed_event_key"
        ),
    )

```

### `backend/app/routers/__init__.py`
```python

```

### `backend/app/routers/health.py`
```python
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


router = APIRouter(tags=["ops"])


@router.get("/health", response_model=HealthResponse, status_code=200)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok")

```

### `backend/app/schemas/__init__.py`
```python

```

### `backend/app/schemas/content_event.py`
```python
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.content_status import ContentStatus
from app.domain.events import ContentEventType


class ContentEventPayload(BaseModel):
    """Wire schema for IF-017 content lifecycle events.

    Published by the content service and consumed by the search indexer.
    Fields are intentionally a superset of what any single event needs;
    optional fields default to None when absent.
    """

    event_id: str = Field(description="Unique event identifier (UUID4).")
    event_type: ContentEventType
    entity_type: str = Field(description="E.g. 'article', 'comment', 'product'.")
    entity_id: str = Field(description="UUID of the content item.")
    version: int = Field(ge=1, description="Monotonically increasing version.")
    status: ContentStatus
    occurred_at: datetime

    # Payload fields — present on create/update/approve; absent on delete/hide.
    title: str | None = None
    body: str | None = None
    author_id: str | None = None

    # Arbitrary extension bag for entity-type-specific attributes.
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"use_enum_values": True}

```

### `backend/app/services/__init__.py`
```python

```

### `backend/app/services/event_bus.py`
```python
"""In-process event bus — IF-017 subscriber registry.

This module provides a lightweight, in-process pub/sub bus used to decouple
the content service from the search indexer.  For production deployments the
same ``ContentEventPayload`` schema is used over SQS / SNS; this bus acts as
a testable stand-in that can be swapped at the FastAPI lifespan boundary.
"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

import structlog

from app.schemas.content_event import ContentEventPayload

logger = structlog.get_logger(__name__)

# Type alias for an async handler receiving a ContentEventPayload.
EventHandler = Callable[[ContentEventPayload], Awaitable[None]]


class EventBus:
    """Simple async fan-out event bus keyed by event_type (or '*' for all)."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Register *handler* for *event_type*.  Use ``'*'`` to catch all."""
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(self, event: ContentEventPayload) -> None:
        """Fan-out *event* to all matching handlers.

        Errors in individual handlers are logged and do not prevent other
        handlers from running.
        """
        targets = (
            self._handlers.get(str(event.event_type), [])
            + self._handlers.get("*", [])
        )
        if not targets:
            logger.debug("event_bus.no_handlers", event_type=event.event_type)
            return

        results = await asyncio.gather(
            *[handler(event) for handler in targets],
            return_exceptions=True,
        )
        for i, result in enumerate(results):
            if isinstance(result, BaseException):
                logger.error(
                    "event_bus.handler_error",
                    handler=repr(targets[i]),
                    error=str(result),
                    exc_info=result,
                )

    def reset(self) -> None:
        """Clear all subscriptions (used in tests)."""
        self._handlers.clear()


# Module-level singleton used by the FastAPI app and service layer.
_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus


def reset_event_bus() -> None:
    """Replace the singleton with a fresh instance (test isolation)."""
    global _bus
    _bus = EventBus()

```

### `backend/app/services/search/__init__.py`
```python

```

### `backend/app/services/search/indexer.py`
```python
"""Search Indexer — TASK-049

Consumes IF-017 content lifecycle events and maintains the OpenSearch
content index with idempotent exactly-once semantics keyed on
(entity_type, entity_id, version).

AC-027.5: Only APPROVED items are written to the index; hidden,
unapproved (draft / pending_review), and deleted items are removed
from the index unconditionally.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from opensearchpy import AsyncOpenSearch, NotFoundError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.domain.content_status import INDEXABLE_STATUSES, ContentStatus
from app.domain.events import ContentEventType
from app.models.content import ProcessedEvent
from app.schemas.content_event import ContentEventPayload
from app.services.search.opensearch_client import build_opensearch_client, ensure_indices

logger = structlog.get_logger(__name__)


class SearchIndexer:
    """Event-driven search index maintainer.

    All public methods are idempotent by (entity_type, entity_id, version).
    The idempotency ledger is stored in the ``processed_events`` DB table so
    that retries after a partial failure never produce duplicate or stale
    index state.
    """

    def __init__(
        self,
        opensearch: AsyncOpenSearch,
        settings: Settings | None = None,
    ) -> None:
        self._os = opensearch
        self._cfg = settings or get_settings()

    # ── Public entry-point ────────────────────────────────────────────────────

    async def handle_event(
        self,
        event: ContentEventPayload,
        db: AsyncSession,
    ) -> bool:
        """Process a single content event.

        Returns ``True`` if the event was processed, ``False`` if it was
        a duplicate (already processed — idempotent skip).

        Raises on unrecoverable errors so the caller's retry / DLQ logic
        can decide what to do.
        """
        log = logger.bind(
            event_id=event.event_id,
            event_type=event.event_type,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            version=event.version,
        )

        # ── 1. Idempotency check ───────────────────────────────────────────────
        already_processed = await self._is_processed(
            db, event.entity_type, event.entity_id, event.version
        )
        if already_processed:
            log.info("search.indexer.duplicate_skipped")
            return False

        # ── 2. Route to correct index operation ───────────────────────────────
        event_type = ContentEventType(event.event_type)
        status = ContentStatus(event.status)

        if event_type == ContentEventType.DELETED:
            await self._delete_from_index(event.entity_type, event.entity_id, log)
        elif status not in INDEXABLE_STATUSES:
            # Hidden / unapproved — remove from index if present (AC-027.5)
            await self._delete_from_index(event.entity_type, event.entity_id, log)
        else:
            # APPROVED — upsert
            await self._upsert_into_index(event, log)

        # ── 3. Record idempotency token ───────────────────────────────────────
        await self._mark_processed(db, event)
        log.info("search.indexer.event_processed")
        return True

    # ── Index operations ──────────────────────────────────────────────────────

    async def _upsert_into_index(
        self,
        event: ContentEventPayload,
        log: Any,
    ) -> None:
        """Write (or overwrite) a document in the content index."""
        doc = self._build_document(event)
        doc_id = self._doc_id(event.entity_type, event.entity_id)
        index = self._cfg.opensearch_index_content

        log.debug("search.indexer.upserting", doc_id=doc_id, index=index)
        await self._os.index(
            index=index,
            id=doc_id,
            body=doc,
            refresh="wait_for",  # immediate visibility for tests
        )

    async def _delete_from_index(
        self,
        entity_type: str,
        entity_id: str,
        log: Any,
    ) -> None:
        """Remove a document from the content index; tolerates missing docs."""
        doc_id = self._doc_id(entity_type, entity_id)
        index = self._cfg.opensearch_index_content

        log.debug("search.indexer.deleting", doc_id=doc_id, index=index)
        try:
            await self._os.delete(index=index, id=doc_id, refresh="wait_for")
        except NotFoundError:
            log.debug("search.indexer.delete_noop_not_found", doc_id=doc_id)

    # ── Idempotency ledger (DB) ───────────────────────────────────────────────

    async def _is_processed(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: str,
        version: int,
    ) -> bool:
        stmt = select(ProcessedEvent).where(
            ProcessedEvent.entity_type == entity_type,
            ProcessedEvent.entity_id == entity_id,
            ProcessedEvent.version == version,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def _mark_processed(
        self,
        db: AsyncSession,
        event: ContentEventPayload,
    ) -> None:
        record = ProcessedEvent(
            id=str(uuid.uuid4()),
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            version=event.version,
            event_type=str(event.event_type),
            processed_at=datetime.now(tz=UTC),
        )
        db.add(record)
        # Caller commits; we only add to the session.

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _doc_id(entity_type: str, entity_id: str) -> str:
        return f"{entity_type}::{entity_id}"

    @staticmethod
    def _build_document(event: ContentEventPayload) -> dict[str, Any]:
        return {
            "entity_id": event.entity_id,
            "entity_type": event.entity_type,
            "title": event.title or "",
            "body": event.body or "",
            "author_id": event.author_id or "",
            "status": str(event.status),
            "version": event.version,
            "occurred_at": event.occurred_at.isoformat(),
            "metadata": event.metadata,
        }


# ── Bootstrap helper ─────────────────────────────────────────────────────────

async def create_indexer(settings: Settings | None = None) -> SearchIndexer:
    """Construct a ready-to-use SearchIndexer with index bootstrapping."""
    cfg = settings or get_settings()
    client = build_opensearch_client(cfg)
    await ensure_indices(client, cfg)
    return SearchIndexer(opensearch=client, settings=cfg)

```

### `backend/app/services/search/opensearch_client.py`
```python
from __future__ import annotations

from typing import Any

from opensearchpy import AsyncOpenSearch

from app.core.config import Settings, get_settings

# ── OpenSearch index mapping (STORE-007) ──────────────────────────────────────
#
# Only APPROVED items are indexed (AC-027.5).
# The mapping is declared here so it can be applied at bootstrap and referenced
# in tests.  Field choices:
#
#   - title / body: text with keyword sub-field for exact/sort queries.
#   - status: keyword (for filter queries, though only "approved" ever lands).
#   - author_id / entity_type: keyword (exact match / aggregation).
#   - version: integer (idempotency tracking in OpenSearch docs is secondary
#     to the DB ledger; kept for debugging).
#   - occurred_at: date (range queries / sorting).
#   - metadata: flat object (dynamic: false to avoid mapping explosion).

CONTENT_INDEX_MAPPING: dict[str, Any] = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "content_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"],
                }
            }
        },
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "entity_id": {"type": "keyword"},
            "entity_type": {"type": "keyword"},
            "title": {
                "type": "text",
                "analyzer": "content_analyzer",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 512}},
            },
            "body": {"type": "text", "analyzer": "content_analyzer"},
            "author_id": {"type": "keyword"},
            "status": {"type": "keyword"},
            "version": {"type": "integer"},
            "occurred_at": {"type": "date"},
            "metadata": {"type": "object", "dynamic": False},
        },
    },
}

# Idempotency ledger index — lightweight, no full-text needed.
PROCESSED_EVENTS_INDEX_MAPPING: dict[str, Any] = {
    "settings": {"number_of_shards": 1, "number_of_replicas": 1},
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "entity_type": {"type": "keyword"},
            "entity_id": {"type": "keyword"},
            "version": {"type": "integer"},
            "event_type": {"type": "keyword"},
            "processed_at": {"type": "date"},
        },
    },
}


def build_opensearch_client(settings: Settings | None = None) -> AsyncOpenSearch:
    """Construct an AsyncOpenSearch client from application settings."""
    cfg = settings or get_settings()
    kwargs: dict[str, Any] = {
        "hosts": [cfg.opensearch_url],
        "use_ssl": cfg.opensearch_url.startswith("https://"),
        "verify_certs": cfg.opensearch_url.startswith("https://"),
        "timeout": 10,
        "max_retries": 3,
        "retry_on_timeout": True,
    }
    username = cfg.opensearch_username
    password = cfg.opensearch_password.get_secret_value()
    if username and password:
        kwargs["http_auth"] = (username, password)

    return AsyncOpenSearch(**kwargs)


async def ensure_indices(client: AsyncOpenSearch, settings: Settings | None = None) -> None:
    """Create indices with mapping if they do not already exist."""
    cfg = settings or get_settings()
    pairs = [
        (cfg.opensearch_index_content, CONTENT_INDEX_MAPPING),
        (cfg.opensearch_index_processed_events, PROCESSED_EVENTS_INDEX_MAPPING),
    ]
    for index_name, mapping in pairs:
        exists = await client.indices.exists(index=index_name)
        if not exists:
            await client.indices.create(index=index_name, body=mapping)

```

### `backend/app/services/search/subscriber.py`
```python
"""Wire the SearchIndexer into the IF-017 EventBus.

Called once at application startup.  Each content event published on the
bus is forwarded to SearchIndexer.handle_event with a fresh DB session.
"""
from __future__ import annotations

import structlog

from app.core.database import AsyncSessionLocal
from app.schemas.content_event import ContentEventPayload
from app.services.event_bus import EventBus
from app.services.search.indexer import SearchIndexer

logger = structlog.get_logger(__name__)


def register_search_subscriber(bus: EventBus, indexer: SearchIndexer) -> None:
    """Subscribe the indexer to all content lifecycle events on *bus*."""

    async def _on_event(event: ContentEventPayload) -> None:
        async with AsyncSessionLocal() as db:
            try:
                processed = await indexer.handle_event(event, db)
                await db.commit()
                if processed:
                    logger.info(
                        "search.subscriber.processed",
                        event_id=event.event_id,
                        event_type=event.event_type,
                    )
            except Exception:
                await db.rollback()
                logger.exception(
                    "search.subscriber.error",
                    event_id=event.event_id,
                    entity_id=event.entity_id,
                )
                raise  # Re-raise so the bus can log / DLQ as needed.

    # Subscribe to every content event type.
    for event_type in ("created", "updated", "deleted", "approved", "hidden"):
        bus.subscribe(event_type, _on_event)

    logger.info("search.subscriber.registered")

```

### `backend/pyproject.toml`
```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.29.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.3.0",
    "sqlalchemy[asyncio]>=2.0.30",
    "alembic>=1.13.1",
    "asyncpg>=0.29.0",
    "httpx>=0.27.0",
    "opensearch-py>=2.6.0",
    "tenacity>=8.3.0",
    "structlog>=24.1.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
]

[project.optional-dependencies]
test = [
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.7",
    "pytest-cov>=5.0.0",
    "anyio>=4.4.0",
    "respx>=0.21.0",
    "factory-boy>=3.3.0",
]
lint = [
    "ruff>=0.4.7",
    "mypy>=1.10.0",
    "types-passlib>=1.7.7",
    "types-python-jose>=3.3.4",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["app*"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --tb=short"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "C4", "SIM"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true
plugins = ["pydantic.mypy"]

```

### `backend/tests/__init__.py`
```python

```

### `backend/tests/conftest.py`
```python
"""Pytest configuration and shared fixtures for TASK-049 tests.

Uses an in-memory SQLite (via aiosqlite) database so no real Postgres is
needed.  OpenSearch is replaced by a lightweight in-memory stub to keep
tests fully self-contained.
"""
from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.domain.content_status import ContentStatus
from app.domain.events import ContentEventType
from app.schemas.content_event import ContentEventPayload
from app.services.search.indexer import SearchIndexer


# ── In-memory SQLite engine ───────────────────────────────────────────────────


@pytest.fixture(scope="session")
def event_loop_policy() -> asyncio.DefaultEventLoopPolicy:
    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture
async def db_engine():  # type: ignore[return]
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:  # type: ignore[return]
    session_factory = async_sessionmaker(
        bind=db_engine, expire_on_commit=False, autoflush=False
    )
    async with session_factory() as session:
        yield session


# ── Fake OpenSearch ───────────────────────────────────────────────────────────


class FakeOpenSearch:
    """Minimal in-memory OpenSearch stub sufficient for indexer tests."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def _key(self, index: str, doc_id: str) -> str:
        return f"{index}::{doc_id}"

    async def index(
        self, *, index: str, id: str, body: dict[str, Any], **kwargs: Any
    ) -> None:
        self._store[self._key(index, id)] = body

    async def delete(self, *, index: str, id: str, **kwargs: Any) -> None:
        key = self._key(index, id)
        if key not in self._store:
            from opensearchpy import NotFoundError

            raise NotFoundError(404, "not_found", {})
        del self._store[key]

    async def get(
        self, *, index: str, id: str, **kwargs: Any
    ) -> dict[str, Any] | None:
        return self._store.get(self._key(index, id))

    def exists_in_index(self, index: str, doc_id: str) -> bool:
        return self._key(index, doc_id) in self._store

    def get_doc(self, index: str, doc_id: str) -> dict[str, Any] | None:
        return self._store.get(self._key(index, doc_id))

    async def close(self) -> None:
        pass


@pytest.fixture
def fake_os() -> FakeOpenSearch:
    return FakeOpenSearch()


@pytest.fixture
def indexer(fake_os: FakeOpenSearch) -> SearchIndexer:
    from app.core.config import Settings

    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        opensearch_url="http://localhost:9200",
        opensearch_index_prefix="test",
        environment="test",
    )
    return SearchIndexer(opensearch=fake_os, settings=settings)  # type: ignore[arg-type]


# ── Event factory ─────────────────────────────────────────────────────────────


def make_event(
    *,
    event_type: ContentEventType = ContentEventType.CREATED,
    status: ContentStatus = ContentStatus.APPROVED,
    entity_type: str = "article",
    entity_id: str | None = None,
    version: int = 1,
    title: str = "Test Article",
    body: str = "Body text",
    author_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ContentEventPayload:
    return ContentEventPayload(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id or str(uuid.uuid4()),
        version=version,
        status=status,
        occurred_at=datetime.now(tz=UTC),
        title=title,
        body=body,
        author_id=author_id or str(uuid.uuid4()),
        metadata=metadata or {},
    )

```

### `backend/tests/test_search_indexer.py`
```python
"""Integration tests for TASK-049: Search Indexing Pipeline.

Covers:
  - create / update events for APPROVED content → upserted into index
  - hide event → removed from index (AC-027.5)
  - approve event → re-added to index
  - delete event → removed from index
  - draft / pending_review events → excluded from index (AC-027.5)
  - idempotent consumption: same (entity_type, entity_id, version) skipped
  - different versions of same entity → both processed independently
  - idempotency key is scoped per entity_type
  - EventBus integration: events published on bus reach indexer
"""
from __future__ import annotations

import asyncio
import uuid

import pytest

from app.domain.content_status import ContentStatus
from app.domain.events import ContentEventType
from tests.conftest import FakeOpenSearch, make_event  # noqa: F401 (FakeOpenSearch used in type hints)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _doc_id(entity_type: str, entity_id: str) -> str:
    return f"{entity_type}::{entity_id}"


# ─────────────────────────────────────────────────────────────────────────────
# APPROVED content is indexed
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_approved_indexes_document(indexer, fake_os, db_session):
    """CREATED + APPROVED → document appears in the content index."""
    event = make_event(event_type=ContentEventType.CREATED, status=ContentStatus.APPROVED)

    processed = await indexer.handle_event(event, db_session)

    assert processed is True
    doc = fake_os.get_doc("test_items", _doc_id(event.entity_type, event.entity_id))
    assert doc is not None
    assert doc["entity_id"] == event.entity_id
    assert doc["title"] == event.title
    assert doc["status"] == "approved"


@pytest.mark.asyncio
async def test_update_approved_overwrites_document(indexer, fake_os, db_session):
    """UPDATED + APPROVED → document is overwritten with new content."""
    entity_id = str(uuid.uuid4())
    v1 = make_event(
        event_type=ContentEventType.CREATED,
        status=ContentStatus.APPROVED,
        entity_id=entity_id,
        version=1,
        title="Original",
    )
    v2 = make_event(
        event_type=ContentEventType.UPDATED,
        status=ContentStatus.APPROVED,
        entity_id=entity_id,
        version=2,
        title="Updated",
    )

    await indexer.handle_event(v1, db_session)
    await indexer.handle_event(v2, db_session)

    doc = fake_os.get_doc("test_items", _doc_id(v2.entity_type, entity_id))
    assert doc is not None
    assert doc["title"] == "Updated"
    assert doc["version"] == 2


# ─────────────────────────────────────────────────────────────────────────────
# AC-027.5 — hidden / unapproved excluded from index
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_hide_event_removes_from_index(indexer, fake_os, db_session):
    """AC-027.5: HIDDEN event removes an already-indexed document."""
    entity_id = str(uuid.uuid4())

    approved_event = make_event(
        event_type=ContentEventType.APPROVED,
        status=ContentStatus.APPROVED,
        entity_id=entity_id,
        version=1,
    )
    await indexer.handle_event(approved_event, db_session)
    assert fake_os.exists_in_index("test_items", _doc_id("article", entity_id))

    hidden_event = make_event(
        event_type=ContentEventType.HIDDEN,
        status=ContentStatus.HIDDEN,
        entity_id=entity_id,
        version=2,
    )
    processed = await indexer.handle_event(hidden_event, db_session)

    assert processed is True
    assert not fake_os.exists_in_index("test_items", _doc_id("article", entity_id))


@pytest.mark.asyncio
async def test_draft_content_not_indexed(indexer, fake_os, db_session):
    """AC-027.5: CREATED with DRAFT status must not appear in index."""
    event = make_event(event_type=ContentEventType.CREATED, status=ContentStatus.DRAFT)

    processed = await indexer.handle_event(event, db_session)

    assert processed is True
    assert not fake_os.exists_in_index(
        "test_items", _doc_id(event.entity_type, event.entity_id)
    )


@pytest.mark.asyncio
async def test_pending_review_content_not_indexed(indexer, fake_os, db_session):
    """AC-027.5: CREATED with PENDING_REVIEW status must not appear in index."""
    event = make_event(
        event_type=ContentEventType.CREATED, status=ContentStatus.PENDING_REVIEW
    )

    await indexer.handle_event(event, db_session)

    assert not fake_os.exists_in_index(
        "test_items", _doc_id(event.entity_type, event.entity_id)
    )


@pytest.mark.asyncio
async def test_approve_event_adds_to_index(indexer, fake_os, db_session):
    """APPROVED event re-adds a previously hidden item to the index."""
    entity_id = str(uuid.uuid4())

    hidden_event = make_event(
        event_type=ContentEventType.HIDDEN,
        status=ContentStatus.HIDDEN,
        entity_id=entity_id,
        version=1,
    )
    await indexer.handle_event(hidden_event, db_session)
    assert not fake_os.exists_in_index("test_items", _doc_id("article", entity_id))

    approve_event = make_event(
        event_type=ContentEventType.APPROVED,
        status=ContentStatus.APPROVED,
        entity_id=entity_id,
        version=2,
        title="Approved Content",
    )
    processed = await indexer.handle_event(approve_event, db_session)

    assert processed is True
    doc = fake_os.get_doc("test_items", _doc_id("article", entity_id))
    assert doc is not None
    assert doc["status"] == "approved"
    assert doc["title"] == "Approved Content"


# ─────────────────────────────────────────────────────────────────────────────
# Delete event
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_event_removes_from_index(indexer, fake_os, db_session):
    """DELETE event removes document regardless of current status."""
    entity_id = str(uuid.uuid4())

    await indexer.handle_event(
        make_event(
            event_type=ContentEventType.APPROVED,
            status=ContentStatus.APPROVED,
            entity_id=entity_id,
            version=1,
        ),
        db_session,
    )

    delete_event = make_event(
        event_type=ContentEventType.DELETED,
        status=ContentStatus.DELETED,
        entity_id=entity_id,
        version=2,
    )
    processed = await indexer.handle_event(delete_event, db_session)

    assert processed is True
    assert not fake_os.exists_in_index("test_items", _doc_id("article", entity_id))


@pytest.mark.asyncio
async def test_delete_event_on_nonexistent_doc_is_idempotent(indexer, fake_os, db_session):
    """DELETE on a doc not in index must not raise (NotFoundError tolerated)."""
    event = make_event(
        event_type=ContentEventType.DELETED,
        status=ContentStatus.DELETED,
    )
    processed = await indexer.handle_event(event, db_session)
    assert processed is True


# ─────────────────────────────────────────────────────────────────────────────
# Idempotency
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_duplicate_event_is_skipped(indexer, fake_os, db_session):
    """Same (entity_type, entity_id, version) processed twice → second is no-op."""
    event = make_event(event_type=ContentEventType.CREATED, status=ContentStatus.APPROVED)

    first = await indexer.handle_event(event, db_session)
    await db_session.commit()

    second = await indexer.handle_event(event, db_session)

    assert first is True
    assert second is False  # duplicate skipped


@pytest.mark.asyncio
async def test_different_versions_are_both_processed(indexer, fake_os, db_session):
    """Different versions of the same entity are each processed once."""
    entity_id = str(uuid.uuid4())

    e1 = make_event(
        event_type=ContentEventType.CREATED,
        status=ContentStatus.APPROVED,
        entity_id=entity_id,
        version=1,
        title="V1",
    )
    e2 = make_event(
        event_type=ContentEventType.UPDATED,
        status=ContentStatus.APPROVED,
        entity_id=entity_id,
        version=2,
        title="V2",
    )

    r1 = await indexer.handle_event(e1, db_session)
    await db_session.commit()
    r2 = await indexer.handle_event(e2, db_session)

    assert r1 is True
    assert r2 is True


@pytest.mark.asyncio
async def test_idempotency_key_is_per_entity_type(indexer, fake_os, db_session):
    """Same entity_id + version but different entity_type are independent."""
    entity_id = str(uuid.uuid4())

    e_article = make_event(
        event_type=ContentEventType.CREATED,
        status=ContentStatus.APPROVED,
        entity_type="article",
        entity_id=entity_id,
        version=1,
    )
    e_comment = make_event(
        event_type=ContentEventType.CREATED,
        status=ContentStatus.APPROVED,
        entity_type="comment",
        entity_id=entity_id,
        version=1,
    )

    r1 = await indexer.handle_event(e_article, db_session)
    await db_session.commit()
    r2 = await indexer.handle_event(e_comment, db_session)

    assert r1 is True
    assert r2 is True


# ─────────────────────────────────────────────────────────────────────────────
# EventBus integration
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_event_bus_delivers_to_subscriber(fake_os, db_engine):
    """Events published on the bus reach the search indexer subscriber."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    import app.services.search.subscriber as sub_module
    from app.core.config import Settings
    from app.services.event_bus import EventBus
    from app.services.search.indexer import SearchIndexer
    from app.services.search.subscriber import register_search_subscriber

    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        opensearch_url="http://localhost:9200",
        opensearch_index_prefix="test",
        environment="test",
    )
    _indexer = SearchIndexer(opensearch=fake_os, settings=settings)  # type: ignore[arg-type]

    bus = EventBus()
    session_factory = async_sessionmaker(
        bind=db_engine, expire_on_commit=False, autoflush=False
    )

    original_session = sub_module.AsyncSessionLocal
    sub_module.AsyncSessionLocal = session_factory  # type: ignore[assignment]
    try:
        register_search_subscriber(bus, _indexer)

        event = make_event(
            event_type=ContentEventType.CREATED, status=ContentStatus.APPROVED
        )
        await bus.publish(event)
        await asyncio.sleep(0)

        doc = fake_os.get_doc("test_items", _doc_id(event.entity_type, event.entity_id))
        assert doc is not None
        assert doc["entity_id"] == event.entity_id
    finally:
        sub_module.AsyncSessionLocal = original_session  # type: ignore[assignment]

```