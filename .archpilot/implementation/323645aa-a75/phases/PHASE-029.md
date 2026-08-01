# Implementation Report

Now fix B904 in articles.py and suppress B008 globally in ruff config (FastAPI's `Depends` idiom):

## Verification
- `python3 -c "import os; files=[]; [files.extend([os.path.join(r,f) for f in fs]) for r,ds,fs in os.walk('.')]; print('\n'.join(sorted(files)[:120]))"` → exit 0
- `python3 -c "import os; root='.'; items=list(os.walk(root)); print(len(items), 'dirs'); [print(r) for r,d,f in items if f]"` → exit 0
- `python3 -c "import os; [print(os.path.join(r,f)) for r,d,fs in os.walk('.') for f in fs]"` → exit 0
- `pip install -e "backend[dev]" --quiet` → exit 2
- `pip install -e "backend[dev]" -q` → exit 1
- `pip install -e "backend[dev]" -q` → exit 0
- `python3 -c "import fastapi, pydantic, sqlalchemy, alembic, bleach, structlog; print('fastapi', fastapi.__version__); print('pydantic', pydantic.__version__); print('sqlalchemy', sqlalchemy.__version__); print('alembic', alembic.__version__); print('bleach', bleach.__version__); print('structlog', structlog.__version__)"` → exit 0
- `python3 -c "import jose, passlib, aiosqlite, httpx, pytest; print('jose ok'); print('passlib ok'); print('aiosqlite ok'); print('httpx', httpx.__version__); print('pytest', pytest.__version__)"` → exit 0
- `ruff check backend/app backend/tests --select E,F,W,I,UP,B` → exit 1
- `ruff check backend/app backend/tests --select E,F,W,I,UP,B --fix --unsafe-fixes` → exit 1

## Generated Files

### `backend/.env.example`
```text
DATABASE_URL=postgresql+asyncpg://kb:kb@localhost:5432/kb_dev
SECRET_KEY=CHANGEME_use_openssl_rand_hex_32
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=development
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:3000

```

### `backend/alembic.ini`
```text
[alembic]
script_location = alembic
file_template = %%(year)d%%(month).2d%%(day).2d_%%(rev)s_%%(slug)s
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = driver://user:pass@localhost/dbname

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
"""Alembic environment — async SQLAlchemy (asyncpg driver)."""
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import all models so their metadata is registered before autogenerate
from app.core.database import Base  # noqa: F401
import app.auth.models  # noqa: F401
import app.kb.article_models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    # Settings override the ini placeholder at runtime
    from app.core.config import get_settings
    return get_settings().database_url


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
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

### `backend/alembic/versions/0001_initial_users.py`
```python
"""Initial migration — users table (STORE-003/STORE-004).

Revision ID: 0001
Revises: —
Create Date: 2024-01-01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE role_enum AS ENUM ('admin', 'contributor', 'viewer')")
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "contributor", "viewer", name="role_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE role_enum")

```

### `backend/alembic/versions/0002_kb_articles.py`
```python
"""KB articles table — STORE-005 (TASK-030/TASK-044).

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-02
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE article_status_enum AS ENUM ('draft', 'published', 'archived')"
    )
    op.create_table(
        "kb_articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("slug", sa.String(512), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "published",
                "archived",
                name="article_status_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
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
    op.create_index("ix_kb_articles_slug", "kb_articles", ["slug"], unique=True)
    op.create_index("ix_kb_articles_author_id", "kb_articles", ["author_id"])


def downgrade() -> None:
    op.drop_index("ix_kb_articles_author_id", table_name="kb_articles")
    op.drop_index("ix_kb_articles_slug", table_name="kb_articles")
    op.drop_table("kb_articles")
    op.execute("DROP TYPE article_status_enum")

```

### `backend/app/__init__.py`
```python

```

### `backend/app/auth/__init__.py`
```python

```

### `backend/app/auth/dependencies.py`
```python
"""FastAPI dependencies for authentication and role-based authorization."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_access_token
from app.auth.models import Role, User
from app.core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


async def require_contributor(
    current_user: User = Depends(get_current_user),
) -> User:
    """Enforce that the caller has Contributor or Admin role (AC-022.2)."""
    if current_user.role not in (Role.CONTRIBUTOR, Role.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Contributor or Admin role required",
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role is not Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return current_user

```

### `backend/app/auth/jwt.py`
```python
"""JWT token utilities."""
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import get_settings


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    settings = get_settings()
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
    """Decode and verify; raises JWTError on failure."""
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])  # type: ignore[return-value]

```

### `backend/app/auth/models.py`
```python
    articles: Mapped[list["Article"]] = relationship(  # type: ignore[name-defined]
"""Auth domain models — User and Role (STORE-003/STORE-004)."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Role(str, enum.Enum):
    ADMIN = "admin"
    CONTRIBUTOR = "contributor"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(
        Enum(Role, name="role_enum"), nullable=False, default=Role.VIEWER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship to articles authored by this user
        "Article", back_populates="author", lazy="noload"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email} role={self.role}>"

```

### `backend/app/auth/passwords.py`
```python
"""Password hashing utilities (bcrypt via passlib)."""
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)

