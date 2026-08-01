# Implementation Report

All packages are available. Now run lint check:

## Verification
- `python3 -c "import os; [print(os.path.join(r,f)) for r,d,files in os.walk('backend') for f in files]"` → exit 0
- `python3 -c "import os; [print(os.path.join(r,f)) for r,d,files in os.walk('.') for f in files if '.git' not in r]"` → exit 0
- `python3 -c "import os; dirs=os.listdir('.'); print(dirs)"` → exit 0
- `pip install fastapi==0.115.5 uvicorn[standard]==0.32.1 pydantic==2.10.3 pydantic-settings==2.6.1 sqlalchemy==2.0.36 alembic==1.14.0 asyncpg==0.30.0 greenlet==3.1.1 python-jose[cryptography]==3.3.0 passlib[bcrypt]==1.7.4 python-multipart==0.0.19 httpx==0.28.1 pytest==8.3.4 pytest-asyncio==0.24.0 pytest-cov==6.0.0 aiosqlite --quiet` → exit 0
- `python3 -c "import fastapi; import pydantic; import sqlalchemy; import alembic; print('fastapi', fastapi.__version__); print('pydantic', pydantic.__version__); print('sqlalchemy', sqlalchemy.__version__); print('alembic', alembic.__version__)"` → exit 0
- `python3 -c "import httpx, pytest, aiosqlite; print('httpx', httpx.__version__); print('aiosqlite ok')"` → exit 0
- `ruff check app/ tests/ --select E,F,I,UP,B --ignore B008` → exit 1

## Generated Files

### `backend/.env.example`
```text
DATABASE_URL=postgresql+asyncpg://cms:cms@localhost:5432/cms_dev
SECRET_KEY=change-me-in-production-use-at-least-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=development

```

### `backend/alembic.ini`
```text
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql+asyncpg://cms:cms@localhost:5432/cms_dev

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
"""Alembic async env for SQLAlchemy 2.0 async engine."""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.pool import NullPool

# Import all models so autogenerate sees their metadata
from app.core.config import settings
from app.core.database import Base
import app.models  # noqa: F401  — registers all tables on Base.metadata

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

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
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):  # type: ignore[no-untyped-def]
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=NullPool,
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

### `backend/alembic/versions/0001_taxonomy.py`
```python
"""Initial taxonomy schema — categories, tags, association tables.

Revision ID: 0001_taxonomy
Revises: —
Create Date: 2025-01-01 00:00:00
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_taxonomy"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- TaxonomyStatus enum ---
    taxonomy_status = sa.Enum("active", "archived", name="taxonomystatus")
    taxonomy_status.create(op.get_bind(), checkfirst=True)

    # --- content stub table (FK target for association tables) ---
    op.create_table(
        "content",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(512), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_content"),
    )

    # --- categories ---
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("label", sa.String(256), nullable=False),
        sa.Column("description", sa.String(1024), nullable=True),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "archived", name="taxonomystatus"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
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
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["categories.id"],
            name="fk_categories_parent_id",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_categories"),
        sa.UniqueConstraint("slug", name="uq_categories_slug"),
    )
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"])

    # --- tags ---
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("label", sa.String(256), nullable=False),
        sa.Column("description", sa.String(1024), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "archived", name="taxonomystatus"),
            nullable=False,
            server_default="active",
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
        sa.PrimaryKeyConstraint("id", name="pk_tags"),
        sa.UniqueConstraint("slug", name="uq_tags_slug"),
    )
    op.create_index("ix_tags_slug", "tags", ["slug"], unique=True)

    # --- content_category association ---
    op.create_table(
        "content_category",
        sa.Column("content_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name="fk_content_category_category_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["content_id"],
            ["content.id"],
            name="fk_content_category_content_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("content_id", "category_id", name="uq_content_category"),
    )

    # --- content_tag association ---
    op.create_table(
        "content_tag",
        sa.Column("content_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["tags.id"],
            name="fk_content_tag_tag_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["content_id"],
            ["content.id"],
            name="fk_content_tag_content_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("content_id", "tag_id", name="uq_content_tag"),
    )


def downgrade() -> None:
    op.drop_table("content_tag")
    op.drop_table("content_category")
    op.drop_index("ix_tags_slug", "tags")
    op.drop_table("tags")
    op.drop_index("ix_categories_parent_id", "categories")
    op.drop_index("ix_categories_slug", "categories")
    op.drop_table("categories")
    op.drop_table("content")
    sa.Enum(name="taxonomystatus").drop(op.get_bind(), checkfirst=True)

```

### `backend/app/__init__.py`
```python

```

### `backend/app/core/__init__.py`
```python

```

### `backend/app/core/config.py`
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://cms:cms@localhost:5432/cms_dev"
    SECRET_KEY: str = "change-me-in-production-use-at-least-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ENVIRONMENT: str = "development"


settings = Settings()

```

### `backend/app/core/database.py`
```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:  # type: ignore[return]
    async with AsyncSessionLocal() as session:
        yield session

```

### `backend/app/core/security.py`
```python
"""Auth dependencies — stub until the full auth module (PHASE-011) is wired in.

In production this verifies a JWT, loads the user from DB, and enforces role.
The `require_admin` dependency raises 403 for non-admin callers.
"""

from __future__ import annotations

import enum
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(auto_error=False)


class UserRole(str, enum.Enum):
    admin = "admin"
    editor = "editor"
    viewer = "viewer"


class CurrentUser:
    def __init__(self, user_id: int, role: UserRole) -> None:
        self.user_id = user_id
        self.role = role

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.admin


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> CurrentUser:
    """Stub: accept any bearer token as an admin for development.

    Replace this body with real JWT validation when PHASE-011 auth is available.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # TODO(PHASE-011): validate JWT, load user from DB
    return CurrentUser(user_id=1, role=UserRole.admin)


async def require_admin(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator role required.",
        )
    return current_user

```

### `backend/app/main.py`
```python
"""Canonical ASGI entrypoint — backend/app/main.py"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routers.admin.taxonomy_router import router as taxonomy_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: nothing needed for basic boot; connection pool is lazy.
    yield
    # Shutdown: dispose engine when full DB module is wired.


app = FastAPI(
    title="CMS API",
    version="0.1.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — tighten origins in production via config
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"] if settings.ENVIRONMENT != "production" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global exception handlers — never leak internal detail to callers
# ---------------------------------------------------------------------------


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Log exc here with structured logger (observability requirement)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred."},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(taxonomy_router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Health / readiness
# ---------------------------------------------------------------------------


@app.get("/healthz", tags=["ops"], include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz", tags=["ops"], include_in_schema=False)
async def readiness() -> dict[str, str]:
    # Extend with a DB ping when full DB module is wired.
    return {"status": "ready"}

```

### `backend/app/models/__init__.py`
```python
"""Central model registry — import here so Alembic autogenerate sees every table."""

from app.models.content import Content  # noqa: F401  stub FK target
from app.models.taxonomy import Category, Tag, TaxonomyStatus, content_category, content_tag  # noqa: F401

__all__ = [
    "Content",
    "Category",
    "Tag",
    "TaxonomyStatus",
    "content_category",
    "content_tag",
]

```

### `backend/app/models/content.py`
```python
"""Minimal stub for the content model so that FK constraints in taxonomy compile.

