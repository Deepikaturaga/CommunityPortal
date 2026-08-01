# Implementation Report

The patch mangled the file. Rewrite it cleanly:

## Verification
- `python3 -c "import os; files=[os.path.join(r,f) for r,ds,fs in os.walk('.') for f in fs if '__pycache__' not in r]; print('\n'.join(sorted(files)[:120]))"` → exit 0
- `python3 -c "import os; print(os.getcwd()); print(os.listdir('.'))"` → exit 0
- `pip install -q "fastapi==0.111.1" "uvicorn[standard]==0.30.1" "pydantic==2.7.4" "pydantic-settings==2.3.4" "sqlalchemy==2.0.31" "alembic==1.13.2" "aiosqlite==0.20.0" "greenlet==3.0.3" "python-jose[cryptography]==3.3.0" "passlib[bcrypt]==1.7.4" "httpx==0.27.0" "structlog==24.2.0" "pytest==8.2.2" "pytest-asyncio==0.23.7" "anyio==4.4.0" "ruff==0.5.0" "mypy==1.10.1" "types-python-jose==3.3.4.20240106" "types-passlib==1.7.7.20240327"` → exit 0
- `pip show fastapi pydantic pydantic-settings sqlalchemy alembic httpx uvicorn` → exit 0
- `ruff check app/ tests/ --select E,F,I,UP,B,SIM` → exit 1
- `ruff check app/ tests/ --select E,F,I,UP,B,SIM` → exit 1
- `ruff check app/ tests/ --select E,F,I,UP,B,SIM` → exit 0
- `mypy app/ --ignore-missing-imports --no-error-summary` → exit 1
- `mypy app/ --ignore-missing-imports --no-error-summary` → exit 1
- `mypy app/ --ignore-missing-imports --no-error-summary` → exit 2
- `mypy app/ --ignore-missing-imports --no-error-summary` → exit 0

## Generated Files

### `backend/.env.example`
```text
# Example environment — copy to .env and fill real values
DATABASE_URL=postgresql+asyncpg://posts:posts@localhost:5432/posts
SECRET_KEY=change-me-min-32-chars-xxxxxxxxxxxxxxxx
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EVENT_BACKEND=memory
# For real SNS/SQS integration:
# EVENT_BACKEND=sns
# AWS_SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:post-events
# AWS_REGION=us-east-1

```

### `backend/alembic.ini`
```text
[alembic]
script_location = alembic
file_template = %%(year)d%%(month).2d%%(day).2d_%%(rev)s_%%(slug)s
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = sqlite+aiosqlite:///./dev.db

```

### `backend/alembic/env.py`
```python
"""Alembic env — async SQLAlchemy support."""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import all models so metadata is populated
from app.core.database import Base
from app.services.posts import models as _post_models  # noqa: F401
from app.services.posts import comment_model as _comment_models  # noqa: F401

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
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

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}

```

### `backend/alembic/versions/0001_initial_posts_comments.py`
```python
"""Initial schema: posts + comments tables.

Revision ID: 0001
Revises: None
Create Date: 2024-07-01 00:00:00
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "posts",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("author_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_posts_author_id", "posts", ["author_id"])

    op.create_table(
        "comments",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("post_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("author_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["post_id"],
            ["posts.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_comments_post_id", "comments", ["post_id"])
    op.create_index("ix_comments_author_id", "comments", ["author_id"])


def downgrade() -> None:
    op.drop_index("ix_comments_author_id", table_name="comments")
    op.drop_index("ix_comments_post_id", table_name="comments")
    op.drop_table("comments")
    op.drop_index("ix_posts_author_id", table_name="posts")
    op.drop_table("posts")

```

### `backend/app/__init__.py`
```python

```

### `backend/app/core/__init__.py`
```python

```