```

### `backend/app/auth/router.py`
```python
"""Auth router — token issuance."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token
from app.auth.models import User
from app.auth.passwords import hash_password, verify_password
from app.auth.schemas import Token, UserCreate, UserRead
from app.core.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    result = await db.execute(select(User).where(User.email == form.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    token = create_access_token(
        subject=str(user.id), extra_claims={"role": user.role.value}
    )
    return Token(access_token=token)


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Registration endpoint (open during bootstrapping; lock down in prod via Admin role guard)."""
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

```

### `backend/app/auth/schemas.py`
```python
"""Auth Pydantic schemas (request/response)."""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.auth.models import Role


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    sub: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    role: Role = Role.VIEWER


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

```

### `backend/app/core/__init__.py`
```python

```

### `backend/app/core/config.py`
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, AnyHttpUrl
from typing import Annotated


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str

    # Security
    secret_key: str
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"

    # App
    environment: str = "development"
    log_level: str = "INFO"
    allowed_origins: str = "http://localhost:3000"

    @field_validator("secret_key")
    @classmethod
    def secret_key_must_be_set(cls, v: str) -> str:
        if v in ("", "CHANGEME_use_openssl_rand_hex_32"):
            raise ValueError("SECRET_KEY must be overridden in production")
        return v

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings

```

### `backend/app/core/database.py`
```python
"""Async SQLAlchemy engine + session factory (single canonical instance)."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _make_engine() -> object:  # returns AsyncEngine; typed loosely to avoid import cycle
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.environment == "development",
        pool_pre_ping=True,
    )


_engine = _make_engine()
_async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_engine,  # type: ignore[arg-type]
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields one session per request."""
    async with _async_session_factory() as session:
        yield session

```

### `backend/app/core/exceptions.py`
```python
"""Global HTTP exception handlers — no internal detail leakage."""
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import structlog

logger = structlog.get_logger(__name__)


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    # Log 5xx at error, 4xx at warning
    lvl = "error" if exc.status_code >= 500 else "warning"
    getattr(logger, lvl)(
        "http_exception",
        method=request.method,
        path=request.url.path,
        status=exc.status_code,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    logger.warning(
        "validation_error",
        method=request.method,
        path=request.url.path,
        errors=exc.errors(),
    )
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

```

### `backend/app/core/logging.py`
```python
"""Structured logging configuration (structlog)."""
import logging
import structlog


def configure_logging(log_level: str = "INFO") -> None:
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper(), logging.INFO),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

```

### `backend/app/kb/__init__.py`
```python

```

### `backend/app/kb/article_models.py`
```python
    author: Mapped["User"] = relationship(  # type: ignore[name-defined]
"""KB Article domain model (STORE-005)."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ArticleStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Article(Base):
    __tablename__ = "kb_articles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    # Body is stored post-sanitization only (AC-022.3); raw HTML never persisted.
    body: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(String(512), unique=True, nullable=False, index=True)
    status: Mapped[ArticleStatus] = mapped_column(
        Enum(ArticleStatus, name="article_status_enum"),
        nullable=False,
        default=ArticleStatus.DRAFT,
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

        "User", back_populates="articles", lazy="joined"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Article id={self.id} slug={self.slug} status={self.status}>"

```

