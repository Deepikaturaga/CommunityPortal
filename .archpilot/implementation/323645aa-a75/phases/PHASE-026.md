# Implementation Report

Now fix the test files' import ordering and TC warnings:

## Verification
- `python3 -c "
import os, sys

def walk(root, indent=0):
    try:
        entries = sorted(os.listdir(root))
    except PermissionError:
        return
    for e in entries:
        if e in {'.git', '__pycache__', '.mypy_cache', '.ruff_cache', 'node_modules', '.venv', 'venv'}:
            continue
        path = os.path.join(root, e)
        print('  ' * indent + e)
        if os.path.isdir(path):
            walk(path, indent + 1)

walk('backend')
"` → exit 1
- `python3 -c "
import os

def walk(root, indent=0):
    try:
        entries = sorted(os.listdir(root))
    except (PermissionError, FileNotFoundError):
        return
    for e in entries:
        if e in {'.git', '__pycache__', '.mypy_cache', '.ruff_cache', 'node_modules', '.venv', 'venv', 'dist', '.pytest_cache'}:
            continue
        path = os.path.join(root, e)
        print('  ' * indent + e)
        if os.path.isdir(path):
            walk(path, indent + 1)

walk('.')
"` → exit 0
- `python3 -c "import os; print(os.getcwd()); print(os.listdir('.'))"` → exit 0
- `pip install -q "fastapi==0.115.5" "uvicorn[standard]==0.32.1" "pydantic==2.10.3" "pydantic-settings==2.6.1" "sqlalchemy==2.0.36" "alembic==1.14.0" "python-jose[cryptography]==3.3.0" "passlib[bcrypt]==1.7.4" "python-multipart==0.0.18" "httpx==0.28.0" "pytest==8.3.4" "pytest-asyncio==0.24.0" "aiosqlite==0.20.0" "email-validator==2.2.0"` → exit 0
- `pip show fastapi pydantic pydantic-settings sqlalchemy alembic httpx python-multipart pytest pytest-asyncio aiosqlite python-jose passlib` → exit 0
- `pip show fastapi pydantic` → exit 0
- `python -m pytest tests/services/test_visibility.py tests/api/test_posts_visibility.py -v --tb=short 2>&1` → exit 4
- `python -m pytest tests/services/test_visibility.py tests/api/test_posts_visibility.py -v --tb=short` → exit 4
- `python -m pytest tests/services/test_visibility.py tests/api/test_posts_visibility.py -v --tb=short` → exit 0
- `ruff check app/services/posts/visibility.py app/services/posts/service.py app/core/enums.py app/models/post.py app/models/user.py tests/services/test_visibility.py tests/api/test_posts_visibility.py` → exit 1

## Generated Files

### `backend/.env.example`
```text
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/blog_dev
SECRET_KEY=change-me-in-production-use-openssl-rand-hex-32
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256
ENVIRONMENT=development

```

### `backend/alembic.ini`
```text
[alembic]
script_location = alembic
prepend_sys_path = .
file_template = %%(year)d%%(month).2d%%(day).2d_%%(rev)s_%%(slug)s
sqlalchemy.url = sqlite+aiosqlite:///./blog_dev.db

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

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.core.database import Base
import app.models  # noqa: F401  — registers all ORM models

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = get_settings().database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    settings = get_settings()
    connectable = create_async_engine(settings.database_url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())

```

### `backend/alembic/script.py.mako`
```text
${message}

```

### `backend/alembic/versions/0001_initial_schema.py`
```python
"""Initial schema: users + posts tables.

Revision ID: 0001
Revises: 
Create Date: 2025-01-01 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "author", "reader", name="userrole"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "posts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "published", "archived", name="poststatus"),
            nullable=False,
        ),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_posts_slug", "posts", ["slug"], unique=True)
    op.create_index("ix_posts_status", "posts", ["status"], unique=False)
    op.create_index("ix_posts_author_id", "posts", ["author_id"], unique=False)


def downgrade() -> None:
    op.drop_table("posts")
    op.drop_table("users")

```

### `backend/app/__init__.py`
```python
"""App package init."""

```

### `backend/app/core/__init__.py`
```python
"""Core sub-package."""

```