### `backend/app/core/auth.py`
```python
"""JWT authentication helpers."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import Settings, get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class TokenPayload(BaseModel):
    sub: str  # user UUID as string
    exp: datetime


def create_access_token(
    subject: UUID | str,
    settings: Settings,
    expires_delta: timedelta | None = None,
) -> str:
    delta = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    expire = datetime.now(UTC) + delta
    data: dict[str, Any] = {"sub": str(subject), "exp": expire}
    return jwt.encode(
        data,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )


async def get_current_user_id(
    token: str = Depends(oauth2_scheme),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> UUID:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
        )
        raw_sub: str | None = payload.get("sub")
        if raw_sub is None:
            raise credentials_exc
        return UUID(raw_sub)
    except (JWTError, ValueError) as exc:
        raise credentials_exc from exc

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
    )

    # ── Database ────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="sqlite+aiosqlite:///./test.db",
        description="Async SQLAlchemy DSN",
    )

    # ── Auth ────────────────────────────────────────────────────────────────
    secret_key: SecretStr = Field(
        default=...,
        min_length=32,
        description="JWT signing secret — never log this",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # ── Event backend ───────────────────────────────────────────────────────
    event_backend: Literal["memory", "sns"] = "memory"
    aws_sns_topic_arn: str | None = None
    aws_region: str = "us-east-1"

    @field_validator("aws_sns_topic_arn")
    @classmethod
    def _require_arn_when_sns(cls, v: str | None, info: object) -> str | None:
        # Pydantic v2: info.data carries already-validated siblings
        data = getattr(info, "data", {})
        if data.get("event_backend") == "sns" and not v:
            raise ValueError("aws_sns_topic_arn is required when event_backend=sns")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # pydantic-settings resolves env vars; secret_key required at runtime
    return Settings.model_validate({})

```

### `backend/app/core/database.py`
```python
"""Async SQLAlchemy engine + session factory."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _build_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
    )


# Module-level singletons — replaced in tests via dependency override
_engine: AsyncEngine = _build_engine()
_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with _session_factory() as session:
        yield session

```

### `backend/app/core/exceptions.py`
```python
"""Global exception handlers — no internal detail leakage."""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


def _error(code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=code, content={"detail": message})


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(404)
    async def not_found(_req: Request, _exc: Exception) -> JSONResponse:
        return _error(status.HTTP_404_NOT_FOUND, "Resource not found")

    @app.exception_handler(405)
    async def method_not_allowed(_req: Request, _exc: Exception) -> JSONResponse:
        return _error(status.HTTP_405_METHOD_NOT_ALLOWED, "Method not allowed")

    @app.exception_handler(500)
    async def internal(_req: Request, exc: Exception) -> JSONResponse:
        # Log without leaking exc.args to the response
        return _error(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error")

```

### `backend/app/core/logging.py`
```python
"""Structured logging configuration (structlog)."""
from __future__ import annotations

import logging
from typing import Any

import structlog


def configure_logging(level: str = "INFO") -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )


def get_logger(name: str) -> Any:  # structlog BoundLogger is not precisely typed
    return structlog.get_logger(name)

```

### `backend/app/events/__init__.py`
```python

```