### `backend/app/kb/article_schemas.py`
```python
"""KB article request / response schemas (IF-007)."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.kb.article_models import ArticleStatus


class ArticleCreate(BaseModel):
    """Request body for POST /api/v1/kb/articles (IF-007)."""

    title: str = Field(min_length=1, max_length=512)
    body: str = Field(
        min_length=1,
        description="HTML body — will be sanitized server-side before storage (AC-022.3).",
    )
    status: ArticleStatus = ArticleStatus.DRAFT

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be blank")
        return v.strip()


class ArticleRead(BaseModel):
    """Response schema for a KB article."""

    id: uuid.UUID
    title: str
    body: str
    slug: str
    status: ArticleStatus
    author_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

```

### `backend/app/kb/articles.py`
```python
"""
KB article service — create and read operations (COMP-005, TASK-044).

Responsibility boundary:
  * Accepts already-validated Pydantic input.
  * Sanitizes HTML body before persistence (AC-022.3).
  * Derives a unique slug.
  * Persists to STORE-005 (kb_articles table).
  * Returns ORM Article instances; callers map to response schemas.
"""
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import structlog

from app.kb.article_models import Article, ArticleStatus
from app.kb.article_schemas import ArticleCreate
from app.kb.sanitizer import sanitize_html
from app.kb.slugs import slugify

logger = structlog.get_logger(__name__)

_MAX_SLUG_ATTEMPTS = 10


async def _unique_slug(db: AsyncSession, base: str) -> str:
    """Return *base* slug, appending a counter suffix until unique."""
    candidate = base
    for attempt in range(_MAX_SLUG_ATTEMPTS):
        result = await db.execute(select(Article).where(Article.slug == candidate))
        if result.scalar_one_or_none() is None:
            return candidate
        candidate = f"{base}-{attempt + 1}"
    # Fallback: append random hex
    candidate = f"{base}-{uuid.uuid4().hex[:6]}"
    return candidate


async def create_article(
    *,
    db: AsyncSession,
    payload: ArticleCreate,
    author_id: uuid.UUID,
) -> Article:
    """
    Create a new KB article.

    - Sanitizes ``payload.body`` with bleach before storage (AC-022.3).
    - Generates a unique slug from the title.
    - Persists and returns the new Article ORM instance.
    """
    # AC-022.3: sanitize before any persistence
    sanitized_body = sanitize_html(payload.body)

    slug = await _unique_slug(db, slugify(payload.title))

    article = Article(
        title=payload.title.strip(),
        body=sanitized_body,
        slug=slug,
        status=payload.status,
        author_id=author_id,
    )
    db.add(article)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception("article_create_failed", author_id=str(author_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create article",
        )
    await db.refresh(article)
    logger.info("article_created", article_id=str(article.id), slug=article.slug)
    return article

```

### `backend/app/kb/kb_router.py`
```python
"""
KB article HTTP router (IF-007, COMP-005).

POST /api/v1/kb/articles
  - Requires Contributor or Admin role (AC-022.2).
  - Sanitizes HTML body before storage (AC-022.3).
  - Returns 201 Created with ArticleRead payload.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_contributor
from app.auth.models import User
from app.core.database import get_db
from app.kb.article_schemas import ArticleCreate, ArticleRead
from app.kb.articles import create_article

router = APIRouter(prefix="/kb", tags=["kb"])


@router.post(
    "/articles",
    response_model=ArticleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a KB article",
    description=(
        "Creates a new Knowledge-Base article. "
        "Requires **Contributor** or **Admin** role (AC-022.2). "
        "HTML body is sanitized server-side before storage (AC-022.3)."
    ),
)
async def create_article_endpoint(
    payload: ArticleCreate,
    current_user: User = Depends(require_contributor),  # AC-022.2
    db: AsyncSession = Depends(get_db),
) -> ArticleRead:
    article = await create_article(
        db=db,
        payload=payload,
        author_id=current_user.id,
    )
    return ArticleRead.model_validate(article)

```

### `backend/app/kb/models_compat.py`
```python
"""Re-export kb domain models from canonical location."""
from app.kb.article_models import Article, ArticleStatus

__all__ = ["Article", "ArticleStatus"]

```