### `backend/app/core/config.py`
```python
"""Application configuration via pydantic-settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./blog_test.db",
        description="SQLAlchemy async database URL",
    )

    # JWT / Auth
    secret_key: str = Field(
        default="CHANGE_ME_IN_PRODUCTION",
        description="HMAC secret for JWT signing",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Runtime
    environment: str = "development"
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()

```

### `backend/app/core/database.py`
```python
"""SQLAlchemy 2.0 async engine + session factory."""

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


def _make_engine():
    settings = get_settings()
    connect_args: dict = {}
    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_async_engine(
        settings.database_url,
        echo=settings.debug,
        connect_args=connect_args,
    )


engine = _make_engine()

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an async DB session and closes it when done."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

```

### `backend/app/core/enums.py`
```python
"""Domain enumerations shared across the application."""

import enum


class UserRole(str, enum.Enum):
    """Roles available to user accounts."""

    ADMIN = "admin"
    AUTHOR = "author"
    READER = "reader"


class PostStatus(str, enum.Enum):
    """Publication lifecycle status for a post."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

```

### `backend/app/core/security.py`
```python
"""JWT creation and verification helpers."""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.core.config import get_settings


def create_access_token(subject: str | int, extra: dict[str, Any] | None = None) -> str:
    """Return a signed JWT access token for *subject*."""
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        **(extra or {}),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT; raises JWTError on failure."""
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


__all__ = ["create_access_token", "decode_access_token", "JWTError"]

```

### `backend/app/dependencies/__init__.py`
```python
"""Dependencies sub-package."""

```

### `backend/app/dependencies/auth.py`
```python
"""FastAPI dependency: resolve the currently-authenticated user from a Bearer JWT."""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Return the User whose JWT is supplied, or raise 401."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        sub: str | None = payload.get("sub")
        if sub is None:
            raise credentials_exc
        user_id = uuid.UUID(sub)
    except (JWTError, ValueError):
        raise credentials_exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exc
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Return the current user; raises 401 if inactive."""
    return current_user


async def get_optional_user(
    token: str | None = Depends(
        OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)
    ),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Return the current user if a valid token is present, else None."""
    if token is None:
        return None
    try:
        payload = decode_access_token(token)
        sub: str | None = payload.get("sub")
        if sub is None:
            return None
        user_id = uuid.UUID(sub)
    except (JWTError, ValueError):
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        return None
    return user

```

### `backend/app/main.py`
```python
"""ASGI application entrypoint."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import Base, engine
from app.routes.auth_router import router as auth_router
from app.routes.posts_router import router as posts_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create tables on startup (dev/test). Alembic handles production migrations."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Blog API",
        version="1.0.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.exception_handler(Exception)
    async def _unhandled(_req: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    PREFIX = "/api/v1"
    app.include_router(auth_router, prefix=PREFIX)
    app.include_router(posts_router, prefix=PREFIX)

    @app.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

```

### `backend/app/models/__init__.py`
```python
"""Re-export all ORM models so Alembic autogenerate can discover them."""

from app.models.post import Post
from app.models.user import User

__all__ = ["User", "Post"]

```

### `backend/app/models/post.py`
```python
"""Post ORM model."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import PostStatus


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus, name="poststatus"),
        nullable=False,
        default=PostStatus.DRAFT,
        index=True,
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    author: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="posts", lazy="selectin"
    )

```

### `backend/app/models/user.py`
```python
"""User ORM model."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole"), nullable=False, default=UserRole.READER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    posts: Mapped[list["Post"]] = relationship(  # noqa: F821
        "Post", back_populates="author", lazy="selectin"
    )

```

### `backend/app/routes/__init__.py`
```python
"""Routes sub-package."""

```

### `backend/app/routes/auth_router.py`
```python
"""Auth router — login token endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/token", response_model=Token)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    result = await db.execute(select(User).where(User.email == form.username))
    user = result.scalar_one_or_none()
    if user is None or not _pwd_ctx.verify(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(str(user.id))
    return Token(access_token=token)

```