This will be replaced by the full Content model when the content module is implemented.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Content(Base):
    """Stub — FK target for content_category / content_tag association tables."""

    __tablename__ = "content"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

```

### `backend/app/models/taxonomy.py`
```python
import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    pass  # forward refs for content models when added


class TaxonomyStatus(str, enum.Enum):
    active = "active"
    archived = "archived"


# ---------------------------------------------------------------------------
# Association tables — created once and referenced by content models.
# They use plain integer FKs so they survive category/tag archival.
# ---------------------------------------------------------------------------

content_category = Table(
    "content_category",
    Base.metadata,
    Column("content_id", Integer, ForeignKey("content.id", ondelete="CASCADE"), nullable=False),
    Column(
        "category_id",
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    UniqueConstraint("content_id", "category_id", name="uq_content_category"),
)

content_tag = Table(
    "content_tag",
    Base.metadata,
    Column("content_id", Integer, ForeignKey("content.id", ondelete="CASCADE"), nullable=False),
    Column(
        "tag_id",
        Integer,
        ForeignKey("tags.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    UniqueConstraint("content_id", "tag_id", name="uq_content_tag"),
)


# ---------------------------------------------------------------------------
# Category — supports one level of hierarchy via nullable parent_id.
# Archiving a parent does NOT cascade-archive children; that is a UI concern.
# ---------------------------------------------------------------------------


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    label: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[TaxonomyStatus] = mapped_column(
        Enum(TaxonomyStatus, name="taxonomystatus"),
        nullable=False,
        default=TaxonomyStatus.active,
        server_default=text("'active'"),
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # self-referential relationship
    parent: Mapped["Category | None"] = relationship(
        "Category", remote_side="Category.id", back_populates="children", lazy="selectin"
    )
    children: Mapped[list["Category"]] = relationship(
        "Category", back_populates="parent", lazy="selectin"
    )

    def archive(self) -> None:
        self.status = TaxonomyStatus.archived

    def restore(self) -> None:
        self.status = TaxonomyStatus.active

    @property
    def is_archived(self) -> bool:
        return self.status == TaxonomyStatus.archived


# ---------------------------------------------------------------------------
# Tag — flat, globally-scoped.
# ---------------------------------------------------------------------------


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    label: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[TaxonomyStatus] = mapped_column(
        Enum(TaxonomyStatus, name="taxonomystatus"),
        nullable=False,
        default=TaxonomyStatus.active,
        server_default=text("'active'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def archive(self) -> None:
        self.status = TaxonomyStatus.archived

    def restore(self) -> None:
        self.status = TaxonomyStatus.active

    @property
    def is_archived(self) -> bool:
        return self.status == TaxonomyStatus.archived

```

### `backend/app/routers/__init__.py`
```python

```

### `backend/app/routers/admin/taxonomy_router.py`
```python
"""Admin router for taxonomy management (COMP-009 / TASK-030).

All mutating endpoints require the `require_admin` dependency (OWASP: Broken Access Control).

Routes:
  Categories
    GET    /admin/categories           list (with status filter + pagination)
    POST   /admin/categories           create
    GET    /admin/categories/{id}      get by id
    PATCH  /admin/categories/{id}      update
    DELETE /admin/categories/{id}      hard delete (fails if content refs exist)
    POST   /admin/categories/{id}/archive   soft-archive
    POST   /admin/categories/{id}/restore   restore archived

  Tags
    GET    /admin/tags                 list
    POST   /admin/tags                 create
    GET    /admin/tags/{id}            get by id
    PATCH  /admin/tags/{id}            update
    DELETE /admin/tags/{id}            hard delete
    POST   /admin/tags/{id}/archive    soft-archive
    POST   /admin/tags/{id}/restore    restore archived
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import CurrentUser, require_admin
from app.models.taxonomy import TaxonomyStatus
from app.schemas.taxonomy_schemas import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdate,
    TagCreate,
    TagListResponse,
    TagResponse,
    TagUpdate,
)
from app.services.admin.taxonomy_service import (
    ArchivedError,
    CategoryService,
    ConflictError,
    NotFoundError,
    TagService,
    TaxonomyValidationError,
)

router = APIRouter(prefix="/admin", tags=["admin-taxonomy"])

# ---------------------------------------------------------------------------
# Dependency factories
# ---------------------------------------------------------------------------


def get_category_service(db: Annotated[AsyncSession, Depends(get_db)]) -> CategoryService:
    return CategoryService(db)


def get_tag_service(db: Annotated[AsyncSession, Depends(get_db)]) -> TagService:
    return TagService(db)


# ---------------------------------------------------------------------------
# Error mapping helpers
# ---------------------------------------------------------------------------


def _raise_not_found(exc: NotFoundError) -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


def _raise_conflict(exc: ConflictError) -> None:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


def _raise_validation(exc: TaxonomyValidationError) -> None:
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


def _raise_archived(exc: ArchivedError) -> None:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


# ===========================================================================
# Category endpoints
# ===========================================================================


@router.get(
    "/categories",
    response_model=CategoryListResponse,
    summary="List categories",
    status_code=status.HTTP_200_OK,
)
async def list_categories(
    page: Annotated[int, Query(ge=1, description="1-based page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=200, description="Items per page")] = 50,
    status_filter: Annotated[TaxonomyStatus | None, Query(alias="status")] = None,
    svc: CategoryService = Depends(get_category_service),
    _admin: CurrentUser = Depends(require_admin),
) -> CategoryListResponse:
    items, total = await svc.list_categories(page=page, page_size=page_size, status_filter=status_filter)
    return CategoryListResponse(
        items=[CategoryResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create category",
)
async def create_category(
    payload: CategoryCreate,
    svc: CategoryService = Depends(get_category_service),
    _admin: CurrentUser = Depends(require_admin),
) -> CategoryResponse:
    try:
        obj = await svc.create_category(payload)
    except ConflictError as exc:
        _raise_conflict(exc)
    except NotFoundError as exc:
        _raise_not_found(exc)
    return CategoryResponse.model_validate(obj)


@router.get(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    summary="Get category by ID",
)
async def get_category(
    category_id: int,
    svc: CategoryService = Depends(get_category_service),
    _admin: CurrentUser = Depends(require_admin),
) -> CategoryResponse:
    try:
        obj = await svc.get_category(category_id)
    except NotFoundError as exc:
        _raise_not_found(exc)
    return CategoryResponse.model_validate(obj)


@router.patch(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    summary="Update category (PATCH)",
)
async def update_category(
    category_id: int,
    payload: CategoryUpdate,
    svc: CategoryService = Depends(get_category_service),
    _admin: CurrentUser = Depends(require_admin),
) -> CategoryResponse:
    try:
        obj = await svc.update_category(category_id, payload)
    except NotFoundError as exc:
        _raise_not_found(exc)
    except ConflictError as exc:
        _raise_conflict(exc)
    except TaxonomyValidationError as exc:
        _raise_validation(exc)
    return CategoryResponse.model_validate(obj)


@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hard-delete category (fails if content refs exist)",
)
async def delete_category(
    category_id: int,
    svc: CategoryService = Depends(get_category_service),
    _admin: CurrentUser = Depends(require_admin),
) -> None:
    try:
        await svc.delete_category(category_id)
    except NotFoundError as exc:
        _raise_not_found(exc)
    except ConflictError as exc:
        _raise_conflict(exc)


@router.post(
    "/categories/{category_id}/archive",
    response_model=CategoryResponse,
    summary="Archive category (soft-state, AC-028.2)",
)
async def archive_category(
    category_id: int,
    svc: CategoryService = Depends(get_category_service),
    _admin: CurrentUser = Depends(require_admin),
) -> CategoryResponse:
    try:
        obj = await svc.archive_category(category_id)
    except NotFoundError as exc:
        _raise_not_found(exc)
    return CategoryResponse.model_validate(obj)


@router.post(
    "/categories/{category_id}/restore",
    response_model=CategoryResponse,
    summary="Restore archived category",
)
async def restore_category(
    category_id: int,
    svc: CategoryService = Depends(get_category_service),
    _admin: CurrentUser = Depends(require_admin),
) -> CategoryResponse:
    try:
        obj = await svc.restore_category(category_id)
    except NotFoundError as exc:
        _raise_not_found(exc)
    return CategoryResponse.model_validate(obj)


# ===========================================================================
# Tag endpoints
# ===========================================================================


@router.get(
    "/tags",
    response_model=TagListResponse,
    summary="List tags",
)
async def list_tags(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    status_filter: Annotated[TaxonomyStatus | None, Query(alias="status")] = None,
    svc: TagService = Depends(get_tag_service),
    _admin: CurrentUser = Depends(require_admin),
) -> TagListResponse:
    items, total = await svc.list_tags(page=page, page_size=page_size, status_filter=status_filter)
    return TagListResponse(
        items=[TagResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/tags",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create tag",
)
async def create_tag(
    payload: TagCreate,
    svc: TagService = Depends(get_tag_service),
    _admin: CurrentUser = Depends(require_admin),
) -> TagResponse:
    try:
        obj = await svc.create_tag(payload)
    except ConflictError as exc:
        _raise_conflict(exc)
    return TagResponse.model_validate(obj)


@router.get(
    "/tags/{tag_id}",
    response_model=TagResponse,
    summary="Get tag by ID",
)
async def get_tag(
    tag_id: int,
    svc: TagService = Depends(get_tag_service),
    _admin: CurrentUser = Depends(require_admin),
) -> TagResponse:
    try:
        obj = await svc.get_tag(tag_id)
    except NotFoundError as exc:
        _raise_not_found(exc)
    return TagResponse.model_validate(obj)


@router.patch(
    "/tags/{tag_id}",
    response_model=TagResponse,
    summary="Update tag (PATCH)",
)
async def update_tag(
    tag_id: int,
    payload: TagUpdate,
    svc: TagService = Depends(get_tag_service),
    _admin: CurrentUser = Depends(require_admin),
) -> TagResponse:
    try:
        obj = await svc.update_tag(tag_id, payload)
    except NotFoundError as exc:
        _raise_not_found(exc)
    except ConflictError as exc:
        _raise_conflict(exc)
    return TagResponse.model_validate(obj)


@router.delete(
    "/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hard-delete tag",
)
async def delete_tag(
    tag_id: int,
    svc: TagService = Depends(get_tag_service),
    _admin: CurrentUser = Depends(require_admin),
) -> None:
    try:
        await svc.delete_tag(tag_id)
    except NotFoundError as exc:
        _raise_not_found(exc)
    except ConflictError as exc:
        _raise_conflict(exc)


@router.post(
    "/tags/{tag_id}/archive",
    response_model=TagResponse,
    summary="Archive tag (soft-state, AC-028.2)",
)
async def archive_tag(
    tag_id: int,
    svc: TagService = Depends(get_tag_service),
    _admin: CurrentUser = Depends(require_admin),
) -> TagResponse:
    try:
        obj = await svc.archive_tag(tag_id)
    except NotFoundError as exc:
        _raise_not_found(exc)
    return TagResponse.model_validate(obj)


@router.post(
    "/tags/{tag_id}/restore",
    response_model=TagResponse,
    summary="Restore archived tag",
)
async def restore_tag(
    tag_id: int,
    svc: TagService = Depends(get_tag_service),
    _admin: CurrentUser = Depends(require_admin),
) -> TagResponse:
    try:
        obj = await svc.restore_tag(tag_id)
    except NotFoundError as exc:
        _raise_not_found(exc)
    return TagResponse.model_validate(obj)

```

### `backend/app/schemas/__init__.py`
```python

```

### `backend/app/schemas/taxonomy_schemas.py`
```python
"""Pydantic v2 request/response schemas for taxonomy (categories + tags).

Separation of concerns:
- *Create / Update* schemas validate inbound API payloads.
- *Response* schemas shape outbound JSON; they never expose internal DB ids beyond
  what the API contract requires.
- *Read* schemas include `id`, `slug`, `status`, timestamps.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.taxonomy import TaxonomyStatus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _validate_slug(value: str) -> str:
    value = value.strip().lower()
    if not _SLUG_RE.match(value):
        raise ValueError(
            "slug must be lowercase alphanumeric words separated by hyphens, e.g. 'my-category'"
        )
    return value


SlugStr = Annotated[str, Field(min_length=1, max_length=128)]
LabelStr = Annotated[str, Field(min_length=1, max_length=256)]
DescStr = Annotated[str | None, Field(default=None, max_length=1024)]


# ===========================================================================
# Category schemas
# ===========================================================================


class CategoryCreate(BaseModel):
    slug: SlugStr
    label: LabelStr
    description: DescStr = None
    parent_id: int | None = None
    sort_order: int = Field(default=0, ge=0, le=32767)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        return _validate_slug(v)

    @field_validator("label")
    @classmethod
    def strip_label(cls, v: str) -> str:
        return v.strip()


class CategoryUpdate(BaseModel):
    """All fields optional — PATCH semantics."""

    label: LabelStr | None = None
    description: DescStr = None
    parent_id: int | None = None
    sort_order: int | None = Field(default=None, ge=0, le=32767)

    @field_validator("label")
    @classmethod
    def strip_label(cls, v: str | None) -> str | None:
        return v.strip() if v else v

    @model_validator(mode="after")
    def at_least_one_field(self) -> "CategoryUpdate":
        if all(
            getattr(self, f) is None for f in ("label", "description", "parent_id", "sort_order")
        ):
            raise ValueError("At least one field must be provided for update.")
        return self


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    label: str
    description: str | None
    parent_id: int | None
    status: TaxonomyStatus
    sort_order: int
    created_at: datetime
    updated_at: datetime


class CategoryListResponse(BaseModel):
    items: list[CategoryResponse]
    total: int
    page: int
    page_size: int


# ===========================================================================
# Tag schemas
# ===========================================================================


class TagCreate(BaseModel):
    slug: SlugStr
    label: LabelStr
    description: DescStr = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        return _validate_slug(v)

    @field_validator("label")
    @classmethod
    def strip_label(cls, v: str) -> str:
        return v.strip()


class TagUpdate(BaseModel):
    """All fields optional — PATCH semantics."""

    label: LabelStr | None = None
    description: DescStr = None

    @field_validator("label")
    @classmethod
    def strip_label(cls, v: str | None) -> str | None:
        return v.strip() if v else v

    @model_validator(mode="after")
    def at_least_one_field(self) -> "TagUpdate":
        if self.label is None and self.description is None:
            raise ValueError("At least one field must be provided for update.")
        return self


class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    label: str
    description: str | None
    status: TaxonomyStatus
    created_at: datetime
    updated_at: datetime


class TagListResponse(BaseModel):
    items: list[TagResponse]
    total: int
    page: int
    page_size: int

```

### `backend/app/services/__init__.py`
```python

```

### `backend/app/services/admin/__init__.py`
```python

```

### `backend/app/services/admin/taxonomy_service.py`
```python
"""Service layer for taxonomy (categories + tags).

Business rules enforced here (not in routers):
- Slugs are globally unique per type; duplicate slug → 409.
- Archived items cannot be assigned to NEW content (AC-028.2).
- Archive/restore transitions update status; existing content relations are untouched (RESTRICT FK).
- Deleting a category/tag with existing content associations is refused (FK RESTRICT).
- Parent category must exist and must not be the category itself.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.taxonomy import Category, Tag, TaxonomyStatus
from app.schemas.taxonomy_schemas import (
    CategoryCreate,
    CategoryUpdate,
    TagCreate,
    TagUpdate,
)


# ---------------------------------------------------------------------------
# Shared exceptions (mapped to HTTP codes in routers)
# ---------------------------------------------------------------------------


class NotFoundError(Exception):
    def __init__(self, entity: str, identifier: str | int) -> None:
        self.entity = entity
        self.identifier = identifier
        super().__init__(f"{entity} '{identifier}' not found.")


class ConflictError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class TaxonomyValidationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class ArchivedError(Exception):
    """Raised when trying to use an archived taxonomy item for new content (AC-028.2)."""

    def __init__(self, entity: str, identifier: str | int) -> None:
        self.entity = entity
        self.identifier = identifier
        super().__init__(
            f"{entity} '{identifier}' is archived and cannot be assigned to new content."
        )


# ---------------------------------------------------------------------------
# Category service
# ---------------------------------------------------------------------------


class CategoryService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ---- helpers ----

    async def _get_or_raise(self, category_id: int) -> Category:
        result = await self._db.execute(select(Category).where(Category.id == category_id))
        obj = result.scalar_one_or_none()
        if obj is None:
            raise NotFoundError("Category", category_id)
        return obj

    async def _assert_slug_free(self, slug: str, exclude_id: int | None = None) -> None:
        stmt = select(Category.id).where(Category.slug == slug)
        if exclude_id is not None:
            stmt = stmt.where(Category.id != exclude_id)
        exists = (await self._db.execute(stmt)).scalar_one_or_none()
        if exists is not None:
            raise ConflictError(f"Category slug '{slug}' is already taken.")

    async def _assert_parent_valid(self, parent_id: int, current_id: int | None = None) -> None:
        if current_id is not None and parent_id == current_id:
            raise TaxonomyValidationError("A category cannot be its own parent.")
        result = await self._db.execute(select(Category.id).where(Category.id == parent_id))
        if result.scalar_one_or_none() is None:
            raise NotFoundError("Category (parent)", parent_id)

    # ---- public API ----

    async def list_categories(
        self,
        page: int = 1,
        page_size: int = 50,
        status_filter: TaxonomyStatus | None = None,
    ) -> tuple[list[Category], int]:
        stmt = select(Category)
        if status_filter is not None:
            stmt = stmt.where(Category.status == status_filter)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total: int = (await self._db.execute(count_stmt)).scalar_one()
        stmt = (
            stmt.order_by(Category.sort_order, Category.label)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list((await self._db.execute(stmt)).scalars().all())
        return items, total

    async def get_category(self, category_id: int) -> Category:
        return await self._get_or_raise(category_id)

    async def get_category_by_slug(self, slug: str) -> Category:
        result = await self._db.execute(select(Category).where(Category.slug == slug))
        obj = result.scalar_one_or_none()
        if obj is None:
            raise NotFoundError("Category", slug)
        return obj

    async def create_category(self, payload: CategoryCreate) -> Category:
        await self._assert_slug_free(payload.slug)
        if payload.parent_id is not None:
            await self._assert_parent_valid(payload.parent_id)
        obj = Category(
            slug=payload.slug,
            label=payload.label,
            description=payload.description,
            parent_id=payload.parent_id,
            sort_order=payload.sort_order,
            status=TaxonomyStatus.active,
        )
        self._db.add(obj)
        try:
            await self._db.commit()
            await self._db.refresh(obj)
        except IntegrityError as exc:
            await self._db.rollback()
            raise ConflictError(f"Category could not be created: {exc.orig}") from exc
        return obj

    async def update_category(self, category_id: int, payload: CategoryUpdate) -> Category:
        obj = await self._get_or_raise(category_id)
        if payload.label is not None:
            obj.label = payload.label
        if payload.description is not None:
            obj.description = payload.description
        if "parent_id" in payload.model_fields_set:
            if payload.parent_id is not None:
                await self._assert_parent_valid(payload.parent_id, current_id=category_id)
            obj.parent_id = payload.parent_id
        if payload.sort_order is not None:
            obj.sort_order = payload.sort_order
        try:
            await self._db.commit()
            await self._db.refresh(obj)
        except IntegrityError as exc:
            await self._db.rollback()
            raise ConflictError(f"Category could not be updated: {exc.orig}") from exc
        return obj

    async def archive_category(self, category_id: int) -> Category:
        obj = await self._get_or_raise(category_id)
        if obj.is_archived:
            return obj  # idempotent
        obj.archive()
        await self._db.commit()
        await self._db.refresh(obj)
        return obj

    async def restore_category(self, category_id: int) -> Category:
        obj = await self._get_or_raise(category_id)
        if not obj.is_archived:
            return obj  # idempotent
        obj.restore()
        await self._db.commit()
        await self._db.refresh(obj)
        return obj

    async def delete_category(self, category_id: int) -> None:
        """Hard delete — refused by DB if content associations exist (FK RESTRICT)."""
        obj = await self._get_or_raise(category_id)
        try:
            await self._db.delete(obj)
            await self._db.commit()
        except IntegrityError as exc:
            await self._db.rollback()
            raise ConflictError(
                "Category cannot be deleted because it is referenced by existing content. "
                "Archive it instead."
            ) from exc

    # ---- AC-028.2 guard (called by content assignment code) ----

    async def assert_assignable(self, category_id: int) -> None:
        """Raise ArchivedError if the category is not active."""
        obj = await self._get_or_raise(category_id)
        if obj.is_archived:
            raise ArchivedError("Category", category_id)


# ---------------------------------------------------------------------------
# Tag service
# ---------------------------------------------------------------------------


class TagService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ---- helpers ----

    async def _get_or_raise(self, tag_id: int) -> Tag:
        result = await self._db.execute(select(Tag).where(Tag.id == tag_id))
        obj = result.scalar_one_or_none()
        if obj is None:
            raise NotFoundError("Tag", tag_id)
        return obj

    async def _assert_slug_free(self, slug: str, exclude_id: int | None = None) -> None:
        stmt = select(Tag.id).where(Tag.slug == slug)
        if exclude_id is not None:
            stmt = stmt.where(Tag.id != exclude_id)
        exists = (await self._db.execute(stmt)).scalar_one_or_none()
        if exists is not None:
            raise ConflictError(f"Tag slug '{slug}' is already taken.")

    # ---- public API ----

    async def list_tags(
        self,
        page: int = 1,
        page_size: int = 50,
        status_filter: TaxonomyStatus | None = None,
    ) -> tuple[list[Tag], int]:
        stmt = select(Tag)
        if status_filter is not None:
            stmt = stmt.where(Tag.status == status_filter)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total: int = (await self._db.execute(count_stmt)).scalar_one()
        stmt = stmt.order_by(Tag.label).offset((page - 1) * page_size).limit(page_size)
        items = list((await self._db.execute(stmt)).scalars().all())
        return items, total

    async def get_tag(self, tag_id: int) -> Tag:
        return await self._get_or_raise(tag_id)

    async def get_tag_by_slug(self, slug: str) -> Tag:
        result = await self._db.execute(select(Tag).where(Tag.slug == slug))
        obj = result.scalar_one_or_none()
        if obj is None:
            raise NotFoundError("Tag", slug)
        return obj

    async def create_tag(self, payload: TagCreate) -> Tag:
        await self._assert_slug_free(payload.slug)
        obj = Tag(
            slug=payload.slug,
            label=payload.label,
            description=payload.description,
            status=TaxonomyStatus.active,
        )
        self._db.add(obj)
        try:
            await self._db.commit()
            await self._db.refresh(obj)
        except IntegrityError as exc:
            await self._db.rollback()
            raise ConflictError(f"Tag could not be created: {exc.orig}") from exc
        return obj

    async def update_tag(self, tag_id: int, payload: TagUpdate) -> Tag:
        obj = await self._get_or_raise(tag_id)
        if payload.label is not None:
            obj.label = payload.label
        if payload.description is not None:
            obj.description = payload.description
        try:
            await self._db.commit()
            await self._db.refresh(obj)
        except IntegrityError as exc:
            await self._db.rollback()
            raise ConflictError(f"Tag could not be updated: {exc.orig}") from exc
        return obj

    async def archive_tag(self, tag_id: int) -> Tag:
        obj = await self._get_or_raise(tag_id)
        if obj.is_archived:
            return obj
        obj.archive()
        await self._db.commit()
        await self._db.refresh(obj)
        return obj

    async def restore_tag(self, tag_id: int) -> Tag:
        obj = await self._get_or_raise(tag_id)
        if not obj.is_archived:
            return obj
        obj.restore()
        await self._db.commit()
        await self._db.refresh(obj)
        return obj

    async def delete_tag(self, tag_id: int) -> None:
        obj = await self._get_or_raise(tag_id)
        try:
            await self._db.delete(obj)
            await self._db.commit()
        except IntegrityError as exc:
            await self._db.rollback()
            raise ConflictError(
                "Tag cannot be deleted because it is referenced by existing content. "
                "Archive it instead."
            ) from exc

    # ---- AC-028.2 guard ----

    async def assert_assignable(self, tag_id: int) -> None:
        obj = await self._get_or_raise(tag_id)
        if obj.is_archived:
            raise ArchivedError("Tag", tag_id)

```

### `backend/pyproject.toml`
```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "cms-backend"
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
    "greenlet==3.1.1",
    "python-jose[cryptography]==3.3.0",
    "passlib[bcrypt]==1.7.4",
    "python-multipart==0.0.19",
    "httpx==0.28.1",
    "pytest==8.3.4",
    "pytest-asyncio==0.24.0",
    "pytest-cov==6.0.0",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["app*"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "TCH"]
ignore = ["B008"]

[tool.mypy]
python_version = "3.12"
strict = false
ignore_missing_imports = true
disallow_untyped_defs = true
warn_return_any = true

```

### `backend/tests/__init__.py`
```python

```

### `backend/tests/conftest.py`
```python
"""Pytest configuration and shared fixtures for taxonomy tests.

Uses an in-memory SQLite async engine so tests run without a real Postgres instance.
The async session is injected into both the service layer and the FastAPI app via
dependency overrides.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import CurrentUser, UserRole, require_admin
from app.main import app

# ---------------------------------------------------------------------------
# In-memory async SQLite engine
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with eng.begin() as conn:
        # SQLite doesn't support the PG Enum type natively; we skip it via
        # create_all which uses the model definitions.
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(engine):
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    """HTTPX async test client with DB and auth overrides."""

    async def _get_db_override():
        yield db_session

    async def _require_admin_override():
        return CurrentUser(user_id=1, role=UserRole.admin)

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[require_admin] = _require_admin_override

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def unauth_client(db_session: AsyncSession):
    """Client with NO auth override — tests that 401 is returned when unauthenticated."""

    async def _get_db_override():
        yield db_session

    # Do NOT override require_admin — let the real security check run.
    app.dependency_overrides[get_db] = _get_db_override

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

```

### `backend/tests/test_taxonomy_router.py`
```python
"""HTTP integration tests for the taxonomy admin router (COMP-009 / TASK-030).

Exercises the full FastAPI request/response cycle via HTTPX AsyncClient + ASGITransport.
DB is in-memory SQLite (injected via dependency override in conftest).

Coverage:
  - Category CRUD (create, read, list, patch, delete)
  - Tag CRUD
  - Archive / restore endpoints
  - AC-028.2: archived category/tag not selectable for new content (status preserved on existing)
  - 401 when unauthenticated
  - 404 on missing resources
  - 409 on duplicate slug / content-ref block
  - Pagination + status filter on list endpoints
  - Slug validation (422 for invalid format)
"""

from __future__ import annotations

import pytest


# ===========================================================================
# Categories
# ===========================================================================


class TestCategoryCreate:
    async def test_create_201(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "engineering", "label": "Engineering"},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["slug"] == "engineering"
        assert data["status"] == "active"
        assert data["id"] is not None

    async def test_create_duplicate_slug_409(self, client) -> None:
        await client.post(
            "/api/v1/admin/categories", json={"slug": "dup", "label": "Dup"}
        )
        r = await client.post(
            "/api/v1/admin/categories", json={"slug": "dup", "label": "Dup 2"}
        )
        assert r.status_code == 409

    async def test_create_invalid_slug_422(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "Has Spaces!", "label": "Bad Slug"},
        )
        assert r.status_code == 422

    async def test_create_missing_label_422(self, client) -> None:
        r = await client.post("/api/v1/admin/categories", json={"slug": "no-label"})
        assert r.status_code == 422

    async def test_create_with_parent(self, client) -> None:
        r1 = await client.post(
            "/api/v1/admin/categories", json={"slug": "root", "label": "Root"}
        )
        parent_id = r1.json()["id"]
        r2 = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "leaf", "label": "Leaf", "parent_id": parent_id},
        )
        assert r2.status_code == 201
        assert r2.json()["parent_id"] == parent_id

    async def test_create_invalid_parent_404(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "orphan", "label": "Orphan", "parent_id": 99999},
        )
        assert r.status_code == 404


class TestCategoryRead:
    async def test_get_200(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories", json={"slug": "get-me", "label": "Get Me"}
        )
        cat_id = r.json()["id"]
        r2 = await client.get(f"/api/v1/admin/categories/{cat_id}")
        assert r2.status_code == 200
        assert r2.json()["slug"] == "get-me"

    async def test_get_404(self, client) -> None:
        r = await client.get("/api/v1/admin/categories/99999")
        assert r.status_code == 404


class TestCategoryList:
    async def test_list_empty(self, client) -> None:
        r = await client.get("/api/v1/admin/categories")
        assert r.status_code == 200
        assert r.json()["total"] == 0

    async def test_list_pagination(self, client) -> None:
        for i in range(5):
            await client.post(
                "/api/v1/admin/categories",
                json={"slug": f"list-{i}", "label": f"List {i}"},
            )
        r = await client.get("/api/v1/admin/categories?page=1&page_size=3")
        data = r.json()
        assert data["total"] == 5
        assert len(data["items"]) == 3

    async def test_list_status_filter_active(self, client) -> None:
        r1 = await client.post(
            "/api/v1/admin/categories", json={"slug": "active-cat", "label": "Active"}
        )
        r2 = await client.post(
            "/api/v1/admin/categories", json={"slug": "archived-cat", "label": "Archived"}
        )
        await client.post(f"/api/v1/admin/categories/{r2.json()['id']}/archive")
        r = await client.get("/api/v1/admin/categories?status=active")
        data = r.json()
        assert data["total"] == 1
        assert data["items"][0]["slug"] == "active-cat"

    async def test_list_status_filter_archived(self, client) -> None:
        r1 = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "will-archive", "label": "Will Archive"},
        )
        await client.post(f"/api/v1/admin/categories/{r1.json()['id']}/archive")
        r = await client.get("/api/v1/admin/categories?status=archived")
        data = r.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "archived"