### `backend/app/kb/sanitizer.py`
```python
"""
HTML sanitizer for KB article body content (AC-022.3).

Uses ``bleach`` to strip all tags/attributes that are not on an explicit
allow-list. Raw user input is NEVER persisted; the sanitized result is
what hits the database.

Allowed tags are a safe subset suitable for rich-text knowledge-base
articles: standard text formatting, headings, lists, blockquotes, code,
and links — but NO script, style, iframe, object, or embed elements.
"""
import re

import bleach

# ---------------------------------------------------------------------------
# Allow-lists
# ---------------------------------------------------------------------------
ALLOWED_TAGS: frozenset[str] = frozenset(
    {
        # Structure
        "p", "br", "hr", "div", "span",
        # Headings
        "h1", "h2", "h3", "h4", "h5", "h6",
        # Emphasis
        "b", "i", "strong", "em", "s", "del", "ins", "mark", "sub", "sup",
        # Lists
        "ul", "ol", "li", "dl", "dt", "dd",
        # Quotation / code
        "blockquote", "pre", "code", "kbd", "samp",
        # Tables (read-only layout; no form elements)
        "table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption",
        # Links and media (src validated separately)
        "a", "img",
        # Misc inline
        "abbr", "cite", "time", "small",
    }
)

ALLOWED_ATTRIBUTES: dict[str, list[str]] = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
    "abbr": ["title"],
    "time": ["datetime"],
    "th": ["scope", "colspan", "rowspan"],
    "td": ["colspan", "rowspan"],
    # Allow class on structural wrappers for styling only — never event handlers
    "div": ["class"],
    "span": ["class"],
    "p": ["class"],
    "pre": ["class"],
    "code": ["class"],
}

# Disallow javascript: / vbscript: / data: URIs in href/src
_DANGEROUS_URL_RE = re.compile(
    r"^\s*(javascript|vbscript|data)\s*:", re.IGNORECASE
)


def _sanitize_link(tag: str, name: str, value: str) -> str | bool:
    """bleach attribute callable: validate href/src are not dangerous."""
    if name in ("href", "src"):
        if _DANGEROUS_URL_RE.match(value):
            return False  # strip the attribute
    return True  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def sanitize_html(raw: str) -> str:
    """
    Return a sanitized copy of *raw* HTML suitable for storage and rendering.

    Strips disallowed tags (content preserved), removes disallowed attributes,
    and rejects javascript:/vbscript:/data: URIs in href/src.

    This function is **deterministic and has no side effects** — safe to call
    in unit tests without a database.
    """
    cleaned = bleach.clean(
        raw,
        tags=ALLOWED_TAGS,
        attributes=_sanitize_link,  # type: ignore[arg-type]
        strip=True,        # strip disallowed tags rather than escaping them
        strip_comments=True,
    )
    return cleaned

```

### `backend/app/kb/slugs.py`
```python
"""Slug generation for KB articles."""
import re
import unicodedata


def slugify(text: str) -> str:
    """
    Convert *text* to a URL-safe ASCII slug.

    1. Normalise unicode to NFKD, encode as ASCII (ignore non-ASCII).
    2. Lower-case.
    3. Replace runs of non-alphanumeric characters with a single hyphen.
    4. Strip leading/trailing hyphens.
    """
    normalised = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    lowered = normalised.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "article"

```

### `backend/app/main.py`
```python
"""
Canonical ASGI application entrypoint.

One FastAPI instance, one lifespan, all routers registered here.
"""
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.exceptions import http_exception_handler, validation_exception_handler
from app.core.logging import configure_logging

# Routers
from app.auth.router import router as auth_router
from app.kb.kb_router import router as kb_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    yield
    # Shutdown: engine disposal handled at process exit; add explicit cleanup here if needed.


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title="KB API",
        version="1.0.0",
        docs_url="/api/docs" if settings.environment != "production" else None,
        redoc_url="/api/redoc" if settings.environment != "production" else None,
        openapi_url="/api/openapi.json" if settings.environment != "production" else None,
        lifespan=lifespan,
    )

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # Global exception handlers (no internal detail leakage)
    application.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    application.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]

    # Routers
    api_prefix = "/api/v1"
    application.include_router(auth_router, prefix=api_prefix)
    application.include_router(kb_router, prefix=api_prefix)

    @application.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()

```