### `backend/app/routes/posts_router.py`
```python
"""Posts REST API router with visibility enforcement."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_active_user, get_optional_user
from app.models.user import User
from app.schemas.posts import PostCreate, PostRead, PostUpdate
from app.services.posts.service import PostService

router = APIRouter(prefix="/posts", tags=["posts"])


def _svc(db: AsyncSession = Depends(get_db)) -> PostService:
    return PostService(db)


@router.get("", response_model=list[PostRead])
async def list_posts(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    viewer: User | None = Depends(get_optional_user),
    svc: PostService = Depends(_svc),
) -> list[PostRead]:
    posts = await svc.list_visible(viewer, limit=limit, offset=offset)
    return [PostRead.model_validate(p) for p in posts]


@router.post("", response_model=PostRead, status_code=status.HTTP_201_CREATED)
async def create_post(
    data: PostCreate,
    author: User = Depends(get_current_active_user),
    svc: PostService = Depends(_svc),
) -> PostRead:
    post = await svc.create(data, author)
    return PostRead.model_validate(post)


@router.get("/{post_id}", response_model=PostRead)
async def get_post(
    post_id: uuid.UUID,
    viewer: User | None = Depends(get_optional_user),
    svc: PostService = Depends(_svc),
) -> PostRead:
    post = await svc.get_by_id(post_id, viewer)
    return PostRead.model_validate(post)


@router.patch("/{post_id}", response_model=PostRead)
async def update_post(
    post_id: uuid.UUID,
    data: PostUpdate,
    editor: User = Depends(get_current_active_user),
    svc: PostService = Depends(_svc),
) -> PostRead:
    post = await svc.update(post_id, data, editor)
    return PostRead.model_validate(post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_post(
    post_id: uuid.UUID,
    actor: User = Depends(get_current_active_user),
    svc: PostService = Depends(_svc),
) -> None:
    await svc.delete(post_id, actor)

```

### `backend/app/schemas/__init__.py`
```python
"""Schemas sub-package."""

```

### `backend/app/schemas/posts.py`
```python
"""Pydantic schemas for Post domain."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import PostStatus


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    body: str = Field(default="")
    status: PostStatus = PostStatus.DRAFT


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(
        default=None, min_length=1, max_length=255, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    body: str | None = None
    status: PostStatus | None = None


class PostRead(PostBase):
    id: uuid.UUID
    author_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

```

### `backend/app/schemas/users.py`
```python
"""Pydantic schemas for User domain."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.core.enums import UserRole


class UserBase(BaseModel):
    email: EmailStr
    display_name: str = Field(default="", max_length=120)
    role: UserRole = UserRole.READER


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRead(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserInDB(UserRead):
    hashed_password: str

```

### `backend/app/services/posts/init_pkg.py`
```python
"""Post service package exports."""

from app.services.posts.service import PostService
from app.services.posts.visibility import (
    assert_can_delete,
    assert_can_edit,
    assert_post_visible,
    assert_post_visible_and_editable,
)

__all__ = [
    "PostService",
    "assert_can_delete",
    "assert_can_edit",
    "assert_post_visible",
    "assert_post_visible_and_editable",
]

```