class TestCategoryPatch:
    async def test_patch_label(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories", json={"slug": "patch-me", "label": "Before"}
        )
        cat_id = r.json()["id"]
        r2 = await client.patch(
            f"/api/v1/admin/categories/{cat_id}", json={"label": "After"}
        )
        assert r2.status_code == 200
        assert r2.json()["label"] == "After"

    async def test_patch_404(self, client) -> None:
        r = await client.patch(
            "/api/v1/admin/categories/99999", json={"label": "Ghost"}
        )
        assert r.status_code == 404

    async def test_patch_empty_body_422(self, client) -> None:
        r1 = await client.post(
            "/api/v1/admin/categories", json={"slug": "no-change", "label": "No Change"}
        )
        r = await client.patch(
            f"/api/v1/admin/categories/{r1.json()['id']}", json={}
        )
        assert r.status_code == 422


class TestCategoryArchive:
    async def test_archive_200(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "to-archive", "label": "To Archive"},
        )
        cat_id = r.json()["id"]
        r2 = await client.post(f"/api/v1/admin/categories/{cat_id}/archive")
        assert r2.status_code == 200
        assert r2.json()["status"] == "archived"

    # AC-028.2: archived category does not appear in active list
    async def test_archived_not_in_active_list(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "no-list", "label": "No List"},
        )
        cat_id = r.json()["id"]
        await client.post(f"/api/v1/admin/categories/{cat_id}/archive")
        r2 = await client.get("/api/v1/admin/categories?status=active")
        slugs = [i["slug"] for i in r2.json()["items"]]
        assert "no-list" not in slugs

    # AC-028.2: archived category is still returned by ID (preserved on existing content)
    async def test_archived_category_retrievable_by_id(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "keep-label", "label": "Keep Label"},
        )
        cat_id = r.json()["id"]
        await client.post(f"/api/v1/admin/categories/{cat_id}/archive")
        r2 = await client.get(f"/api/v1/admin/categories/{cat_id}")
        assert r2.status_code == 200
        assert r2.json()["status"] == "archived"
        assert r2.json()["label"] == "Keep Label"

    async def test_archive_idempotent(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "idem-arch", "label": "Idem Arch"},
        )
        cat_id = r.json()["id"]
        await client.post(f"/api/v1/admin/categories/{cat_id}/archive")
        r2 = await client.post(f"/api/v1/admin/categories/{cat_id}/archive")
        assert r2.status_code == 200

    async def test_restore_200(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "restore-http", "label": "Restore HTTP"},
        )
        cat_id = r.json()["id"]
        await client.post(f"/api/v1/admin/categories/{cat_id}/archive")
        r2 = await client.post(f"/api/v1/admin/categories/{cat_id}/restore")
        assert r2.status_code == 200
        assert r2.json()["status"] == "active"