### `backend/app/events/publisher.py`
```python
"""
Event publisher abstraction.

Backend is selected at startup from Settings.event_backend:
  - "memory"  -> in-process list (tests / local dev)
  - "sns"     -> AWS SNS (production)

The adapter is injected via FastAPI dependency so tests can override it.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

log = get_logger(__name__)


class EventPublisher(ABC):
    """Interface -- emit a structured event payload."""

    @abstractmethod
    async def publish(self, event_type: str, payload: dict[str, Any]) -> None: ...


# -- In-process backend (memory / test) -----------------------------------------


class MemoryEventPublisher(EventPublisher):
    """Stores published events in memory -- useful for unit tests and local dev."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        entry = {"event_type": event_type, **payload}
        self.events.append(entry)
        log.info("event.published", event_type=event_type, payload=payload)


# -- AWS SNS backend ------------------------------------------------------------


class SnsEventPublisher(EventPublisher):
    """
    Publishes events to AWS SNS.

    Lazy import of boto3 so the service starts without AWS SDKs in local dev
    when event_backend=memory.
    """

    def __init__(self, topic_arn: str, region: str) -> None:
        self._topic_arn = topic_arn
        self._region = region

    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        import boto3  # lazy — only needed in production path

        client = boto3.client("sns", region_name=self._region)
        message = json.dumps({"event_type": event_type, **payload}, default=str)
        client.publish(
            TopicArn=self._topic_arn,
            Message=message,
            MessageAttributes={
                "event_type": {
                    "DataType": "String",
                    "StringValue": event_type,
                }
            },
        )
        log.info("event.sns.published", event_type=event_type, topic_arn=self._topic_arn)


# -- DI factory -----------------------------------------------------------------

_publisher_cache: EventPublisher | None = None


def get_event_publisher(
    settings: Settings | None = None,
) -> EventPublisher:
    """
    FastAPI dependency -- returns a singleton publisher keyed to Settings.event_backend.
    Override in tests with app.dependency_overrides.
    """
    global _publisher_cache
    if _publisher_cache is None:
        cfg = settings or get_settings()
        if cfg.event_backend == "sns":
            _publisher_cache = SnsEventPublisher(
                topic_arn=cfg.aws_sns_topic_arn or "",
                region=cfg.aws_region,
            )
        else:
            _publisher_cache = MemoryEventPublisher()
    return _publisher_cache


def reset_publisher_cache() -> None:
    """Test helper -- clear singleton so tests start clean."""
    global _publisher_cache
    _publisher_cache = None

```

### `backend/app/main.py`
```python
"""ASGI entrypoint — single canonical FastAPI application."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.services.posts.comments_router import router as comments_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    configure_logging()
    # Validate settings eagerly at startup (pydantic-settings raises on bad config)
    _ = settings
    yield
    # Shutdown: SQLAlchemy engine disposal handled per-request via DI


def create_app() -> FastAPI:
    app = FastAPI(
        title="Posts Service",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    register_exception_handlers(app)

    # ── Routers ──────────────────────────────────────────────────────────────
    app.include_router(comments_router, prefix="/v1")

    # ── Health ───────────────────────────────────────────────────────────────
    @app.get("/health", tags=["ops"], include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

```

### `backend/app/services/__init__.py`
```python

```

### `backend/app/services/posts/__init__.py`
```python

```

### `backend/app/services/posts/comment_model.py`
```python
"""SQLAlchemy ORM model: Comment."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.services.posts.models import Post


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    post: Mapped[Post] = relationship("Post", back_populates="comments")

```

### `backend/app/services/posts/comments_router.py`
```python
"""
Router: POST /posts/{post_id}/comments

Requires Bearer JWT auth (deny-by-default).
B008 (Depends in default) is intentional FastAPI pattern — suppressed per ruff config.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.core.database import get_session
from app.events.publisher import EventPublisher, get_event_publisher
from app.services.posts.comments_schema import CommentCreate, CommentResponse
from app.services.posts.comments_service import CommentService

router = APIRouter(prefix="/posts", tags=["comments"])


def _get_comment_service(
    session: AsyncSession = Depends(get_session),  # noqa: B008
    publisher: EventPublisher = Depends(get_event_publisher),  # noqa: B008
) -> CommentService:
    return CommentService(session=session, publisher=publisher)


@router.post(
    "/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a comment on a post",
    description=(
        "Persists the comment and emits a `comment.created` event (IF-017) "
        "for downstream notification consumers."
    ),
)
async def create_comment(
    post_id: UUID,
    body: CommentCreate,
    current_user_id: UUID = Depends(get_current_user_id),  # noqa: B008
    service: CommentService = Depends(_get_comment_service),  # noqa: B008
) -> CommentResponse:
    return await service.create_comment(
        post_id=post_id,
        author_id=current_user_id,
        payload=body,
    )

```

