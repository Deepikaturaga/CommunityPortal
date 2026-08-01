# Implementation Report

Now fix the conftest unused import and suppress B008 in pyproject + fix long lines in tests:

## Verification
- `python3 -c "
import os, json
result = []
for root, dirs, files in os.walk('backend'):
    dirs[:] = sorted([d for d in dirs if d not in ['__pycache__','.venv','node_modules','.git','dist']])
    for f in sorted(files):
        result.append(os.path.join(root, f))
print('\n'.join(result))
"` → exit 0
- `python3 -c "
import os
for root, dirs, files in os.walk('.'):
    dirs[:] = sorted([d for d in dirs if d not in ['__pycache__','.venv','node_modules','.git','dist','site-packages']])
    for f in sorted(files):
        print(os.path.join(root, f))
"` → exit 0
- `python3 -c "import subprocess; r = subprocess.run(['git','log','--oneline','-20'], capture_output=True, text=True); print(r.stdout); print(r.stderr)"` → exit 1
- `pip show fastapi pydantic sqlalchemy alembic` → exit 0
- `pip show pytest pytest-asyncio httpx` → exit 0
- `pip show backend` → exit 0
- `python3 -c "
import os
base = '/tmp/archpilot_verify_zlautyjj/backend'
for root, dirs, files in os.walk(base):
    dirs[:] = sorted([d for d in dirs if d not in ['__pycache__','.venv','node_modules','.git','dist','site-packages']])
    for f in sorted(files):
        print(os.path.join(root, f).replace(base, 'backend'))
"` → exit 0
- `python3 -c "
import importlib.util, sys
spec = importlib.util.find_spec('app')
print(spec)
import app
print(app.__file__)
"` → exit 1
- `python3 -c "
import pkg_resources, os
dist = pkg_resources.get_distribution('backend')
print('Location:', dist.location)
print('Egg-link:', getattr(dist, 'egg_link', 'N/A'))
# list direct_url
try:
    with open(os.path.join(dist.egg_info, 'direct_url.json')) as f:
        print(f.read())
except Exception as e:
    print(e)
"` → exit 1
- `pip show -f backend` → exit 0
- `python3 -c "
with open('/usr/local/lib/python3.12/site-packages/__editable__.backend-0.1.0.pth') as f:
    print(f.read())
"` → exit 0
- `python3 -c "
with open('/usr/local/lib/python3.12/site-packages/__editable___backend_0_1_0_finder.py') as f:
    print(f.read())
"` → exit 0
- `python3 -c "
import os
base = '/tmp/archpilot_verify_zlautyjj/backend'
for root, dirs, files in os.walk(base):
    dirs[:] = sorted([d for d in dirs if d not in ['__pycache__','.venv','node_modules','.git','dist','site-packages']])
    for f in sorted(files):
        full = os.path.join(root, f)
        rel  = full.replace(base + '/', 'backend/')
        print(rel)
"` → exit 0
- `python3 -c "
import os
base = '/tmp/archpilot_verify_zlautyjj'
for root, dirs, files in os.walk(base):
    dirs[:] = sorted([d for d in dirs if d not in ['__pycache__','.venv','node_modules','.git','dist','site-packages']])
    for f in sorted(files):
        full = os.path.join(root, f)
        rel  = full.replace(base + '/', '')
        print(rel)
"` → exit 0
- `python3 -c "
import os
base = '/tmp/archpilot_verify_zlautyjj'
print('exists:', os.path.exists(base))
print('ls:', os.listdir(base))
"` → exit 1
- `python3 -c "
import os, sys
# find where the editable backend lives
for p in sys.path:
    if 'backend' in p.lower():
        print('sys.path entry:', p)
# check direct_url
import json
with open('/usr/local/lib/python3.12/site-packages/backend-0.1.0.dist-info/direct_url.json') as f:
    print(json.load(f))
"` → exit 0
- `python3 -c "
import os
# The editable path was /tmp/archpilot_verify_zlautyjj/backend
# Let's find the actual mount
import glob
candidates = glob.glob('/tmp/arch*') + glob.glob('/tmp/back*') + glob.glob('/workspace*') + glob.glob('/app*') + glob.glob('/srv*') + glob.glob('/home/*')
for c in candidates:
    print(c)
"` → exit 0
- `python3 -c "
import os
for root, dirs, files in os.walk('/tmp/archpilot_verify_51ub0f98'):
    dirs[:] = sorted([d for d in dirs if d not in ['__pycache__','.venv','node_modules','.git','dist','site-packages']])
    for f in sorted(files):
        print(os.path.join(root, f))
"` → exit 0
- `python3 -c "
import os
for root, dirs, files in os.walk('/app'):
    dirs[:] = sorted([d for d in dirs if d not in ['__pycache__','.venv','node_modules','.git','dist','site-packages']])
    for f in sorted(files):
        print(os.path.join(root, f))
"` → exit 0
- `python3 -c "import os; print(os.getcwd())"` → exit 0
- `python3 -c "
import os
base = '/tmp/archpilot_verify_f3_i8p5s'
print('exists:', os.path.exists(base))
print('ls:', os.listdir(base) if os.path.exists(base) else 'MISSING')
"` → exit 0
- `python3 -c "
import os, glob
# find the probe file
for root, dirs, files in os.walk('/'):
    dirs[:] = [d for d in dirs if d not in ['proc','sys','dev','run','usr','etc','bin','lib','lib64','boot','opt','media','mnt','snap','srv'] and 'cache' not in d.lower()]
    for f in files:
        if f == '.probe':
            print(os.path.join(root, f))
"` → exit 0
- `python3 -c "
import os
base = '/tmp/archpilot_verify_f2a8fxgw'
for root, dirs, files in os.walk(base):
    dirs[:] = sorted([d for d in dirs if d not in ['__pycache__','.venv','node_modules','.git','dist','site-packages']])
    for f in sorted(files):
        print(os.path.join(root, f).replace(base+'/', ''))
"` → exit 0
- `python3 -c "
import json
with open('/usr/local/lib/python3.12/site-packages/backend-0.1.0.dist-info/direct_url.json') as f:
    d = json.load(f)
print('Editable source:', d['url'])
"` → exit 0
- `python3 -c "
import os
base = '/tmp/archpilot_verify_zlautyjj/backend'
print('exists:', os.path.exists(base))
"` → exit 0
- `pip show aiosqlite asyncpg passlib python-jose pydantic-settings python-multipart` → exit 0
- `ruff check backend/app backend/tests --select E,F,I,UP,B` → exit 1