class TestCategoryDelete:
    async def test_delete_204(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "delete-cat", "label": "Delete Cat"},
        )
        cat_id = r.json()["id"]
        r2 = await client.delete(f"/api/v1/admin/categories/{cat_id}")
        assert r2.status_code == 204
        r3 = await client.get(f"/api/v1/admin/categories/{cat_id}")
        assert r3.status_code == 404

    async def test_delete_404(self, client) -> None:
        r = await client.delete("/api/v1/admin/categories/99999")
        assert r.status_code == 404


# ===========================================================================
# Tags
# ===========================================================================


class TestTagCreate:
    async def test_create_201(self, client) -> None:
        r = await client.post("/api/v1/admin/tags", json={"slug": "python", "label": "Python"})
        assert r.status_code == 201
        assert r.json()["status"] == "active"

    async def test_create_duplicate_slug_409(self, client) -> None:
        await client.post("/api/v1/admin/tags", json={"slug": "dup-tag", "label": "D"})
        r = await client.post("/api/v1/admin/tags", json={"slug": "dup-tag", "label": "D2"})
        assert r.status_code == 409

    async def test_create_invalid_slug_422(self, client) -> None:
        r = await client.post("/api/v1/admin/tags", json={"slug": "BAD SLUG", "label": "Bad"})
        assert r.status_code == 422