### `backend/app/services/posts/comments_schema.py`
```python
"""Pydantic request/response schemas for comments (IF-017 contract)."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CommentCreate(BaseModel):
    """Request body for POST /posts/{post_id}/comments."""

    body: str = Field(..., min_length=1, max_length=10_000, description="Comment text")

    @field_validator("body")
    @classmethod
    def strip_body(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("body must not be blank")
        return stripped


class CommentResponse(BaseModel):
    """Response envelope for a single comment."""

    id: UUID
    post_id: UUID
    author_id: UUID
    body: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── IF-017 event payload ──────────────────────────────────────────────────────

class CommentCreatedEvent(BaseModel):
    """
    IF-017 — event published when a comment is persisted.

    Consumers (notification service, etc.) subscribe to this shape.
    Fields are intentionally stable; add new optional fields, never remove.
    """

    event_type: str = "comment.created"
    comment_id: UUID
    post_id: UUID
    author_id: UUID  # commenter
    post_author_id: UUID  # recipient for notification
    body_preview: str = Field(
        ...,
        description="First 200 chars of the comment body — safe for notification text",
    )
    occurred_at: datetime

```

### `backend/app/services/posts/comments_service.py`
```python
"""
Comment service — business logic for TASK-042.

Responsibilities:
1. Verify the target Post exists (raises 404 otherwise).
2. Persist the Comment in a single explicit transaction.
3. Emit IF-017 CommentCreatedEvent after successful persistence.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.events.publisher import EventPublisher
from app.services.posts.comment_model import Comment
from app.services.posts.comments_schema import (
    CommentCreate,
    CommentCreatedEvent,
    CommentResponse,
)
from app.services.posts.models import Post

log = get_logger(__name__)


class CommentService:
    def __init__(self, session: AsyncSession, publisher: EventPublisher) -> None:
        self._session = session
        self._publisher = publisher

    # ── Queries ──────────────────────────────────────────────────────────────

    async def _get_post_or_404(self, post_id: uuid.UUID) -> Post:
        result = await self._session.execute(
            select(Post).where(Post.id == post_id)
        )
        post = result.scalar_one_or_none()
        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post {post_id} not found",
            )
        return post

    # ── Commands ─────────────────────────────────────────────────────────────

    async def create_comment(
        self,
        post_id: uuid.UUID,
        author_id: uuid.UUID,
        payload: CommentCreate,
    ) -> CommentResponse:
        """
        Persist comment + emit IF-017 event.

        Transaction is committed before the event fires so the DB write is
        durable even if the event bus is temporarily unavailable.
        """
        post = await self._get_post_or_404(post_id)

        comment = Comment(
            id=uuid.uuid4(),
            post_id=post_id,
            author_id=author_id,
            body=payload.body,
        )
        async with self._session.begin():
            self._session.add(comment)

        # Refresh to pick up server-side defaults (created_at, updated_at)
        await self._session.refresh(comment)

        log.info(
            "comment.created",
            comment_id=str(comment.id),
            post_id=str(post_id),
            author_id=str(author_id),
        )

        # ── IF-017 event emission ────────────────────────────────────────────
        event = CommentCreatedEvent(
            comment_id=comment.id,
            post_id=post_id,
            author_id=author_id,
            post_author_id=post.author_id,
            body_preview=comment.body[:200],
            occurred_at=comment.created_at if comment.created_at else datetime.now(UTC),
        )
        await self._publisher.publish(event.event_type, event.model_dump(mode="json"))

        return CommentResponse.model_validate(comment)

```

### `backend/app/services/posts/models.py`
```python
"""SQLAlchemy ORM model: Post."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.services.posts.comment_model import Comment


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # back-ref populated by Comment.post relationship
    comments: Mapped[list[Comment]] = relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan"
    )

```