### `backend/app/services/posts/service.py`
```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.user import User
    from app.schemas.posts import PostCreate, PostUpdate

    async def get_by_id(self, post_id: uuid.UUID, viewer: "User | None") -> Post:
    async def get_by_slug(self, slug: str, viewer: "User | None") -> Post:
        viewer: "User | None",
            pass  # no filter -- admin sees all
    async def create(self, data: "PostCreate", author: "User") -> Post:
        data: "PostUpdate",
        editor: "User",
    async def delete(self, post_id: uuid.UUID, actor: "User") -> None:
"""Post service — thin persistence layer consumed by routers."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import PostStatus
from app.models.post import Post
from app.services.posts.visibility import assert_post_visible, assert_post_visible_and_editable


class PostService:
    """CRUD operations for posts with integrated visibility enforcement."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

        """Return *post_id* if *viewer* may see it, else raise HTTP 404."""
        result = await self._db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        return assert_post_visible(post, viewer)

        """Return the post with *slug* if *viewer* may see it, else raise HTTP 404."""
        result = await self._db.execute(select(Post).where(Post.slug == slug))
        post = result.scalar_one_or_none()
        return assert_post_visible(post, viewer)

    async def list_visible(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Post]:
        """
        Return posts the *viewer* is allowed to see.

        - Unauthenticated or READER users: published posts only.
        - AUTHOR: published posts + own drafts.
        - ADMIN: all posts.
        """
        stmt = select(Post).order_by(Post.created_at.desc()).limit(limit).offset(offset)

        if viewer is None:
            stmt = stmt.where(Post.status == PostStatus.PUBLISHED)
        elif viewer.role.value == "admin":
        else:
            # author sees their own drafts + all published
            from sqlalchemy import or_

            stmt = stmt.where(
                or_(
                    Post.status == PostStatus.PUBLISHED,
                    (Post.status == PostStatus.DRAFT) & (Post.author_id == viewer.id),
                )
            )

        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

        post = Post(
            title=data.title,
            slug=data.slug,
            body=data.body,
            status=data.status,
            author_id=author.id,
        )
        self._db.add(post)
        await self._db.flush()
        await self._db.refresh(post)
        return post

    async def update(
        self,
        post_id: uuid.UUID,
    ) -> Post:
        """Update a post — raises 404 if not visible, 403 if not owner/admin."""
        result = await self._db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        post = assert_post_visible_and_editable(post, editor)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(post, field, value)

        await self._db.flush()
        await self._db.refresh(post)
        return post

        """Delete a post — raises 404 if not visible, 403 if not owner/admin."""
        result = await self._db.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()
        post = assert_post_visible_and_editable(post, actor)
        await self._db.delete(post)
        await self._db.flush()

```

### `backend/app/services/posts/visibility.py`
```python
"""
Post visibility rules -- AC-017.1, AC-019.3
============================================

Rules enforced here:
- DRAFT posts are only visible to their author and to admins.
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from app.models.post import Post
    from app.models.user import User
def _is_admin(user: "User") -> bool:
def _is_owner(post: "Post", user: "User") -> bool:
def _can_view_draft(post: "Post", viewer: "User | None") -> bool:
def assert_post_visible(post: "Post | None", viewer: "User | None") -> "Post":
        # Return 404 -- not 403 -- to avoid leaking draft existence (AC-017.1)
def assert_can_edit(post: "Post", editor: "User") -> None:
def assert_can_delete(post: "Post", actor: "User") -> None:
    """Alias of assert_can_edit -- same ownership semantics apply to deletion."""
def assert_post_visible_and_editable(post: "Post | None", actor: "User") -> "Post":
- Any other caller receives HTTP 404 (not 403) to avoid leaking draft existence.
- Edit (PUT/PATCH) and delete (DELETE) operations additionally require ownership
  or admin role (AC-019.x, AC-020.x).

All public-facing helpers raise HTTPException so routers can remain thin.
"""

from __future__ import annotations

from fastapi import HTTPException, status

from app.core.enums import PostStatus, UserRole


# ---------------------------------------------------------------------------
# Primitive predicates
# ---------------------------------------------------------------------------


    return user.role == UserRole.ADMIN


    return post.author_id == user.id


    """Return True when *viewer* is allowed to see a DRAFT post."""
    if viewer is None:
        return False
    return _is_owner(post, viewer) or _is_admin(viewer)


# ---------------------------------------------------------------------------
# Visibility gate (AC-017.1)
# ---------------------------------------------------------------------------


    """
    Ensure *viewer* may see *post*.

    Raises HTTP 404 in all cases where the post should not be visible so that
    draft existence is not disclosed to unauthorised callers.

    Returns the post unchanged when access is permitted.
    """
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if post.status == PostStatus.DRAFT and not _can_view_draft(post, viewer):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    return post


# ---------------------------------------------------------------------------
# Ownership gate (AC-019.3 / AC-020.x)
# ---------------------------------------------------------------------------


    """
    Ensure *editor* is allowed to mutate (edit or delete) *post*.

    Authors may only edit their own posts.  Admins may edit any post.
    Raises HTTP 403 on failure.
    """
    if _is_admin(editor) or _is_owner(post, editor):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to modify this post",
    )


    assert_can_edit(post, actor)


# ---------------------------------------------------------------------------
# Convenience: combined visibility + ownership (for edit/delete endpoints)
# ---------------------------------------------------------------------------


    """
    Resolve visibility for the *actor* (who is authenticated) and then check
    edit rights.  Draft posts are already visible to their own author, so a
    single author calling an edit endpoint receives the correct behaviour.

    Returns the resolved post on success.
    """
    resolved = assert_post_visible(post, actor)
    assert_can_edit(resolved, actor)
    return resolved

```