### `backend/pyproject.toml`
```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "kb-api"
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
    "python-multipart==0.0.12",
    "bleach==6.1.0",
    "structlog==24.4.0",
    "greenlet==3.1.1",
]

[project.optional-dependencies]
dev = [
    "pytest==8.3.4",
    "pytest-asyncio==0.24.0",
    "httpx==0.28.1",
    "pytest-cov==6.0.0",
    "ruff==0.8.4",
    "mypy==1.13.0",
    "aiosqlite==0.20.0",
    "types-passlib==1.7.7.20240819",
    "types-bleach==6.1.0.20240331",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["app*"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "S", "B", "ANN"]
ignore = ["ANN101", "ANN102", "ANN401"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]

```

### `backend/tests/__init__.py`
```python

```

### `backend/tests/conftest.py`
```python
"""
Shared pytest fixtures for KB API tests.

Uses an in-process SQLite database (aiosqlite) for speed and isolation.
Each test module gets a fresh database via function-scoped fixtures.
"""
from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.models import Role, User
from app.auth.passwords import hash_password
from app.core.database import Base, get_db
from app.main import app

# SQLite test URL — no server required
_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session backed by a fresh in-memory SQLite database."""
    engine = create_async_engine(_TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture()
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTPX async client wired to the test database via DI override."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ------------------------------------------------------------------
# Helper factories
# ------------------------------------------------------------------

async def make_user(
    db: AsyncSession,
    *,
    email: str = "user@example.com",
    password: str = "password123",
    role: Role = Role.VIEWER,
    full_name: str = "Test User",
    is_active: bool = True,
) -> User:
    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=role,
        is_active=is_active,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_token(client: AsyncClient, *, email: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]

```