### `backend/pyproject.toml`
```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "posts-service"
version = "0.1.0"
description = "Posts micro-service with comments and notification events"
requires-python = ">=3.12"
dependencies = [
    "fastapi==0.111.1",
    "uvicorn[standard]==0.30.1",
    "pydantic==2.7.4",
    "pydantic-settings==2.3.4",
    "sqlalchemy==2.0.31",
    "alembic==1.13.2",
    "asyncpg==0.29.0",
    "greenlet==3.0.3",
    "python-jose[cryptography]==3.3.0",
    "passlib[bcrypt]==1.7.4",
    "httpx==0.27.0",
    "structlog==24.2.0",
    "python-multipart==0.0.9",
]

[project.optional-dependencies]
test = [
    "pytest==8.2.2",
    "pytest-asyncio==0.23.7",
    "anyio==4.4.0",
    "aiosqlite==0.20.0",
    "coverage==7.5.4",
]
lint = [
    "ruff==0.5.0",
    "mypy==1.10.1",
    "types-python-jose==3.3.4.20240106",
    "types-passlib==1.7.7.20240327",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["app*"]

[tool.ruff]
line-length = 99
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "TCH"]
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

```

### `backend/tests/conftest.py`
```python
"""Shared pytest fixtures for the posts service."""
from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.auth import create_access_token
from app.core.config import Settings
from app.core.database import Base, get_session
from app.events.publisher import (
    EventPublisher,
    MemoryEventPublisher,
    get_event_publisher,
    reset_publisher_cache,
)
from app.main import app

# ── In-memory SQLite engine for tests ────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

_test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
_TestSessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_test_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables() -> AsyncGenerator[None, None]:
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with _TestSessionFactory() as session:
        yield session


@pytest.fixture
def memory_publisher() -> MemoryEventPublisher:
    reset_publisher_cache()
    pub = MemoryEventPublisher()
    return pub


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession,
    memory_publisher: MemoryEventPublisher,
) -> AsyncGenerator[AsyncClient, None]:
    """HTTPX async client wired to the test DB and memory publisher."""

    async def _override_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    def _override_publisher() -> EventPublisher:
        return memory_publisher

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_event_publisher] = _override_publisher
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Auth helpers ──────────────────────────────────────────────────────────────

TEST_SETTINGS = Settings(
    secret_key="test-secret-key-must-be-32-chars-xx",  # type: ignore[call-arg]
    database_url=TEST_DATABASE_URL,
)


def make_token(user_id: uuid.UUID | None = None) -> str:
    uid = user_id or uuid.uuid4()
    return create_access_token(uid, TEST_SETTINGS)

```