### `backend/pyproject.toml`
```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "blog-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi==0.115.5",
    "uvicorn[standard]==0.32.1",
    "pydantic==2.10.3",
    "pydantic-settings==2.6.1",
    "sqlalchemy==2.0.36",
    "alembic==1.14.0",
    "asyncpg==0.30.0",
    "python-jose[cryptography]==3.3.0",
    "passlib[bcrypt]==1.7.4",
    "python-multipart==0.0.18",
    "httpx==0.28.0",
    "greenlet==3.1.1",
]

[project.optional-dependencies]
test = [
    "pytest==8.3.4",
    "pytest-asyncio==0.24.0",
    "httpx==0.28.0",
    "aiosqlite==0.20.0",
]
lint = [
    "ruff==0.8.3",
    "mypy==1.13.0",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["app*"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "TCH"]
ignore = ["B008"]

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true
plugins = ["pydantic.mypy"]

```

### `backend/tests/__init__.py`
```python
# pytest root marker

```

### `backend/tests/api/__init__.py`
```python
# pytest root marker

```

### `backend/tests/api/test_posts_visibility.py`
```python
"""
HTTP integration tests for posts endpoints — draft visibility & ownership.

VER-002 (HTTP layer): GET /api/v1/posts/{id} returns 404 for draft to non-owner
VER-004 (HTTP layer): PATCH/DELETE returns 403 for non-owner on published post,
                      404 for non-owner on draft (existence not leaked)
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.post import Post
from app.models.user import User
from tests.conftest import bearer


@pytest.mark.asyncio
class TestDraftVisibilityHTTP:
    """VER-002: Draft post 404 to unauthenticated + non-owner callers."""

    async def test_draft_unauthenticated_returns_404(
        self, client: AsyncClient, draft_post: Post
    ) -> None:
        resp = await client.get(f"/api/v1/posts/{draft_post.id}")
        assert resp.status_code == 404

    async def test_draft_non_owner_returns_404(
        self,
        client: AsyncClient,
        draft_post: Post,
        other_author_user: User,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{draft_post.id}", headers=bearer(other_author_user)
        )
        assert resp.status_code == 404

    async def test_draft_owner_returns_200(
        self,
        client: AsyncClient,
        draft_post: Post,
        author_user: User,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{draft_post.id}", headers=bearer(author_user)
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == str(draft_post.id)

    async def test_draft_admin_returns_200(
        self,
        client: AsyncClient,
        draft_post: Post,
        admin_user: User,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{draft_post.id}", headers=bearer(admin_user)
        )
        assert resp.status_code == 200

    async def test_published_unauthenticated_returns_200(
        self, client: AsyncClient, published_post: Post
    ) -> None:
        resp = await client.get(f"/api/v1/posts/{published_post.id}")
        assert resp.status_code == 200

    async def test_list_excludes_drafts_for_unauthenticated(
        self,
        client: AsyncClient,
        draft_post: Post,
        published_post: Post,
    ) -> None:
        resp = await client.get("/api/v1/posts")
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()]
        assert str(published_post.id) in ids
        assert str(draft_post.id) not in ids

    async def test_list_includes_own_draft_for_author(
        self,
        client: AsyncClient,
        draft_post: Post,
        published_post: Post,
        author_user: User,
    ) -> None:
        resp = await client.get("/api/v1/posts", headers=bearer(author_user))
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()]
        assert str(draft_post.id) in ids

    async def test_list_excludes_others_drafts_for_different_author(
        self,
        client: AsyncClient,
        draft_post: Post,
        other_author_user: User,
    ) -> None:
        resp = await client.get("/api/v1/posts", headers=bearer(other_author_user))
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()]
        assert str(draft_post.id) not in ids

    async def test_list_includes_all_drafts_for_admin(
        self,
        client: AsyncClient,
        draft_post: Post,
        admin_user: User,
    ) -> None:
        resp = await client.get("/api/v1/posts", headers=bearer(admin_user))
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()]
        assert str(draft_post.id) in ids


@pytest.mark.asyncio
class TestOwnershipEnforcementHTTP:
    """VER-004: PATCH/DELETE ownership checks."""

    async def test_owner_can_patch_own_post(
        self,
        client: AsyncClient,
        published_post: Post,
        author_user: User,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{published_post.id}",
            json={"title": "Updated title"},
            headers=bearer(author_user),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated title"

    async def test_non_owner_patch_published_returns_403(
        self,
        client: AsyncClient,
        published_post: Post,
        other_author_user: User,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{published_post.id}",
            json={"title": "Stolen edit"},
            headers=bearer(other_author_user),
        )
        assert resp.status_code == 403

    async def test_non_owner_patch_draft_returns_404(
        self,
        client: AsyncClient,
        draft_post: Post,
        other_author_user: User,
    ) -> None:
        """Non-owner patching a draft should receive 404, not 403 (draft existence hidden)."""
        resp = await client.patch(
            f"/api/v1/posts/{draft_post.id}",
            json={"title": "Stolen edit"},
            headers=bearer(other_author_user),
        )
        assert resp.status_code == 404

    async def test_admin_can_patch_any_post(
        self,
        client: AsyncClient,
        published_post: Post,
        admin_user: User,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{published_post.id}",
            json={"title": "Admin override"},
            headers=bearer(admin_user),
        )
        assert resp.status_code == 200

    async def test_owner_can_delete_own_post(
        self,
        client: AsyncClient,
        published_post: Post,
        author_user: User,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/posts/{published_post.id}", headers=bearer(author_user)
        )
        assert resp.status_code == 204

    async def test_non_owner_delete_published_returns_403(
        self,
        client: AsyncClient,
        published_post: Post,
        other_author_user: User,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/posts/{published_post.id}", headers=bearer(other_author_user)
        )
        assert resp.status_code == 403

    async def test_non_owner_delete_draft_returns_404(
        self,
        client: AsyncClient,
        draft_post: Post,
        other_author_user: User,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/posts/{draft_post.id}", headers=bearer(other_author_user)
        )
        assert resp.status_code == 404

    async def test_admin_can_delete_any_post(
        self,
        client: AsyncClient,
        published_post: Post,
        admin_user: User,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/posts/{published_post.id}", headers=bearer(admin_user)
        )
        assert resp.status_code == 204

    async def test_unauthenticated_patch_returns_401(
        self, client: AsyncClient, published_post: Post
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{published_post.id}", json={"title": "x"}
        )
        assert resp.status_code == 401

    async def test_unauthenticated_delete_returns_401(
        self, client: AsyncClient, published_post: Post
    ) -> None:
        resp = await client.delete(f"/api/v1/posts/{published_post.id}")
        assert resp.status_code == 401

```