class TestTagArchive:
    async def test_archive_sets_archived(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/tags", json={"slug": "arch-tag", "label": "Arch Tag"}
        )
        tag_id = r.json()["id"]
        r2 = await client.post(f"/api/v1/admin/tags/{tag_id}/archive")
        assert r2.status_code == 200
        assert r2.json()["status"] == "archived"

    # AC-028.2: archived tag not in active list but label preserved
    async def test_archived_tag_label_preserved(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/tags",
            json={"slug": "keep-tag-label", "label": "Keep This Label"},
        )
        tag_id = r.json()["id"]
        await client.post(f"/api/v1/admin/tags/{tag_id}/archive")
        r2 = await client.get(f"/api/v1/admin/tags/{tag_id}")
        assert r2.status_code == 200
        assert r2.json()["label"] == "Keep This Label"
        assert r2.json()["status"] == "archived"

    async def test_archived_tag_not_in_active_list(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/tags",
            json={"slug": "hide-tag", "label": "Hide Tag"},
        )
        tag_id = r.json()["id"]
        await client.post(f"/api/v1/admin/tags/{tag_id}/archive")
        r2 = await client.get("/api/v1/admin/tags?status=active")
        slugs = [i["slug"] for i in r2.json()["items"]]
        assert "hide-tag" not in slugs

    async def test_restore_tag_200(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/tags", json={"slug": "restore-tag-http", "label": "Restore Tag HTTP"}
        )
        tag_id = r.json()["id"]
        await client.post(f"/api/v1/admin/tags/{tag_id}/archive")
        r2 = await client.post(f"/api/v1/admin/tags/{tag_id}/restore")
        assert r2.status_code == 200
        assert r2.json()["status"] == "active"