## Generated Files

### `backend/.env.example`
```text
DATABASE_URL=sqlite+aiosqlite:///./dev.db
SECRET_KEY=changeme-dev-secret-32-bytes-long!!
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=development

```

### `backend/alembic.ini`
```text
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = sqlite+aiosqlite:///./dev.db

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
"""Alembic env.py — async SQLAlchemy 2.0 pattern."""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ── Metadata import ──────────────────────────────────────────────────────────
# Import all models so Alembic sees their metadata.
from app.core.database import Base  # noqa: F401
import app.services.moderation.models  # noqa: F401

# ── Config ────────────────────────────────────────────────────────────────────
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# ── Offline migrations ────────────────────────────────────────────────────────
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


# ── Online migrations ─────────────────────────────────────────────────────────
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

### `backend/alembic/versions/0001_create_moderation_reports.py`
```python
"""create moderation_reports table

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "moderation_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("reporter_id", sa.String(36), nullable=False),
        sa.Column("target_id", sa.String(36), nullable=False),
        sa.Column(
            "reason",
            sa.Enum(
                "spam",
                "harassment",
                "hate_speech",
                "misinformation",
                "violence",
                "other",
                name="report_reason_enum",
            ),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "reviewed",
                "dismissed",
                "actioned",
                name="report_status_enum",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("reviewed_by", sa.String(36), nullable=True),
        sa.Column("reviewer_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        # AC-015.2 — duplicate-report unique constraint
        sa.UniqueConstraint(
            "reporter_id",
            "target_id",
            name="uq_moderation_report_reporter_target",
        ),
    )
    op.create_index("ix_moderation_reports_reporter_id", "moderation_reports", ["reporter_id"])
    op.create_index("ix_moderation_reports_target_id", "moderation_reports", ["target_id"])
    op.create_index("ix_moderation_reports_status", "moderation_reports", ["status"])
    op.create_index("ix_moderation_reports_created_at", "moderation_reports", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_moderation_reports_created_at", "moderation_reports")
    op.drop_index("ix_moderation_reports_status", "moderation_reports")
    op.drop_index("ix_moderation_reports_target_id", "moderation_reports")
    op.drop_index("ix_moderation_reports_reporter_id", "moderation_reports")
    op.drop_table("moderation_reports")
    # SQLite does not support DROP TYPE; guard for Postgres
    try:
        op.execute("DROP TYPE IF EXISTS report_reason_enum")
        op.execute("DROP TYPE IF EXISTS report_status_enum")
    except Exception:
        pass

```

### `backend/app/__init__.py`
```python
from __future__ import annotations

```

### `backend/app/core/__init__.py`
```python
from __future__ import annotations

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
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./dev.db"

    # Security
    secret_key: str = "changeme-dev-secret-32-bytes-long!!"
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"

    # Runtime
    environment: str = "development"
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()

```

### `backend/app/core/database.py`
```python
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
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
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

```

### `backend/app/core/errors.py`
```python
from __future__ import annotations

from http import HTTPStatus

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ConflictError(AppError):
    def __init__(self, message: str = "Resource conflict") -> None:
        super().__init__(message, status_code=HTTPStatus.CONFLICT)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status_code=HTTPStatus.NOT_FOUND)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message, status_code=HTTPStatus.FORBIDDEN)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred."},
    )

```

### `backend/app/main.py`
```python
"""
Canonical ASGI entrypoint — app.main:app
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import Base, engine
from app.core.errors import AppError, app_error_handler, unhandled_error_handler
from app.services.moderation.router import router as moderation_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Create tables for test/dev (SQLite). Alembic manages prod migrations.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Backend API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Exception handlers ────────────────────────────────────────────────────────
app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, unhandled_error_handler)  # type: ignore[arg-type]

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(moderation_router, prefix="/api/v1")


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["ops"], include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}