### `backend/tests/conftest.py`
```python
"""Shared pytest fixtures for the backend test suite."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.enums import PostStatus, UserRole
from app.core.security import create_access_token
from app.main import create_app
from app.models.post import Post
from app.models.user import User

# ---------------------------------------------------------------------------
# In-memory SQLite engine for tests
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

_test_engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
_TestSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_test_engine, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with _TestSessionLocal() as session:
        yield session
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Helpers: build ORM objects directly (no HTTP) to keep tests fast
# ---------------------------------------------------------------------------


def _make_user(
    role: UserRole = UserRole.READER,
    *,
    user_id: uuid.UUID | None = None,
    email: str | None = None,
) -> User:
    uid = user_id or uuid.uuid4()
    return User(
        id=uid,
        email=email or f"{uid}@example.com",
        hashed_password="$2b$12$notreal",
        display_name="Test User",
        role=role,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_post(
    author: User,
    status: PostStatus = PostStatus.PUBLISHED,
    *,
    post_id: uuid.UUID | None = None,
) -> Post:
    pid = post_id or uuid.uuid4()
    return Post(
        id=pid,
        title="Test Post",
        slug=f"test-post-{pid}",
        body="Body text",
        status=status,
        author_id=author.id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest_asyncio.fixture
async def author_user(db: AsyncSession) -> User:
    user = _make_user(UserRole.AUTHOR)
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def other_author_user(db: AsyncSession) -> User:
    user = _make_user(UserRole.AUTHOR)
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession) -> User:
    user = _make_user(UserRole.ADMIN)
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def reader_user(db: AsyncSession) -> User:
    user = _make_user(UserRole.READER)
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def draft_post(db: AsyncSession, author_user: User) -> Post:
    post = _make_post(author_user, PostStatus.DRAFT)
    db.add(post)
    await db.flush()
    return post


@pytest_asyncio.fixture
async def published_post(db: AsyncSession, author_user: User) -> Post:
    post = _make_post(author_user, PostStatus.PUBLISHED)
    db.add(post)
    await db.flush()
    return post


def bearer(user: User) -> dict[str, Any]:
    """Return Authorization header for a user."""
    token = create_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}

```