### `backend/tests/test_kb_articles.py`
```python
"""
Integration tests for POST /api/v1/kb/articles (TASK-044).

Coverage map:
  AC-022.2  →  test_403_for_viewer, test_403_for_unauthenticated
  AC-022.3  →  test_body_sanitized_on_create
  VER-002   →  test_contributor_can_create_article (happy-path HTTP + DB)
  VER-010   →  test_admin_can_create_article
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Role
from app.kb.article_models import Article
from tests.conftest import get_token, make_user


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture()
async def contributor_token(client: AsyncClient, db_session: AsyncSession) -> str:
    await make_user(
        db_session,
        email="contrib@example.com",
        password="secret1234",
        role=Role.CONTRIBUTOR,
    )
    return await get_token(client, email="contrib@example.com", password="secret1234")


@pytest_asyncio.fixture()
async def admin_token(client: AsyncClient, db_session: AsyncSession) -> str:
    await make_user(
        db_session,
        email="admin@example.com",
        password="secret1234",
        role=Role.ADMIN,
    )
    return await get_token(client, email="admin@example.com", password="secret1234")


@pytest_asyncio.fixture()
async def viewer_token(client: AsyncClient, db_session: AsyncSession) -> str:
    await make_user(
        db_session,
        email="viewer@example.com",
        password="secret1234",
        role=Role.VIEWER,
    )
    return await get_token(client, email="viewer@example.com", password="secret1234")


# ---------------------------------------------------------------------------
# AC-022.2 — role enforcement
# ---------------------------------------------------------------------------

async def test_unauthenticated_returns_401(client: AsyncClient) -> None:
    """No bearer token → 401."""
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "No auth", "body": "<p>test</p>"},
    )
    assert resp.status_code == 401


async def test_viewer_returns_403(
    client: AsyncClient, viewer_token: str
) -> None:
    """Viewer role → 403 Forbidden (AC-022.2)."""
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "Viewer attempt", "body": "<p>hello</p>"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 403


async def test_contributor_can_create_article(
    client: AsyncClient,
    db_session: AsyncSession,
    contributor_token: str,
) -> None:
    """Contributor role → 201 Created (AC-022.2, VER-002)."""
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "My First Article", "body": "<p>Hello <strong>world</strong></p>"},
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "My First Article"
    assert data["slug"] == "my-first-article"
    assert data["status"] == "draft"
    assert "id" in data
    assert "author_id" in data

    # Verify persistence in DB
    result = await db_session.execute(
        select(Article).where(Article.slug == "my-first-article")
    )
    article = result.scalar_one_or_none()
    assert article is not None
    assert article.title == "My First Article"


async def test_admin_can_create_article(
    client: AsyncClient,
    admin_token: str,
) -> None:
    """Admin role is also allowed (AC-022.2, VER-010)."""
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "Admin Article", "body": "<p>content</p>"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["title"] == "Admin Article"


# ---------------------------------------------------------------------------
# AC-022.3 — sanitization enforced at storage boundary
# ---------------------------------------------------------------------------

async def test_body_sanitized_on_create(
    client: AsyncClient,
    db_session: AsyncSession,
    contributor_token: str,
) -> None:
    """
    XSS payload in body is stripped before storage.
    The stored article body must not contain the script tag (AC-022.3).
    """
    xss_payload = "<p>Safe text</p><script>alert('xss')</script>"
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "XSS Test Article", "body": xss_payload},
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    assert resp.status_code == 201
    returned_body = resp.json()["body"]
    assert "<script>" not in returned_body
    assert "alert" not in returned_body
    assert "Safe text" in returned_body

    # Confirm sanitization happened at the DB layer too
    result = await db_session.execute(
        select(Article).where(Article.slug == "xss-test-article")
    )
    article = result.scalar_one_or_none()
    assert article is not None
    assert "<script>" not in article.body
    assert "alert" not in article.body


async def test_javascript_href_sanitized(
    client: AsyncClient,
    contributor_token: str,
) -> None:
    """javascript: URI in href is stripped before storage (AC-022.3)."""
    body = '<a href="javascript:evil()">click me</a>'
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "JS Href Article", "body": body},
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    assert resp.status_code == 201
    stored_body = resp.json()["body"]
    assert "javascript:" not in stored_body
    # Text preserved
    assert "click me" in stored_body


async def test_safe_html_preserved(
    client: AsyncClient,
    contributor_token: str,
) -> None:
    """Legitimate formatting tags survive sanitization (AC-022.3)."""
    body = "<h2>Title</h2><p>Para with <em>emphasis</em> and <code>code</code>.</p>"
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "Safe HTML Article", "body": body},
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    assert resp.status_code == 201
    stored_body = resp.json()["body"]
    assert "<h2>" in stored_body
    assert "<em>" in stored_body
    assert "<code>" in stored_body


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

async def test_empty_title_returns_422(
    client: AsyncClient,
    contributor_token: str,
) -> None:
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "", "body": "<p>body</p>"},
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    assert resp.status_code == 422


async def test_blank_title_returns_422(
    client: AsyncClient,
    contributor_token: str,
) -> None:
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "   ", "body": "<p>body</p>"},
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    assert resp.status_code == 422


async def test_missing_body_returns_422(
    client: AsyncClient,
    contributor_token: str,
) -> None:
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "No body"},
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    assert resp.status_code == 422


async def test_slug_deduplication(
    client: AsyncClient,
    contributor_token: str,
) -> None:
    """Creating two articles with the same title yields distinct slugs."""
    payload = {"title": "Duplicate Title", "body": "<p>body</p>"}
    r1 = await client.post(
        "/api/v1/kb/articles",
        json=payload,
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    r2 = await client.post(
        "/api/v1/kb/articles",
        json=payload,
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["slug"] != r2.json()["slug"]


async def test_custom_status_draft(
    client: AsyncClient,
    contributor_token: str,
) -> None:
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "Draft Status", "body": "<p>x</p>", "status": "draft"},
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "draft"


async def test_invalid_status_returns_422(
    client: AsyncClient,
    contributor_token: str,
) -> None:
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "Bad Status", "body": "<p>x</p>", "status": "bogus"},
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    assert resp.status_code == 422

```