### `backend/tests/test_comments.py`
```python
"""
AC-021.x — Comment create endpoint + IF-017 event tests.

Coverage:
  AC-021.1  Comment persisted in DB with correct fields
  AC-021.2  HTTP 201 + CommentResponse body returned
  AC-021.3  IF-017 event emitted with correct shape
  AC-021.4  event_type == "comment.created"
  AC-021.5  post_author_id in event matches the post's author
  AC-021.6  body_preview capped at 200 chars
  AC-021.7  401 when no auth token supplied
  AC-021.8  404 when post does not exist
  AC-021.9  422 when body is blank / missing
  AC-021.10 422 when body exceeds max length
"""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.publisher import MemoryEventPublisher
from app.services.posts.models import Post
from tests.conftest import make_token

# ── Helpers ───────────────────────────────────────────────────────────────────


async def _seed_post(session: AsyncSession, author_id: uuid.UUID | None = None) -> Post:
    """Insert a Post row directly so comment tests have a parent."""
    post = Post(
        id=uuid.uuid4(),
        author_id=author_id or uuid.uuid4(),
        title="Test Post",
        body="Post body",
    )
    async with session.begin():
        session.add(post)
    await session.refresh(post)
    return post


# ── AC-021.1 / AC-021.2 ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_comment_persisted_and_201(
    client: AsyncClient,
    db_session: AsyncSession,
    memory_publisher: MemoryEventPublisher,
) -> None:
    """AC-021.1 Comment persisted; AC-021.2 HTTP 201 + response body."""
    commenter_id = uuid.uuid4()
    post = await _seed_post(db_session)
    token = make_token(commenter_id)

    resp = await client.post(
        f"/v1/posts/{post.id}/comments",
        json={"body": "Great post!"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["body"] == "Great post!"
    assert data["post_id"] == str(post.id)
    assert data["author_id"] == str(commenter_id)
    assert "id" in data
    assert "created_at" in data


# ── AC-021.3 / AC-021.4 / AC-021.5 ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_if017_event_emitted(
    client: AsyncClient,
    db_session: AsyncSession,
    memory_publisher: MemoryEventPublisher,
) -> None:
    """AC-021.3 event emitted; AC-021.4 event_type; AC-021.5 post_author_id."""
    post_author_id = uuid.uuid4()
    commenter_id = uuid.uuid4()
    post = await _seed_post(db_session, author_id=post_author_id)
    token = make_token(commenter_id)

    resp = await client.post(
        f"/v1/posts/{post.id}/comments",
        json={"body": "Nice work!"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201

    assert len(memory_publisher.events) == 1
    evt = memory_publisher.events[0]
    assert evt["event_type"] == "comment.created"
    assert evt["post_id"] == str(post.id)
    assert evt["author_id"] == str(commenter_id)
    assert evt["post_author_id"] == str(post_author_id)


# ── AC-021.6 ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_body_preview_capped_at_200(
    client: AsyncClient,
    db_session: AsyncSession,
    memory_publisher: MemoryEventPublisher,
) -> None:
    """AC-021.6 body_preview must not exceed 200 chars."""
    post = await _seed_post(db_session)
    long_body = "x" * 500
    token = make_token()

    resp = await client.post(
        f"/v1/posts/{post.id}/comments",
        json={"body": long_body},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert len(memory_publisher.events) == 1
    preview = memory_publisher.events[0]["body_preview"]
    assert len(preview) <= 200


# ── AC-021.7 ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unauthenticated_returns_401(
    client: AsyncClient,
    db_session: AsyncSession,
    memory_publisher: MemoryEventPublisher,
) -> None:
    """AC-021.7 missing auth → 401."""
    post = await _seed_post(db_session)
    resp = await client.post(
        f"/v1/posts/{post.id}/comments",
        json={"body": "Sneaky"},
    )
    assert resp.status_code == 401
    assert len(memory_publisher.events) == 0


# ── AC-021.8 ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_post_not_found_returns_404(
    client: AsyncClient,
    memory_publisher: MemoryEventPublisher,
) -> None:
    """AC-021.8 non-existent post → 404; no event fired."""
    token = make_token()
    missing_id = uuid.uuid4()

    resp = await client.post(
        f"/v1/posts/{missing_id}/comments",
        json={"body": "Hello?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
    assert len(memory_publisher.events) == 0


# ── AC-021.9 ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_blank_body_returns_422(
    client: AsyncClient,
    db_session: AsyncSession,
    memory_publisher: MemoryEventPublisher,
) -> None:
    """AC-021.9 blank/whitespace-only body → 422."""
    post = await _seed_post(db_session)
    token = make_token()

    for bad_body in ["", "   ", "\t\n"]:
        resp = await client.post(
            f"/v1/posts/{post.id}/comments",
            json={"body": bad_body},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422, f"Expected 422 for body={bad_body!r}"

    assert len(memory_publisher.events) == 0


# ── AC-021.10 ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_oversized_body_returns_422(
    client: AsyncClient,
    db_session: AsyncSession,
    memory_publisher: MemoryEventPublisher,
) -> None:
    """AC-021.10 body > 10 000 chars → 422."""
    post = await _seed_post(db_session)
    token = make_token()

    resp = await client.post(
        f"/v1/posts/{post.id}/comments",
        json={"body": "a" * 10_001},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422
    assert len(memory_publisher.events) == 0

```