### `backend/tests/services/__init__.py`
```python
# pytest root marker

```

### `backend/tests/services/test_visibility.py`
```python
"""
Unit tests for app/services/posts/visibility.py

VER-002: Draft post visibility rules
  - Unauthenticated caller gets 404 on a draft post
  - Wrong-user (non-owner, non-admin) gets 404 on a draft post
  - Post owner gets the post back for their own draft
  - Admin gets the post back for any draft
  - Published posts are visible to everyone (None, reader, author, admin)

VER-004: Ownership / edit-rights enforcement
  - Owner can edit own post (published or draft)
  - Admin can edit any post
  - Non-owner, non-admin raises 403 on edit
  - Non-owner, non-admin raises 403 on delete
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

from app.core.enums import PostStatus, UserRole
from app.models.post import Post
from app.models.user import User
from app.services.posts.visibility import (
    assert_can_delete,
    assert_can_edit,
    assert_post_visible,
    assert_post_visible_and_editable,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _user(role: UserRole, uid: uuid.UUID | None = None) -> User:
    uid = uid or uuid.uuid4()
    return User(
        id=uid,
        email=f"{uid}@test.com",
        hashed_password="x",
        display_name="U",
        role=role,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _post(author: User, status: PostStatus) -> Post:
    pid = uuid.uuid4()
    return Post(
        id=pid,
        title="T",
        slug=f"slug-{pid}",
        body="B",
        status=status,
        author_id=author.id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


# ===========================================================================
# VER-002 — assert_post_visible
# ===========================================================================


class TestDraftVisibility:
    """AC-017.1: Draft posts are only visible to owner or admin."""

    def test_none_post_raises_404(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            assert_post_visible(None, viewer=None)
        assert exc_info.value.status_code == 404

    def test_draft_unauthenticated_raises_404(self) -> None:
        author = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.DRAFT)
        with pytest.raises(HTTPException) as exc_info:
            assert_post_visible(post, viewer=None)
        assert exc_info.value.status_code == 404, "Must be 404 not 403 (AC-017.1)"

    def test_draft_non_owner_reader_raises_404(self) -> None:
        author = _user(UserRole.AUTHOR)
        reader = _user(UserRole.READER)
        post = _post(author, PostStatus.DRAFT)
        with pytest.raises(HTTPException) as exc_info:
            assert_post_visible(post, viewer=reader)
        assert exc_info.value.status_code == 404

    def test_draft_non_owner_author_raises_404(self) -> None:
        author = _user(UserRole.AUTHOR)
        other = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.DRAFT)
        with pytest.raises(HTTPException) as exc_info:
            assert_post_visible(post, viewer=other)
        assert exc_info.value.status_code == 404

    def test_draft_owner_can_see_own_draft(self) -> None:
        author = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.DRAFT)
        result = assert_post_visible(post, viewer=author)
        assert result is post

    def test_draft_admin_can_see_any_draft(self) -> None:
        author = _user(UserRole.AUTHOR)
        admin = _user(UserRole.ADMIN)
        post = _post(author, PostStatus.DRAFT)
        result = assert_post_visible(post, viewer=admin)
        assert result is post

    def test_published_visible_to_none(self) -> None:
        author = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.PUBLISHED)
        result = assert_post_visible(post, viewer=None)
        assert result is post

    def test_published_visible_to_reader(self) -> None:
        author = _user(UserRole.AUTHOR)
        reader = _user(UserRole.READER)
        post = _post(author, PostStatus.PUBLISHED)
        assert assert_post_visible(post, viewer=reader) is post

    def test_published_visible_to_different_author(self) -> None:
        author = _user(UserRole.AUTHOR)
        other = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.PUBLISHED)
        assert assert_post_visible(post, viewer=other) is post

    def test_published_visible_to_admin(self) -> None:
        author = _user(UserRole.AUTHOR)
        admin = _user(UserRole.ADMIN)
        post = _post(author, PostStatus.PUBLISHED)
        assert assert_post_visible(post, viewer=admin) is post


# ===========================================================================
# VER-004 — assert_can_edit / assert_can_delete
# ===========================================================================


class TestOwnershipEnforcement:
    """AC-019.3 / AC-020.x: Only owners and admins may edit/delete."""

    def test_owner_can_edit_own_published_post(self) -> None:
        author = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.PUBLISHED)
        assert_can_edit(post, editor=author)  # no exception

    def test_owner_can_edit_own_draft(self) -> None:
        author = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.DRAFT)
        assert_can_edit(post, editor=author)

    def test_admin_can_edit_any_post(self) -> None:
        author = _user(UserRole.AUTHOR)
        admin = _user(UserRole.ADMIN)
        post = _post(author, PostStatus.PUBLISHED)
        assert_can_edit(post, editor=admin)

    def test_non_owner_reader_cannot_edit(self) -> None:
        author = _user(UserRole.AUTHOR)
        reader = _user(UserRole.READER)
        post = _post(author, PostStatus.PUBLISHED)
        with pytest.raises(HTTPException) as exc_info:
            assert_can_edit(post, editor=reader)
        assert exc_info.value.status_code == 403

    def test_non_owner_author_cannot_edit(self) -> None:
        author = _user(UserRole.AUTHOR)
        other = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.PUBLISHED)
        with pytest.raises(HTTPException) as exc_info:
            assert_can_edit(post, editor=other)
        assert exc_info.value.status_code == 403

    def test_owner_can_delete_own_post(self) -> None:
        author = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.PUBLISHED)
        assert_can_delete(post, actor=author)

    def test_admin_can_delete_any_post(self) -> None:
        author = _user(UserRole.AUTHOR)
        admin = _user(UserRole.ADMIN)
        post = _post(author, PostStatus.DRAFT)
        assert_can_delete(post, actor=admin)

    def test_non_owner_cannot_delete(self) -> None:
        author = _user(UserRole.AUTHOR)
        other = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.PUBLISHED)
        with pytest.raises(HTTPException) as exc_info:
            assert_can_delete(post, actor=other)
        assert exc_info.value.status_code == 403


# ===========================================================================
# Combined: assert_post_visible_and_editable
# ===========================================================================


class TestVisibleAndEditable:
    """Combined visibility + edit-right check used by update/delete endpoints."""

    def test_owner_of_draft_can_edit(self) -> None:
        author = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.DRAFT)
        result = assert_post_visible_and_editable(post, actor=author)
        assert result is post

    def test_stranger_on_draft_gets_404_not_403(self) -> None:
        """Non-owner of a draft must get 404 (existence not leaked)."""
        author = _user(UserRole.AUTHOR)
        stranger = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.DRAFT)
        with pytest.raises(HTTPException) as exc_info:
            assert_post_visible_and_editable(post, actor=stranger)
        assert exc_info.value.status_code == 404  # visibility check fires first

    def test_non_owner_on_published_gets_403(self) -> None:
        author = _user(UserRole.AUTHOR)
        other = _user(UserRole.READER)
        post = _post(author, PostStatus.PUBLISHED)
        with pytest.raises(HTTPException) as exc_info:
            assert_post_visible_and_editable(post, actor=other)
        assert exc_info.value.status_code == 403

    def test_none_post_gives_404(self) -> None:
        actor = _user(UserRole.ADMIN)
        with pytest.raises(HTTPException) as exc_info:
            assert_post_visible_and_editable(None, actor=actor)
        assert exc_info.value.status_code == 404

```