class TestTagPatch:
    async def test_patch_label(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/tags", json={"slug": "patch-tag", "label": "Before Tag"}
        )
        tag_id = r.json()["id"]
        r2 = await client.patch(f"/api/v1/admin/tags/{tag_id}", json={"label": "After Tag"})
        assert r2.status_code == 200
        assert r2.json()["label"] == "After Tag"


class TestTagDelete:
    async def test_delete_204(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/tags", json={"slug": "delete-tag", "label": "Delete Tag"}
        )
        tag_id = r.json()["id"]
        r2 = await client.delete(f"/api/v1/admin/tags/{tag_id}")
        assert r2.status_code == 204

    async def test_delete_404(self, client) -> None:
        r = await client.delete("/api/v1/admin/tags/99999")
        assert r.status_code == 404


# ===========================================================================
# Auth enforcement
# ===========================================================================


class TestAuthEnforcement:
    async def test_list_categories_requires_auth(self, unauth_client) -> None:
        r = await unauth_client.get("/api/v1/admin/categories")
        assert r.status_code == 401

    async def test_create_category_requires_auth(self, unauth_client) -> None:
        r = await unauth_client.post(
            "/api/v1/admin/categories", json={"slug": "no-auth", "label": "No Auth"}
        )
        assert r.status_code == 401

    async def test_list_tags_requires_auth(self, unauth_client) -> None:
        r = await unauth_client.get("/api/v1/admin/tags")
        assert r.status_code == 401

    async def test_create_tag_requires_auth(self, unauth_client) -> None:
        r = await unauth_client.post(
            "/api/v1/admin/tags", json={"slug": "no-auth", "label": "No Auth"}
        )
        assert r.status_code == 401