```

### `backend/app/services/__init__.py`
```python
from __future__ import annotations

```

### `backend/app/services/moderation/__init__.py`
```python
from __future__ import annotations

```

### `backend/app/services/moderation/models.py`
```python
"""
STORE-006 — ModerationReport ORM model.

Unique constraint on (reporter_id, target_id) enforces AC-015.2: a single
reporter may not file more than one report against the same target.
"""
from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


class ReportReason(str, enum.Enum):
    SPAM = "spam"
    HARASSMENT = "harassment"
    HATE_SPEECH = "hate_speech"
    MISINFORMATION = "misinformation"
    VIOLENCE = "violence"
    OTHER = "other"


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    DISMISSED = "dismissed"
    ACTIONED = "actioned"


class ModerationReport(Base):
    """
    STORE-006 — Moderation report submitted by a user.

    Constraints
    -----------
    * uq_moderation_report_reporter_target — prevents duplicate submissions
      from the same reporter against the same target (AC-015.2).
    """

    __tablename__ = "moderation_reports"

    __table_args__ = (
        # AC-015.2 duplicate-report unique constraint
        UniqueConstraint(
            "reporter_id",
            "target_id",
            name="uq_moderation_report_reporter_target",
        ),
        # performance index for moderator queue queries
        Index("ix_moderation_reports_status", "status"),
        Index("ix_moderation_reports_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ── Parties ──────────────────────────────────────────────────────────────
    # reporter_id and target_id are UUIDs referencing the user store.
    # They are stored as plain strings to remain decoupled from the user
    # service schema; a FK constraint is added when that table is in scope.
    reporter_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # ── Content ───────────────────────────────────────────────────────────────
    reason: Mapped[str] = mapped_column(
        Enum(ReportReason, name="report_reason_enum", create_constraint=True),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        Enum(ReportStatus, name="report_status_enum", create_constraint=True),
        nullable=False,
        default=ReportStatus.PENDING,
        server_default=ReportStatus.PENDING.value,
    )
    reviewed_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    def __repr__(self) -> str:
        return (
            f"<ModerationReport id={self.id!r} "
            f"reporter={self.reporter_id!r} "
            f"target={self.target_id!r} "
            f"status={self.status!r}>"
        )

```

### `backend/app/services/moderation/reports.py`
```python
"""
COMP-006 report intake service.

Business rules
--------------
* AC-015.2: duplicate (reporter_id, target_id) → ConflictError → HTTP 409.
* A reporter may not report themselves (self-report guard).
* Duplicate detection is enforced at both the DB layer (unique constraint)
  and the service layer (explicit pre-check) for a clear 409 error message
  rather than a raw integrity-error 500.
"""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.services.moderation.models import ModerationReport, ReportStatus
from app.services.moderation.schemas import ReportCreate, ReportResponse


class ModerationReportService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Intake ────────────────────────────────────────────────────────────────

    async def create_report(self, payload: ReportCreate) -> ReportResponse:
        """
        Accept a new moderation report.

        Raises
        ------
        ForbiddenError  — reporter and target are the same user.
        ConflictError   — a report from reporter_id against target_id already
                          exists (AC-015.2 → HTTP 409).
        """
        if payload.reporter_id == payload.target_id:
            raise ForbiddenError("A user may not report themselves.")

        # Explicit pre-check (fast path) — avoids relying solely on DB error
        existing = await self._db.scalar(
            select(ModerationReport).where(
                ModerationReport.reporter_id == payload.reporter_id,
                ModerationReport.target_id == payload.target_id,
            )
        )
        if existing is not None:
            raise ConflictError(
                f"A report from reporter {payload.reporter_id!r} against "
                f"target {payload.target_id!r} already exists."
            )

        report = ModerationReport(
            id=str(uuid.uuid4()),
            reporter_id=payload.reporter_id,
            target_id=payload.target_id,
            reason=payload.reason.value,
            description=payload.description,
            status=ReportStatus.PENDING.value,
        )
        self._db.add(report)

        try:
            await self._db.commit()
            await self._db.refresh(report)
        except IntegrityError as exc:
            await self._db.rollback()
            # Race-condition guard: another request beat us to the unique slot.
            raise ConflictError(
                f"A report from reporter {payload.reporter_id!r} against "
                f"target {payload.target_id!r} already exists."
            ) from exc

        return ReportResponse.model_validate(report)

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_report(self, report_id: str) -> ReportResponse:
        row = await self._db.get(ModerationReport, report_id)
        if row is None:
            raise NotFoundError(f"Report {report_id!r} not found.")
        return ReportResponse.model_validate(row)

    async def list_reports(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[ReportResponse], int]:
        count_q = select(func.count()).select_from(ModerationReport)
        total: int = await self._db.scalar(count_q) or 0

        rows_q = (
            select(ModerationReport)
            .order_by(ModerationReport.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._db.execute(rows_q)
        rows = result.scalars().all()
        return [ReportResponse.model_validate(r) for r in rows], total

```

### `backend/app/services/moderation/router.py`
```python
"""
COMP-006 Moderation Report Intake — HTTP router (IF-008).

Routes
------
POST   /moderation/reports          → 201 ReportResponse  | 409 on duplicate
GET    /moderation/reports          → 200 ReportListResponse
GET    /moderation/reports/{id}     → 200 ReportResponse  | 404
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.moderation.reports import ModerationReportService
from app.services.moderation.schemas import (
    ReportCreate,
    ReportListResponse,
    ReportResponse,
)

router = APIRouter(prefix="/moderation/reports", tags=["moderation"])


def _svc(db: AsyncSession = Depends(get_db)) -> ModerationReportService:
    return ModerationReportService(db)


@router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a moderation report (IF-008 / COMP-006)",
    responses={
        409: {"description": "Duplicate report for this (reporter_id, target_id) pair."},
        403: {"description": "Reporter and target must be different users."},
    },
)
async def create_report(
    payload: ReportCreate,
    svc: ModerationReportService = Depends(_svc),
) -> ReportResponse:
    """
    Submit a new moderation report.

    Returns **HTTP 409** when a report from the same ``reporter_id``
    against the same ``target_id`` already exists (AC-015.2).
    """
    return await svc.create_report(payload)


@router.get(
    "",
    response_model=ReportListResponse,
    status_code=status.HTTP_200_OK,
    summary="List moderation reports",
)
async def list_reports(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    svc: ModerationReportService = Depends(_svc),
) -> ReportListResponse:
    items, total = await svc.list_reports(offset=offset, limit=limit)
    return ReportListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch a single moderation report",
    responses={404: {"description": "Report not found."}},
)
async def get_report(
    report_id: str,
    svc: ModerationReportService = Depends(_svc),
) -> ReportResponse:
    return await svc.get_report(report_id)

```

### `backend/app/services/moderation/schemas.py`
```python
"""
Pydantic v2 schemas for COMP-006 report intake (IF-008).
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.services.moderation.models import ReportReason, ReportStatus

# ── Request ───────────────────────────────────────────────────────────────────

_UUIDStr = Annotated[str, StringConstraints(min_length=36, max_length=36)]


class ReportCreate(BaseModel):
    """Body for POST /moderation/reports (IF-008)."""

    reporter_id: _UUIDStr = Field(
        ...,
        description="UUID of the user filing the report.",
    )
    target_id: _UUIDStr = Field(
        ...,
        description="UUID of the user or content being reported.",
    )
    reason: ReportReason = Field(
        ...,
        description="Category that best describes the violation.",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional free-text elaboration (max 2 000 chars).",
    )


# ── Response ──────────────────────────────────────────────────────────────────


class ReportResponse(BaseModel):
    """Serialised ModerationReport returned to callers."""

    id: str
    reporter_id: str
    target_id: str
    reason: ReportReason
    description: str | None
    status: ReportStatus
    reviewed_by: str | None
    reviewer_note: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Paginated list ────────────────────────────────────────────────────────────


class ReportListResponse(BaseModel):
    items: list[ReportResponse]
    total: int
    limit: int
    offset: int

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
    "fastapi>=0.115.5",
    "pydantic>=2.10.3",
    "pydantic-settings>=2.6.1",
    "sqlalchemy>=2.0.36",
    "alembic>=1.14.0",
    "aiosqlite>=0.20.0",
    "asyncpg>=0.30.0",
    "passlib>=1.7.4",
    "python-jose>=3.3.0",
    "python-multipart>=0.0.19",
    "httpx>=0.28.1",
]

[project.optional-dependencies]
test = [
    "pytest>=8.3.4",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.28.1",
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
select = ["E", "F", "I", "UP", "B", "S"]
ignore = ["S101", "B008"]

```

### `backend/tests/__init__.py`
```python
from __future__ import annotations

```

### `backend/tests/conftest.py`
```python
"""
Shared pytest fixtures for the backend test suite.
Uses an in-memory SQLite database (aiosqlite) for isolation.
"""
from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Per-test isolated async SQLite session."""
    engine = create_async_engine(TEST_DB_URL, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    async with factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    """
    HTTPX AsyncClient wired to the FastAPI test app with
    the test DB session injected via dependency override.
    """

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()

```

### `backend/tests/test_moderation_reports.py`
```python
"""
Tests for COMP-006 moderation report intake (TASK-036 / AC-015.x).

AC-015.1  POST /api/v1/moderation/reports → 201 with ReportResponse body.
AC-015.2  Duplicate (reporter_id, target_id) → 409.
AC-015.3  Self-report (reporter_id == target_id) → 403.
AC-015.4  Missing required fields → 422.
AC-015.5  GET /api/v1/moderation/reports → 200 list.
AC-015.6  GET /api/v1/moderation/reports/{id} → 200 | 404.
"""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

BASE = "/api/v1/moderation/reports"

REPORTER = str(uuid.uuid4())
TARGET   = str(uuid.uuid4())
THIRD    = str(uuid.uuid4())


def _valid_payload(
    reporter_id: str = REPORTER,
    target_id: str = TARGET,
    reason: str = "spam",
    description: str | None = "Test report",
) -> dict:
    p: dict = {
        "reporter_id": reporter_id,
        "target_id": target_id,
        "reason": reason,
    }
    if description is not None:
        p["description"] = description
    return p


# ── AC-015.1 — happy path ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_report_returns_201(client: AsyncClient) -> None:
    resp = await client.post(BASE, json=_valid_payload())
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["reporter_id"] == REPORTER
    assert body["target_id"] == TARGET
    assert body["reason"] == "spam"
    assert body["status"] == "pending"
    assert "id" in body
    assert "created_at" in body


@pytest.mark.asyncio
async def test_create_report_no_description(client: AsyncClient) -> None:
    resp = await client.post(BASE, json=_valid_payload(description=None))
    assert resp.status_code == 201, resp.text
    assert resp.json()["description"] is None


# ── AC-015.2 — duplicate (reporter_id, target_id) → 409 ──────────────────────


@pytest.mark.asyncio
async def test_duplicate_report_returns_409(client: AsyncClient) -> None:
    """
    AC-015.2: submitting a second report with the same (reporter_id, target_id)
    must return HTTP 409 Conflict.
    """
    payload = _valid_payload()
    r1 = await client.post(BASE, json=payload)
    assert r1.status_code == 201, r1.text

    r2 = await client.post(BASE, json=payload)
    assert r2.status_code == 409, r2.text
    assert "already exists" in r2.json()["detail"].lower() or "conflict" in r2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_different_reporter_same_target_allowed(client: AsyncClient) -> None:
    """Different reporters may independently report the same target."""
    r1 = await client.post(BASE, json=_valid_payload(reporter_id=REPORTER, target_id=TARGET))
    r2 = await client.post(BASE, json=_valid_payload(reporter_id=THIRD, target_id=TARGET))
    assert r1.status_code == 201, r1.text
    assert r2.status_code == 201, r2.text


@pytest.mark.asyncio
async def test_same_reporter_different_targets_allowed(client: AsyncClient) -> None:
    """A reporter may file reports against distinct targets."""
    r1 = await client.post(BASE, json=_valid_payload(reporter_id=REPORTER, target_id=TARGET))
    r2 = await client.post(BASE, json=_valid_payload(reporter_id=REPORTER, target_id=THIRD))
    assert r1.status_code == 201, r1.text
    assert r2.status_code == 201, r2.text


# ── AC-015.3 — self-report → 403 ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_self_report_returns_403(client: AsyncClient) -> None:
    same = str(uuid.uuid4())
    resp = await client.post(BASE, json=_valid_payload(reporter_id=same, target_id=same))
    assert resp.status_code == 403, resp.text


# ── AC-015.4 — validation → 422 ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_missing_reporter_id_returns_422(client: AsyncClient) -> None:
    payload = {"target_id": TARGET, "reason": "spam"}
    resp = await client.post(BASE, json=payload)
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_missing_target_id_returns_422(client: AsyncClient) -> None:
    payload = {"reporter_id": REPORTER, "reason": "spam"}
    resp = await client.post(BASE, json=payload)
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_invalid_reason_returns_422(client: AsyncClient) -> None:
    payload = _valid_payload(reason="not_a_valid_reason")
    resp = await client.post(BASE, json=payload)
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_description_too_long_returns_422(client: AsyncClient) -> None:
    payload = _valid_payload(description="x" * 2001)
    resp = await client.post(BASE, json=payload)
    assert resp.status_code == 422, resp.text


# ── AC-015.5 — list endpoint ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_reports_empty(client: AsyncClient) -> None:
    resp = await client.get(BASE)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


@pytest.mark.asyncio
async def test_list_reports_after_create(client: AsyncClient) -> None:
    await client.post(BASE, json=_valid_payload())
    resp = await client.get(BASE)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1


@pytest.mark.asyncio
async def test_list_reports_pagination(client: AsyncClient) -> None:
    # Create 3 distinct reports
    ids = [str(uuid.uuid4()) for _ in range(3)]
    for tid in ids:
        await client.post(BASE, json=_valid_payload(reporter_id=REPORTER, target_id=tid))

    resp = await client.get(BASE, params={"limit": 2, "offset": 0})
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 2
    assert resp.json()["total"] == 3

    resp2 = await client.get(BASE, params={"limit": 2, "offset": 2})
    assert resp2.status_code == 200
    assert len(resp2.json()["items"]) == 1


# ── AC-015.6 — single-fetch + 404 ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_report_by_id(client: AsyncClient) -> None:
    create_resp = await client.post(BASE, json=_valid_payload())
    report_id = create_resp.json()["id"]

    resp = await client.get(f"{BASE}/{report_id}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] == report_id


@pytest.mark.asyncio
async def test_get_report_not_found_returns_404(client: AsyncClient) -> None:
    resp = await client.get(f"{BASE}/{uuid.uuid4()}")
    assert resp.status_code == 404, resp.text


# ── VER-002 — all valid reason enum values accepted ───────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "reason",
    ["spam", "harassment", "hate_speech", "misinformation", "violence", "other"],
)
async def test_all_reason_values_accepted(client: AsyncClient, reason: str) -> None:
    reporter = str(uuid.uuid4())
    target   = str(uuid.uuid4())
    resp = await client.post(BASE, json=_valid_payload(reporter_id=reporter, target_id=target, reason=reason))
    assert resp.status_code == 201, f"{reason}: {resp.text}"
    assert resp.json()["reason"] == reason

```