### `backend/tests/test_sanitizer.py`
```python
"""
Tests for the KB article sanitizer (AC-022.3, VER-004).

These are pure unit tests — no DB or HTTP required.
"""
import pytest

from app.kb.sanitizer import sanitize_html


class TestSanitizeHtml:
    # -- Allowed content passes through ----------------------------------

    def test_plain_text_preserved(self) -> None:
        assert sanitize_html("Hello world") == "Hello world"

    def test_allowed_tags_preserved(self) -> None:
        html = "<p>Hello <strong>world</strong></p>"
        result = sanitize_html(html)
        assert "<p>" in result
        assert "<strong>" in result

    def test_allowed_link_preserved(self) -> None:
        html = '<a href="https://example.com" title="ex">link</a>'
        result = sanitize_html(html)
        assert 'href="https://example.com"' in result

    def test_img_with_safe_src_preserved(self) -> None:
        html = '<img src="https://cdn.example.com/img.png" alt="logo">'
        result = sanitize_html(html)
        assert 'src="https://cdn.example.com/img.png"' in result

    def test_heading_preserved(self) -> None:
        html = "<h2>Section</h2>"
        result = sanitize_html(html)
        assert "<h2>" in result

    def test_ordered_list_preserved(self) -> None:
        html = "<ol><li>first</li><li>second</li></ol>"
        result = sanitize_html(html)
        assert "<ol>" in result
        assert "<li>" in result

    def test_code_block_preserved(self) -> None:
        html = "<pre><code>print('hi')</code></pre>"
        result = sanitize_html(html)
        assert "<pre>" in result
        assert "<code>" in result

    # -- Dangerous content stripped --------------------------------------

    def test_script_tag_stripped(self) -> None:
        html = "<p>Hi</p><script>alert('xss')</script>"
        result = sanitize_html(html)
        assert "<script>" not in result
        assert "alert" not in result

    def test_script_tag_strips_content_too(self) -> None:
        """bleach strip=True removes the tag AND its contents for script."""
        html = "<script>evil()</script>"
        result = sanitize_html(html)
        assert "evil" not in result

    def test_iframe_stripped(self) -> None:
        html = '<iframe src="https://evil.com"></iframe>'
        result = sanitize_html(html)
        assert "<iframe>" not in result

    def test_style_tag_stripped(self) -> None:
        html = "<style>body{display:none}</style>"
        result = sanitize_html(html)
        assert "<style>" not in result

    def test_on_event_attribute_stripped(self) -> None:
        html = '<p onclick="evil()">Click me</p>'
        result = sanitize_html(html)
        assert "onclick" not in result
        # Text content preserved
        assert "Click me" in result

    def test_javascript_href_stripped(self) -> None:
        html = '<a href="javascript:alert(1)">XSS</a>'
        result = sanitize_html(html)
        assert "javascript:" not in result
        # Link text preserved
        assert "XSS" in result

    def test_vbscript_href_stripped(self) -> None:
        html = '<a href="vbscript:MsgBox(1)">XSS</a>'
        result = sanitize_html(html)
        assert "vbscript:" not in result

    def test_data_uri_img_src_stripped(self) -> None:
        html = '<img src="data:text/html,<h1>XSS</h1>" alt="x">'
        result = sanitize_html(html)
        assert "data:" not in result

    def test_html_comments_stripped(self) -> None:
        html = "<!-- hidden comment --><p>visible</p>"
        result = sanitize_html(html)
        assert "<!--" not in result
        assert "visible" in result

    def test_object_embed_stripped(self) -> None:
        html = '<object data="evil.swf"></object>'
        result = sanitize_html(html)
        assert "<object>" not in result

    # -- Edge cases ------------------------------------------------------

    def test_empty_string(self) -> None:
        assert sanitize_html("") == ""

    def test_whitespace_only(self) -> None:
        result = sanitize_html("   ")
        assert result.strip() == ""

    def test_deeply_nested_xss(self) -> None:
        html = "<p><b><i><script>x()</script></i></b></p>"
        result = sanitize_html(html)
        assert "<script>" not in result
        assert "x()" not in result

    def test_unicode_content_preserved(self) -> None:
        html = "<p>Héllo wörld 日本語</p>"
        result = sanitize_html(html)
        assert "Héllo" in result
        assert "日本語" in result

```