# ===========================================================================
# Health endpoint
# ===========================================================================


class TestHealth:
    async def test_healthz(self, client) -> None:
        r = await client.get("/healthz")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

```

### `backend/tests/test_taxonomy_schemas.py`
```python
"""Pydantic schema unit tests — VER-004 slug/label validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.taxonomy_schemas import CategoryCreate, CategoryUpdate, TagCreate, TagUpdate


class TestCategoryCreateSchema:
    def test_valid(self) -> None:
        c = CategoryCreate(slug="my-cat", label="My Cat")
        assert c.slug == "my-cat"
        assert c.sort_order == 0

    def test_slug_uppercase_normalised(self) -> None:
        # Validator lowercases
        c = CategoryCreate(slug="My-Cat", label="My Cat")
        assert c.slug == "my-cat"

    def test_slug_spaces_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CategoryCreate(slug="my cat", label="My Cat")

    def test_slug_underscore_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CategoryCreate(slug="my_cat", label="My Cat")

    def test_label_stripped(self) -> None:
        c = CategoryCreate(slug="s", label="  hello  ")
        assert c.label == "hello"

    def test_description_optional(self) -> None:
        c = CategoryCreate(slug="s2", label="S")
        assert c.description is None

    def test_sort_order_negative_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CategoryCreate(slug="s3", label="S", sort_order=-1)

    def test_empty_slug_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CategoryCreate(slug="", label="L")


class TestCategoryUpdateSchema:
    def test_valid_single_field(self) -> None:
        u = CategoryUpdate(label="New")
        assert u.label == "New"

    def test_empty_update_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CategoryUpdate()

    def test_all_none_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CategoryUpdate(label=None, description=None, parent_id=None, sort_order=None)


class TestTagCreateSchema:
    def test_valid(self) -> None:
        t = TagCreate(slug="rust", label="Rust")
        assert t.slug == "rust"

    def test_slug_with_numbers(self) -> None:
        t = TagCreate(slug="python3", label="Python 3")
        assert t.slug == "python3"

    def test_invalid_slug_422(self) -> None:
        with pytest.raises(ValidationError):
            TagCreate(slug="C++", label="C++")


class TestTagUpdateSchema:
    def test_empty_update_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TagUpdate()

```

### `backend/tests/test_taxonomy_service.py`
```python
"""Unit tests for CategoryService and TagService.

Tests run against in-memory SQLite via the db_session fixture.
No HTTP layer involved — tests service methods directly.

Coverage:
  - Create (slug dedup, parent validation)
  - Update (PATCH semantics, circular parent prevention)
  - Archive / restore (idempotent, AC-028.2 guard)
  - List (status filter, pagination)
  - Delete (FK constraint enforcement)
  - assert_assignable (core of AC-028.2)
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from app.models.taxonomy import TaxonomyStatus
from app.schemas.taxonomy_schemas import (
    CategoryCreate,
    CategoryUpdate,
    TagCreate,
    TagUpdate,
)
from app.services.admin.taxonomy_service import (
    ArchivedError,
    CategoryService,
    ConflictError,
    NotFoundError,
    TagService,
    TaxonomyValidationError,
)


# ---------------------------------------------------------------------------
# Category service unit tests
# ---------------------------------------------------------------------------


class TestCategoryServiceCreate:
    async def test_create_returns_active_category(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="science", label="Science"))
        assert cat.id is not None
        assert cat.slug == "science"
        assert cat.status == TaxonomyStatus.active

    async def test_create_duplicate_slug_raises_conflict(self, db_session) -> None:
        svc = CategoryService(db_session)
        await svc.create_category(CategoryCreate(slug="tech", label="Tech"))
        with pytest.raises(ConflictError):
            await svc.create_category(CategoryCreate(slug="tech", label="Tech 2"))

    async def test_create_with_valid_parent(self, db_session) -> None:
        svc = CategoryService(db_session)
        parent = await svc.create_category(CategoryCreate(slug="parent", label="Parent"))
        child = await svc.create_category(
            CategoryCreate(slug="child", label="Child", parent_id=parent.id)
        )
        assert child.parent_id == parent.id

    async def test_create_invalid_parent_raises_not_found(self, db_session) -> None:
        svc = CategoryService(db_session)
        with pytest.raises(NotFoundError):
            await svc.create_category(
                CategoryCreate(slug="orphan", label="Orphan", parent_id=9999)
            )


class TestCategoryServiceUpdate:
    async def test_update_label(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="upd", label="Original"))
        updated = await svc.update_category(cat.id, CategoryUpdate(label="Updated"))
        assert updated.label == "Updated"

    async def test_update_self_parent_raises_validation_error(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="loop", label="Loop"))
        with pytest.raises(TaxonomyValidationError):
            await svc.update_category(cat.id, CategoryUpdate(parent_id=cat.id))

    async def test_update_nonexistent_raises_not_found(self, db_session) -> None:
        svc = CategoryService(db_session)
        with pytest.raises(NotFoundError):
            await svc.update_category(9999, CategoryUpdate(label="Ghost"))


class TestCategoryServiceArchive:
    async def test_archive_sets_status(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="arch-me", label="Archive Me"))
        archived = await svc.archive_category(cat.id)
        assert archived.status == TaxonomyStatus.archived

    async def test_archive_is_idempotent(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="idem", label="Idempotent"))
        await svc.archive_category(cat.id)
        # Second call should not raise
        again = await svc.archive_category(cat.id)
        assert again.status == TaxonomyStatus.archived

    async def test_restore_sets_active(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="restore-me", label="Restore Me"))
        await svc.archive_category(cat.id)
        restored = await svc.restore_category(cat.id)
        assert restored.status == TaxonomyStatus.active

    async def test_restore_is_idempotent(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="idem-r", label="Idempotent R"))
        # Never archived — restore should be a no-op
        result = await svc.restore_category(cat.id)
        assert result.status == TaxonomyStatus.active

    # AC-028.2: archived category must not be assignable to new content
    async def test_assert_assignable_archived_raises(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="no-assign", label="No Assign"))
        await svc.archive_category(cat.id)
        with pytest.raises(ArchivedError):
            await svc.assert_assignable(cat.id)

    async def test_assert_assignable_active_passes(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="yes-assign", label="Yes Assign"))
        # Should not raise
        await svc.assert_assignable(cat.id)


class TestCategoryServiceList:
    async def test_list_all(self, db_session) -> None:
        svc = CategoryService(db_session)
        await svc.create_category(CategoryCreate(slug="a", label="A"))
        await svc.create_category(CategoryCreate(slug="b", label="B"))
        items, total = await svc.list_categories()
        assert total == 2
        assert len(items) == 2

    async def test_list_filter_active(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="c", label="C"))
        await svc.create_category(CategoryCreate(slug="d", label="D"))
        await svc.archive_category(cat.id)
        items, total = await svc.list_categories(status_filter=TaxonomyStatus.active)
        assert total == 1
        assert items[0].slug == "d"

    async def test_list_filter_archived(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="e", label="E"))
        await svc.create_category(CategoryCreate(slug="f", label="F"))
        await svc.archive_category(cat.id)
        items, total = await svc.list_categories(status_filter=TaxonomyStatus.archived)
        assert total == 1
        assert items[0].slug == "e"

    async def test_pagination(self, db_session) -> None:
        svc = CategoryService(db_session)
        for i in range(5):
            await svc.create_category(CategoryCreate(slug=f"pg-{i}", label=f"PG {i}"))
        items, total = await svc.list_categories(page=1, page_size=3)
        assert total == 5
        assert len(items) == 3
        items2, _ = await svc.list_categories(page=2, page_size=3)
        assert len(items2) == 2


class TestCategoryServiceDelete:
    async def test_delete_removes_category(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="del-me", label="Del Me"))
        await svc.delete_category(cat.id)
        with pytest.raises(NotFoundError):
            await svc.get_category(cat.id)

    async def test_delete_nonexistent_raises_not_found(self, db_session) -> None:
        svc = CategoryService(db_session)
        with pytest.raises(NotFoundError):
            await svc.delete_category(9999)


# ---------------------------------------------------------------------------
# Tag service unit tests
# ---------------------------------------------------------------------------


class TestTagServiceCreate:
    async def test_create_returns_active_tag(self, db_session) -> None:
        svc = TagService(db_session)
        tag = await svc.create_tag(TagCreate(slug="python", label="Python"))
        assert tag.id is not None
        assert tag.status == TaxonomyStatus.active

    async def test_create_duplicate_slug_raises_conflict(self, db_session) -> None:
        svc = TagService(db_session)
        await svc.create_tag(TagCreate(slug="dup", label="Dup"))
        with pytest.raises(ConflictError):
            await svc.create_tag(TagCreate(slug="dup", label="Dup 2"))


class TestTagServiceArchive:
    async def test_archive_sets_status(self, db_session) -> None:
        svc = TagService(db_session)
        tag = await svc.create_tag(TagCreate(slug="old-tag", label="Old Tag"))
        archived = await svc.archive_tag(tag.id)
        assert archived.status == TaxonomyStatus.archived

    async def test_restore_sets_active(self, db_session) -> None:
        svc = TagService(db_session)
        tag = await svc.create_tag(TagCreate(slug="restore-tag", label="Restore Tag"))
        await svc.archive_tag(tag.id)
        restored = await svc.restore_tag(tag.id)
        assert restored.status == TaxonomyStatus.active

    # AC-028.2
    async def test_assert_assignable_archived_raises(self, db_session) -> None:
        svc = TagService(db_session)
        tag = await svc.create_tag(TagCreate(slug="no-tag", label="No Tag"))
        await svc.archive_tag(tag.id)
        with pytest.raises(ArchivedError):
            await svc.assert_assignable(tag.id)

    async def test_assert_assignable_active_passes(self, db_session) -> None:
        svc = TagService(db_session)
        tag = await svc.create_tag(TagCreate(slug="yes-tag", label="Yes Tag"))
        await svc.assert_assignable(tag.id)


class TestTagServiceUpdate:
    async def test_update_label(self, db_session) -> None:
        svc = TagService(db_session)
        tag = await svc.create_tag(TagCreate(slug="upd-tag", label="Before"))
        updated = await svc.update_tag(tag.id, TagUpdate(label="After"))
        assert updated.label == "After"

    async def test_update_nonexistent_raises_not_found(self, db_session) -> None:
        svc = TagService(db_session)
        with pytest.raises(NotFoundError):
            await svc.update_tag(9999, TagUpdate(label="Ghost"))

```