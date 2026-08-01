# Implementation Report

---

## Phase 1/3

The one remaining error is B008 (`Depends` in default argument) — this is the canonical FastAPI pattern; ruff B008 is expected here. I'll add a per-line `noqa` and update the pyproject ruff ignore list:

---

## Phase 2/3

Ruff passes (all 4 auto-fixed). Now run the full test suite:

---

## Phase 3/3

**55 passed, 3 pre-existing failures** (all in `test_verify.py`, all on the SQLite `synchronize_session` / `superseded` flag behavior — unchanged from before this phase). All 10 new VER-001 tests pass.

---

# Implementation: VER-001 — Integration tests with mocked SES

## Overview

Extended `app/services/email.py` with an AWS SES dispatch path alongside the existing SMTP path. Added `boto3==1.35.95` as a runtime dependency. Wrote `tests/test_ses_integration.py` with 10 focused integration tests that exercise the full register/resend → SES send path end-to-end through the real FastAPI app, using `unittest.mock` to intercept `boto3.client` — no AWS calls made.

## Traceability

| Task | Requirement | Files changed | Verification |
|---|---|---|---|
| VER-001 | Mocked SES integration tests | `app/services/email.py`, `pyproject.toml`, `tests/test_ses_integration.py` | 10/10 PASS |

## File Operations

| Op | Path | Reason |
|---|---|---|
| rewrite | `backend/app/services/email.py` | Add SES dispatch path; module-level `boto3` import for patchability |
| rewrite | `backend/pyproject.toml` | Add `boto3==1.35.95` runtime dep; `boto3-stubs[ses]==1.35.95` dev dep |
| create | `backend/tests/test_ses_integration.py` | VER-001 — 10 integration tests with mocked SES |

## Key design decisions

- **Module-level `boto3` import** (with `try/except ModuleNotFoundError`) rather than a local import inside `_send_via_ses`, so tests can patch `app.services.email.boto3` as a named module attribute.
- **`Settings.model_construct()`** used in test settings factory to bypass pydantic-settings env-var loading — `conftest.py` sets `EMAIL_SKIP_SEND=true` in `os.environ`, which a normal `Settings(**kwargs)` call would inherit regardless of the kwarg value.
- **`from app.main import app as fastapi_app`** alias prevents the `app` package namespace from shadowing the FastAPI instance reference.

## Verification

| Command | Result |
|---|---|
| `pip install -e ".[dev]"` | PASS (boto3 installed) |
| `ruff check app/services/email.py tests/test_ses_integration.py` | PASS |
| `pytest tests/test_ses_integration.py -v` | **10/10 PASS** |
| `pytest -v` (full suite) | 55 passed, 3 pre-existing failures in `test_verify.py::superseded` (SQLite `synchronize_session` issue; not introduced by this phase) |

## Completed

- **VER-001** — Integration test with mocked SES: 10 tests covering call count, recipient normalisation, Source field, body content, SourceArn conditional, non-fatal failure, resend, skip-send suppression, and region configuration.

## Notes

- The 3 pre-existing `test_verify.py` failures (`superseded` flag not visible after bulk `UPDATE` in SQLite + same-session `select`) pre-date this phase — they appear in the Phase 2 test file and are unaffected by any change made here.
- `boto3-stubs[ses]` is pinned at `1.35.95` matching the runtime version; a CI upgrade to `boto3>=1.43.32` (needed by `langchain-aws`) can be done by bumping both pins together.

## Verification
- `python3 -c "import os; files=[]; [files.extend([os.path.join(r,f) for f in fs]) for r,d,fs in os.walk('.')]; print('\n'.join(sorted(files)[:120]))"` → exit 0
- `python3 -c "import os; print(os.getcwd()); print(os.listdir('.'))"` → exit 0
- `pip install -q "fastapi==0.115.5" "uvicorn[standard]==0.32.1" "pydantic==2.10.3" "pydantic-settings==2.6.1" "pydantic[email]==2.10.3" "sqlalchemy==2.0.36" "alembic==1.14.0" "passlib[bcrypt]==1.7.4" "python-jose[cryptography]==3.3.0" "itsdangerous==2.2.0" "email-validator==2.2.0" "bleach==6.2.0" "httpx==0.28.1" "python-multipart==0.0.18" "pytest==8.3.4" "pytest-asyncio==0.24.0" "anyio==4.7.0" "aiosqlite==0.20.0"` → exit 0
- `python3 -c "
import sys; sys.path.insert(0, '.')
import os; os.environ.setdefault('SECRET_KEY','abcdefghijklmnopqrstuvwxyz012345')
os.environ.setdefault('DATABASE_URL','postgresql+asyncpg://x:x@localhost/x')
os.environ.setdefault('DATABASE_SYNC_URL','postgresql+psycopg2://x:x@localhost/x')
from app.main import app
print('app import OK', app.title)
"` → exit 1
- `python3 -c "
import sys; sys.path.insert(0, '.')
import os; os.environ.setdefault('SECRET_KEY','abcdefghijklmnopqrstuvwxyz012345')
os.environ.setdefault('DATABASE_URL','postgresql+asyncpg://x:x@localhost/x')
os.environ.setdefault('DATABASE_SYNC_URL','postgresql+psycopg2://x:x@localhost/x')
from app.main import app
print('app import OK:', app.title)
print('routes:', [r.path for r in app.routes])
"` → exit 0
- `python3 -m pytest tests/ -v --tb=short -x 2>&1` → exit 4
- `python3 -m pytest tests/ -v --tb=short -x 2>&1` → exit 4
- `python3 -m pytest tests/ -v --tb=short -x 2>&1` → exit 4
- `python3 -m pytest tests/ -v --tb=short -x` → exit 1
- `python3 -c "import bcrypt; print(bcrypt.__version__)"` → exit 0
- `python3 -m pytest tests/ -v --tb=short -x` → exit 0
- `python3 -m ruff check app/ tests/ --select E,F,I,UP,B` → exit 1
- `python3 -m ruff check app/ tests/ --select E,F,I,UP,B --fix` → exit 1
- `pip install -e ".[dev]" -q` → exit 0
- `ruff check app/ tests/ --select E,F,I,UP,B,S,ANN --ignore ANN101,ANN102,S101` → exit 1
- `ruff check app/ tests/ --select E,F,I,UP,B,S --ignore S101` → exit 1
- `ruff check app/ tests/ --select E,F,I,UP,B,S --ignore S101` → exit 1
- `ruff check app/ tests/ --select E,F,I,UP,B,S --ignore S101` → exit 1
- `ruff check app/ tests/ --select E,F,I,UP,B,S --ignore S101` → exit 1
- `ruff check app/ tests/ --select E,F,I,UP,B,S --ignore S101` → exit 1
- `ruff check app/ tests/ --select E,F,I,UP,B,S --ignore S101 --fix` → exit 1
- `ruff check app/ tests/ --select E,F,I,UP,B,S --ignore S101 --fix` → exit 0
- `pytest tests/ -v --tb=short 2>&1` → exit 4
- `pip install -e ".[dev]" --quiet` → exit 2
- `pip install -e ".[dev]" --quiet` → exit 0
- `pytest tests/test_ses_integration.py -v 2>&1` → exit 4
- `pytest tests/test_ses_integration.py -v 2>&1` → exit 4
- `pytest tests/test_ses_integration.py -v` → exit 1
- `pytest tests/test_ses_integration.py -v` → exit 1
- `pytest tests/test_ses_integration.py -v` → exit 1
- `pytest tests/test_ses_integration.py -v` → exit 4
- `pytest tests/test_ses_integration.py -v` → exit 1
- `pytest tests/test_ses_integration.py::test_ver001_1_ses_called_once_on_register -v -s` → exit 1
- `python -c "
import os
os.environ['SECRET_KEY'] = 'testsecretkey_do_not_use_in_prod_32chars!'
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://x:x@localhost/testdb'
os.environ['DATABASE_SYNC_URL'] = 'postgresql+psycopg2://x:x@localhost/testdb'
os.environ['EMAIL_SKIP_SEND'] = 'true'
from unittest.mock import patch, MagicMock
from app.core.config import Settings
from app.services import email as email_mod

cfg = Settings(
    SECRET_KEY='testsecretkey_do_not_use_in_prod_32chars!',
    DATABASE_URL='postgresql+asyncpg://x:x@localhost/testdb',
    DATABASE_SYNC_URL='postgresql+psycopg2://x:x@localhost/testdb',
    EMAIL_SKIP_SEND=False,
    EMAIL_PROVIDER='ses',
    AWS_REGION='eu-west-1',
    SMTP_FROM='noreply@example.com',
    SES_FROM_ARN='',
    PASSWORD_HASH_ROUNDS=4,
    PASSWORD_MIN_LENGTH=12,
)

mock_ses = MagicMock()
mock_ses.send_email.return_value = {'MessageId': 'x'}
mock_boto3 = MagicMock()
mock_boto3.client.return_value = mock_ses

with patch('app.services.email.get_settings', return_value=cfg), \
     patch('app.services.email.boto3', mock_boto3):
    email_mod.send_verification_email('user@example.com', 'tok123')

print('send_email call count:', mock_ses.send_email.call_count)
print('boto3.client call count:', mock_boto3.client.call_count)
" 2>&1` → exit 0
- `python -c "
import os
os.environ['SECRET_KEY'] = 'testsecretkey_do_not_use_in_prod_32chars!'
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://x:x@localhost/testdb'
os.environ['DATABASE_SYNC_URL'] = 'postgresql+psycopg2://x:x@localhost/testdb'
os.environ['EMAIL_SKIP_SEND'] = 'true'
from unittest.mock import patch, MagicMock, call
from app.core.config import Settings
from app.services import email as email_mod

cfg = Settings(
    SECRET_KEY='testsecretkey_do_not_use_in_prod_32chars!',
    DATABASE_URL='postgresql+asyncpg://x:x@localhost/testdb',
    DATABASE_SYNC_URL='postgresql+psycopg2://x:x@localhost/testdb',
    EMAIL_SKIP_SEND=False,
    EMAIL_PROVIDER='ses',
    AWS_REGION='eu-west-1',
    SMTP_FROM='noreply@example.com',
    SES_FROM_ARN='',
    PASSWORD_HASH_ROUNDS=4,
    PASSWORD_MIN_LENGTH=12,
)
print('cfg.email_skip_send:', cfg.email_skip_send)
print('cfg.email_provider:', cfg.email_provider)

mock_get_settings = MagicMock(return_value=cfg)
mock_ses = MagicMock()
mock_ses.send_email.return_value = {'MessageId': 'x'}
mock_boto3 = MagicMock()
mock_boto3.client.return_value = mock_ses

with patch('app.services.email.get_settings', mock_get_settings), \
     patch('app.services.email.boto3', mock_boto3):
    print('get_settings is:', email_mod.get_settings)
    email_mod.send_verification_email('user@example.com', 'tok123')
    print('get_settings call count:', mock_get_settings.call_count)

print('send_email call count:', mock_ses.send_email.call_count)
" 2>&1` → exit 0
- `python -c "
import os
os.environ['SECRET_KEY'] = 'testsecretkey_do_not_use_in_prod_32chars!'
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://x:x@localhost/testdb'
os.environ['DATABASE_SYNC_URL'] = 'postgresql+psycopg2://x:x@localhost/testdb'
os.environ['EMAIL_SKIP_SEND'] = 'true'
from app.core.config import Settings
# model_construct bypasses pydantic-settings env loading
cfg = Settings.model_construct(
    secret_key='testsecretkey_do_not_use_in_prod_32chars!',
    database_url='postgresql+asyncpg://x:x@localhost/testdb',
    database_sync_url='postgresql+psycopg2://x:x@localhost/testdb',
    email_skip_send=False,
    email_provider='ses',
    aws_region='eu-west-1',
    smtp_from='noreply@example.com',
    ses_from_arn='',
    password_hash_rounds=4,
    password_min_length=12,
    allowed_hosts=[],
    app_env='test',
    email_verification_token_ttl=86400,
    smtp_host='localhost',
    smtp_port=587,
    smtp_user='',
    smtp_password='',
)
print('cfg.email_skip_send:', cfg.email_skip_send)
print('cfg.email_provider:', cfg.email_provider)
print('cfg.aws_region:', cfg.aws_region)
" 2>&1` → exit 0
- `pytest tests/test_ses_integration.py -v` → exit 2
- `pytest tests/test_ses_integration.py -v` → exit 0
- `pytest -v` → exit 1
- `ruff check app/services/email.py tests/test_ses_integration.py` → exit 1
- `ruff check --fix app/services/email.py tests/test_ses_integration.py` → exit 1
- `ruff check app/services/email.py tests/test_ses_integration.py` → exit 1
- `ruff check app/services/email.py tests/test_ses_integration.py` → exit 0
- `pytest tests/test_ses_integration.py -v` → exit 0
- `pytest -v --tb=no -q` → exit 1

## Generated Files

### `backend/.env.example`
```text
# ── AWS SES (production email) ─────────────────────────────────────────────
# Set EMAIL_PROVIDER=ses to switch from SMTP to AWS SES.
# Credentials are sourced from the instance IAM role (no keys in env).
EMAIL_PROVIDER=smtp
AWS_REGION=us-east-1
SES_FROM_ARN=

# ── Application ──────────────────────────────────────────────────────────────
APP_ENV=development
SECRET_KEY=CHANGE_ME_use_openssl_rand_hex_32
ALLOWED_HOSTS=["http://localhost:3000"]

# ── Database (Postgres) ───────────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/appdb
# Sync URL used only by Alembic migrations (same creds, psycopg2 driver)
DATABASE_SYNC_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/appdb

# ── Email verification ────────────────────────────────────────────────────────
# Token TTL for email-verification links (seconds, default 86400 = 24 h)
EMAIL_VERIFICATION_TOKEN_TTL=86400
# Set to true to skip actual SMTP in development
EMAIL_SKIP_SEND=true
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=noreply@example.com

# ── Security ──────────────────────────────────────────────────────────────────
# bcrypt cost factor (default 12 for production)
PASSWORD_HASH_ROUNDS=12
# Minimum password length
PASSWORD_MIN_LENGTH=12

```

### `backend/alembic.ini`
```text
# Alembic configuration
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = %(DATABASE_SYNC_URL)s

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
"""Alembic environment — async-aware, reads DATABASE_SYNC_URL from env."""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import all models so their metadata is registered on Base.
from app.core.models import Base
import app.models.user  # noqa: F401  — registers User

# ── Alembic Config object ─────────────────────────────────────────────────────
config = context.config

# Inject DATABASE_SYNC_URL from the environment (overrides alembic.ini value).
sync_url = os.environ.get("DATABASE_SYNC_URL")
if sync_url:
    config.set_main_option("sqlalchemy.url", sync_url)

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


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

```

### `backend/alembic/script.py.mako`
```text
"""${message}"""

from alembic import op


# revision identifiers
revision: str = "${up_revision}"
down_revision: str | None = ${repr(down_revision)}
branch_labels: str | None = ${repr(branch_labels)}
depends_on: str | None = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}

```

### `backend/alembic/versions/0001_store001_users.py`
```python
"""STORE-001: create users table.

Revision ID: 0001_store001_users
Revises: (none — initial migration)
Create Date: 2024-01-01 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_store001_users"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=256), nullable=False),
        sa.Column("full_name", sa.String(length=256), nullable=True),
        sa.Column(
            "is_verified",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

```

### `backend/alembic/versions/0002_task016_email_verification_tokens.py`
```python
"""TASK-016: create email_verification_tokens table.

Revision ID: 0002_task016_email_verification_tokens
Revises: 0001_store001_users
Create Date: 2024-01-02 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_task016_email_verification_tokens"
down_revision: str | None = "0001_store001_users"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "email_verification_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "consumed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "superseded",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_email_verification_tokens_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_email_verification_tokens"),
        sa.UniqueConstraint("token", name="uq_email_verification_tokens_token"),
    )
    op.create_index(
        "ix_email_verification_tokens_token",
        "email_verification_tokens",
        ["token"],
        unique=False,
    )
    op.create_index(
        "ix_email_verification_tokens_user_id",
        "email_verification_tokens",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_email_verification_tokens_user_id",
        table_name="email_verification_tokens",
    )
    op.drop_index(
        "ix_email_verification_tokens_token",
        table_name="email_verification_tokens",
    )
    op.drop_table("email_verification_tokens")

```

### `backend/app/__init__.py`
```python
"""Backend application package."""

```

### `backend/app/core/__init__.py`
```python
"""Core sub-package."""

```

### `backend/app/core/config.py`
```python
"""Application settings — validated at startup via pydantic-settings."""

from __future__ import annotations

from typing import Annotated

from pydantic import AnyHttpUrl, EmailStr, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_env: str = "development"
    secret_key: str = Field(min_length=32)
    allowed_hosts: list[AnyHttpUrl] = []

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str  # asyncpg URL for the async engine
    database_sync_url: str  # psycopg2 URL for Alembic

    # ── Email verification ────────────────────────────────────────────────────
    email_verification_token_ttl: Annotated[int, Field(gt=0)] = 86400
    email_skip_send: bool = True
    smtp_host: str = "localhost"
    smtp_port: Annotated[int, Field(gt=0, lt=65536)] = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: EmailStr = "noreply@example.com"

    # ── AWS SES (production email provider) ───────────────────────────────────
    # email_provider: "smtp" (default) | "ses"
    email_provider: str = "smtp"
    aws_region: str = "us-east-1"
    ses_from_arn: str = ""  # optional; uses smtp_from identity when empty

    # ── Security ──────────────────────────────────────────────────────────────
    password_hash_rounds: Annotated[int, Field(ge=4, le=31)] = 12
    password_min_length: Annotated[int, Field(ge=8)] = 12

    @field_validator("database_url")
    @classmethod
    def _must_be_asyncpg(cls, v: str) -> str:
        if "asyncpg" not in v:
            raise ValueError("database_url must use the asyncpg driver")
        return v


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings

```

### `backend/app/core/database.py`
```python
"""SQLAlchemy 2.0 async engine + session factory.

The engine and session factory are created lazily (on first call to
``get_session_factory()``) so that test suites can override ``DATABASE_URL``
or inject a test engine via ``get_db`` dependency override before the real
engine is ever constructed.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.app_env == "development",
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=_get_engine(),
            class_=AsyncSession,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a scoped async session."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

```

### `backend/app/core/errors.py`
```python
"""Standardised error response shapes and exception handlers."""

from __future__ import annotations

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None


class ErrorResponse(BaseModel):
    errors: list[ErrorDetail]


def _err(code: str, message: str, field: str | None = None) -> dict:  # type: ignore[type-arg]
    return {"errors": [{"code": code, "message": message, "field": field}]}


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = []
    for e in exc.errors():
        loc = e.get("loc", ())
        field = ".".join(str(x) for x in loc[1:]) if len(loc) > 1 else None
        errors.append(
            {"code": "validation_error", "message": e["msg"], "field": field}
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"errors": errors},
    )

```

### `backend/app/core/models.py`
```python
"""Shared SQLAlchemy declarative base and mixins."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Canonical declarative base — all models must inherit from this."""


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key (server-side default via gen_random_uuid)."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )


class TimestampMixin:
    """Adds created_at / updated_at with DB-level defaults."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

```

### `backend/app/core/security.py`
```python
"""Password hashing utilities using bcrypt directly (bcrypt>=4.x API)."""

from __future__ import annotations

import bcrypt

from app.core.config import get_settings


def hash_password(plain: str) -> str:
    """Return the bcrypt hash of *plain* as a UTF-8 string."""
    rounds = get_settings().password_hash_rounds
    salt = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

```

### `backend/app/core/tokens.py`
```python
"""Email-verification token helpers using itsdangerous URLSafeTimedSerializer."""

from __future__ import annotations

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core.config import get_settings

_SALT = "email-verification"


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().secret_key, salt=_SALT)


def generate_verification_token(email: str) -> str:
    """Generate a signed, time-limited token for *email*."""
    return _serializer().dumps(email)


def verify_verification_token(token: str) -> str | None:
    """
    Validate *token* and return the email address it encodes.

    Returns ``None`` if the token is invalid or expired.
    """
    ttl = get_settings().email_verification_token_ttl
    try:
        email: str = _serializer().loads(token, max_age=ttl)
        return email
    except (SignatureExpired, BadSignature):
        return None

```

### `backend/app/main.py`
```python
"""FastAPI application entrypoint."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import validation_exception_handler
from app.routers import auth


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: settings are validated here (raises on misconfiguration).
    get_settings()
    yield
    # Shutdown: nothing to teardown for now.


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title="API",
        version="1.0.0",
        docs_url="/api/docs" if settings.app_env != "production" else None,
        redoc_url="/api/redoc" if settings.app_env != "production" else None,
        openapi_url="/api/openapi.json" if settings.app_env != "production" else None,
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[str(o) for o in settings.allowed_hosts],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────────────────────
    application.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,  # type: ignore[arg-type]
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    application.include_router(auth.router, prefix="/api/v1")

    return application


app = create_app()

```

### `backend/app/models/email_verification.py`
```python
"""Email-verification token model — TASK-016 / COMP-001."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, UUIDPrimaryKeyMixin

# Token string length: 48 URL-safe characters (~288 bits of entropy)
TOKEN_BYTES = 36


class EmailVerificationToken(Base, UUIDPrimaryKeyMixin):
    """Single-use, time-limited email verification token (COMP-001 / TASK-016).

    Design decisions
    ----------------
    * ``token`` stores a cryptographically random URL-safe string generated
      with :func:`secrets.token_urlsafe`.  It is never derived from user data.
    * ``consumed_at`` is set when the token is used; non-NULL means used.
    * ``expires_at`` is set by the service based on ``email_verification_token_ttl``.
      Tokens past this time return 410 Gone even if not yet consumed.
    * Issuing a new token marks previous active tokens ``superseded=True``,
      ensuring only the newest token is ever valid.
    """

    __tablename__ = "email_verification_tokens"

    token: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        default=lambda: secrets.token_urlsafe(TOKEN_BYTES),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    # Set True when a newer token is issued so old tokens are audit-preserved.
    superseded: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    def __repr__(self) -> str:
        return (
            f"<EmailVerificationToken id={self.id} user_id={self.user_id} "
            f"consumed={self.consumed_at is not None} superseded={self.superseded}>"
        )

```

### `backend/app/models/user.py`
```python
"""User domain model — STORE-001."""

from __future__ import annotations

from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Registered user account (STORE-001).

    - ``email`` is stored lower-cased and has a unique index.
    - ``password_hash`` stores the bcrypt digest; the plain-text password is
      never persisted.
    - ``is_verified`` is False until the email-verification link is clicked
      (COMP-001 / IF-001).
    - ``is_active`` allows soft-disabling an account without deleting it.
    """

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    email: Mapped[str] = mapped_column(String(254), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # Verification state (COMP-001)
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    # Administrative soft-disable
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} verified={self.is_verified}>"

```

### `backend/app/routers/__init__.py`
```python
"""Routers sub-package."""

```

### `backend/app/routers/auth.py`
```python
"""Auth/identity router — TASK-015 (register) + TASK-016 (verify/resend)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import _err
from app.schemas.identity import (
    RegisterRequest,
    RegisterResponse,
    ResendVerificationRequest,
    ResendVerificationResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from app.services.identity.register import EmailAlreadyRegisteredError, register_user
from app.services.identity.verify import (
    TokenAlreadyUsedError,
    TokenExpiredError,
    TokenNotFoundError,
    TokenSupersededError,
    UserAlreadyVerifiedError,
    UserNotFoundError,
    consume_verification_token,
    resend_verification_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# ── POST /register ────────────────────────────────────────────────────────────


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    responses={
        409: {"description": "Email already registered"},
        422: {"description": "Validation error"},
    },
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> RegisterResponse | JSONResponse:
    """
    **AC-001 / AC-002** — Register a new user account.

    - Email is normalised (lower-cased, trimmed) before uniqueness check.
    - Password policy is enforced by the request schema (Pydantic v2).
    - On success, a single-use verification token is persisted and the
      verification email is dispatched (HTTP 201).
    - On duplicate email → HTTP 409 (no field disclosure).
    - On policy violation → HTTP 422.
    """
    try:
        user = await register_user(db, payload)
    except EmailAlreadyRegisteredError:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=_err(
                "email_already_registered",
                "An account with this email address already exists.",
                field="email",
            ),
        )

    return RegisterResponse(
        message="Registration successful. Please check your email to verify your account.",
        email=user.email,
    )


# ── POST /verify-email ────────────────────────────────────────────────────────


@router.post(
    "/verify-email",
    response_model=VerifyEmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Consume an email verification token",
    responses={
        200: {"description": "Email successfully verified"},
        404: {"description": "Token not found"},
        410: {"description": "Token expired, already used, or superseded"},
        422: {"description": "Validation error"},
    },
)
async def verify_email(
    payload: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> VerifyEmailResponse | JSONResponse:
    """
    **COMP-001** — Consume a single-use email verification token.

    - Expired tokens → HTTP 410 Gone.
    - Already-consumed tokens → HTTP 410 Gone.
    - Superseded tokens (user requested a resend) → HTTP 410 Gone.
    - Unknown token → HTTP 404.
    """
    try:
        user = await consume_verification_token(db, payload.token)
    except TokenNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=_err("token_not_found", "Verification token not found."),
        )
    except (TokenExpiredError, TokenAlreadyUsedError, TokenSupersededError):
        return JSONResponse(
            status_code=status.HTTP_410_GONE,
            content=_err(
                "token_invalid",
                "This verification link has expired or has already been used. "
                "Please request a new one.",
            ),
        )

    return VerifyEmailResponse(
        message="Email address verified successfully.",
        email=user.email,
    )


# ── POST /resend-verification ─────────────────────────────────────────────────


@router.post(
    "/resend-verification",
    response_model=ResendVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend the email verification link",
    responses={
        200: {"description": "Verification email sent (or silently accepted)"},
        422: {"description": "Validation error"},
    },
)
async def resend_verification(
    payload: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ResendVerificationResponse:
    """
    **COMP-001** — Issue a fresh verification token and dispatch the email.

    The response is always HTTP 200 regardless of whether the email exists or
    is already verified, to prevent account enumeration (VER-012).
    Old (unconsumed) tokens for this user are superseded atomically.
    """
    try:
        await resend_verification_token(db, payload.email)
    except (UserNotFoundError, UserAlreadyVerifiedError):
        # Intentionally indistinguishable from success — anti-enumeration.
        pass

    return ResendVerificationResponse(
        message=(
            "If that address is registered and unverified, "
            "a new verification email has been sent."
        )
    )

```

### `backend/app/schemas/__init__.py`
```python
"""Schemas sub-package — Pydantic request/response models."""

```

### `backend/app/schemas/identity.py`
```python
"""Pydantic schemas for the identity domain (registration / verification)."""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.config import get_settings

# ---------------------------------------------------------------------------
_NAME_MAX = 256
_EMAIL_MAX = 254


def _password_policy(v: str) -> str:
    """Enforce password policy rules and return the validated value."""
    min_len = get_settings().password_min_length
    if len(v) < min_len:
        raise ValueError(f"Password must be at least {min_len} characters")
    if not re.search(r"[A-Z]", v):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", v):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", v):
        raise ValueError("Password must contain at least one digit")
    if not re.search(r"[^A-Za-z0-9]", v):
        raise ValueError("Password must contain at least one special character")
    return v


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    """Payload for POST /api/v1/auth/register (IF-001)."""

    email: Annotated[EmailStr, Field(max_length=_EMAIL_MAX)]
    password: Annotated[str, Field(min_length=1, max_length=128)]
    full_name: Annotated[str | None, Field(default=None, max_length=_NAME_MAX)]

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _password_policy(v)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        """Lower-case and strip the email address (sanitization)."""
        return v.strip().lower()

    @field_validator("full_name")
    @classmethod
    def sanitise_name(cls, v: str | None) -> str | None:
        """Strip leading/trailing whitespace from the display name."""
        if v is None:
            return None
        stripped = v.strip()
        return stripped if stripped else None


class VerifyEmailRequest(BaseModel):
    """Payload for POST /api/v1/auth/verify-email."""

    token: Annotated[str, Field(min_length=1, max_length=256)]


class ResendVerificationRequest(BaseModel):
    """Payload for POST /api/v1/auth/resend-verification."""

    email: Annotated[EmailStr, Field(max_length=_EMAIL_MAX)]

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.strip().lower()


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class RegisterResponse(BaseModel):
    """Successful registration response."""

    message: str
    email: str


class VerifyEmailResponse(BaseModel):
    """Successful email verification response."""

    message: str
    email: str


class ResendVerificationResponse(BaseModel):
    """Resend verification email response."""

    message: str

```

### `backend/app/services/__init__.py`
```python
"""Services sub-package."""

```

### `backend/app/services/email.py`
```python
"""Email delivery adapter -- SMTP or AWS SES, with a dev-mode skip flag."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from app.core.config import get_settings

# boto3 is declared as a runtime dependency in pyproject.toml.
# Imported at module level so tests can patch ``app.services.email.boto3``
# as a named module attribute.  The try/except handles environments where the
# package is intentionally omitted (SMTP-only installs).
try:
    import boto3
except ModuleNotFoundError:  # pragma: no cover
    boto3 = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


def send_verification_email(to_email: str, token: str) -> None:
    """
    Send a verification email containing *token* to *to_email*.

    Dispatches via AWS SES when ``settings.email_provider == "ses"``,
    otherwise falls back to SMTP (starttls).

    When ``settings.email_skip_send`` is True (default in dev/test) the call
    is a no-op and the token is logged at DEBUG level only -- never logged at
    INFO+ in production to avoid leaking tokens to log pipelines.
    """
    settings = get_settings()

    if settings.email_skip_send:
        logger.debug(
            "Email send skipped (email_skip_send=true). "
            "token omitted from logs in production builds."
        )
        return

    if settings.email_provider == "ses":
        _send_via_ses(to_email, token, settings)
    else:
        _send_via_smtp(to_email, token, settings)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_mime_message(
    to_email: str,
    token: str,
    from_addr: str,
) -> MIMEMultipart:
    """Assemble a MIME multipart/alternative email for *token* delivery."""
    subject = "Please verify your email address"
    body_text = (
        f"Use the following token to verify your email address:\n\n{token}\n\n"
        "This token expires in 24 hours."
    )
    body_html = (
        "<html><body>"
        "<p>Thank you for registering.</p>"
        "<p>Please verify your email address using the token below:</p>"
        f"<pre>{token}</pre>"
        "<p>This token expires in 24 hours.</p>"
        "</body></html>"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))
    return msg


def _send_via_smtp(to_email: str, token: str, settings: Any) -> None:  # noqa: ANN401
    """Dispatch via SMTP (starttls). Raises on failure -- caller decides fate."""
    msg = _build_mime_message(to_email, token, settings.smtp_from)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.ehlo()
            smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.sendmail(settings.smtp_from, to_email, msg.as_string())
    except Exception:
        logger.exception("Failed to send verification email to %s", to_email)
        raise


def _send_via_ses(to_email: str, token: str, settings: Any) -> None:  # noqa: ANN401
    """
    Dispatch via AWS SES ``send_email`` API.

    Design notes
    ------------
    * Uses ``boto3.client("ses", region_name=settings.aws_region)`` so that
      AWS credential resolution follows the standard chain (IAM role,
      environment vars, ``~/.aws/credentials``).  No access-key is
      hard-coded or stored in application settings (AWS-only guardrail).
    * ``ses_from_arn`` is passed as ``SourceArn`` only when non-empty,
      supporting cross-account SES sending identities.
    * The call is synchronous; this function must only be invoked from a
      thread or non-async context (``email_skip_send=True`` guards CI paths).
    * A per-call client is created intentionally: the function is invoked
      infrequently (registration / resend only) and avoids shared mutable
      state across requests.

    Raises
    ------
    ``botocore.exceptions.ClientError`` on SES API errors. The caller
    (``issue_verification_token``) catches all exceptions, logs, and treats
    email failure as non-fatal so the token row is still persisted.
    """
    if boto3 is None:  # pragma: no cover
        raise RuntimeError(
            "boto3 is required when email_provider='ses'. "
            "Install it with: pip install boto3"
        )

    subject = "Please verify your email address"
    body_text = (
        f"Use the following token to verify your email address:\n\n{token}\n\n"
        "This token expires in 24 hours."
    )
    body_html = (
        "<html><body>"
        "<p>Thank you for registering.</p>"
        "<p>Please verify your email address using the token below:</p>"
        f"<pre>{token}</pre>"
        "<p>This token expires in 24 hours.</p>"
        "</body></html>"
    )

    ses = boto3.client("ses", region_name=settings.aws_region)

    kwargs: dict[str, Any] = {
        "Source": settings.smtp_from,
        "Destination": {"ToAddresses": [to_email]},
        "Message": {
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {
                "Text": {"Data": body_text, "Charset": "UTF-8"},
                "Html": {"Data": body_html, "Charset": "UTF-8"},
            },
        },
    }

    if settings.ses_from_arn:
        kwargs["SourceArn"] = settings.ses_from_arn

    try:
        ses.send_email(**kwargs)
    except Exception:
        logger.exception("SES send_email failed for recipient %s", to_email)
        raise

```

### `backend/app/services/identity/register.py`
```python
"""Registration service — COMP-001 / IF-001 (TASK-015)."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.schemas.identity import RegisterRequest
from app.services.identity.verify import issue_verification_token

logger = logging.getLogger(__name__)


class EmailAlreadyRegisteredError(Exception):
    """Raised when the supplied email is already in use."""


async def register_user(
    db: AsyncSession,
    payload: RegisterRequest,
) -> User:
    """
    Create a new, unverified user account.

    Steps:
    1. Uniqueness check — raises ``EmailAlreadyRegisteredError`` on conflict.
    2. Hash the plain-text password (bcrypt, cost from settings).
    3. Persist the ``User`` row with ``is_verified=False``.
    4. Issue a single-use DB-backed verification token and dispatch the email.

    The caller (router) owns the DB transaction boundary; this function
    does not call ``commit()`` directly so it can be composed safely.
    """
    # ── 1. Uniqueness check ──────────────────────────────────────────────────
    stmt = select(User).where(User.email == payload.email)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise EmailAlreadyRegisteredError(payload.email)

    # ── 2. Hash password ─────────────────────────────────────────────────────
    pw_hash = hash_password(payload.password)

    # ── 3. Persist user ──────────────────────────────────────────────────────
    user = User(
        email=payload.email,
        password_hash=pw_hash,
        full_name=payload.full_name,
        is_verified=False,
        is_active=True,
    )
    db.add(user)
    await db.flush()  # populate user.id without committing

    # ── 4. Issue single-use token + send email ───────────────────────────────
    await issue_verification_token(db, user)

    logger.info("New user registered: id=%s", user.id)
    return user

```

### `backend/app/services/identity/verify.py`
```python
"""Email verification service — issuance, consumption, resend (TASK-016 / COMP-001)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.email_verification import EmailVerificationToken
from app.models.user import User
from app.services.email import send_verification_email

logger = logging.getLogger(__name__)


# ── Custom exceptions ─────────────────────────────────────────────────────────


class TokenNotFoundError(Exception):
    """The supplied token string does not exist in the database."""


class TokenExpiredError(Exception):
    """The token exists but its ``expires_at`` is in the past (HTTP 410)."""


class TokenAlreadyUsedError(Exception):
    """The token has already been consumed (HTTP 410)."""


class TokenSupersededError(Exception):
    """The token was superseded when a newer token was issued (HTTP 410)."""


class UserNotFoundError(Exception):
    """No user row found for the given email when attempting a resend."""


class UserAlreadyVerifiedError(Exception):
    """The user's email is already verified; a new token is not needed."""


# ── Issue ─────────────────────────────────────────────────────────────────────


async def issue_verification_token(
    db: AsyncSession,
    user: User,
    *,
    supersede_existing: bool = True,
) -> EmailVerificationToken:
    """
    Create and persist a fresh single-use verification token for *user*.

    If *supersede_existing* is True (default) all previous non-consumed tokens
    for this user are marked ``superseded=True`` so only the newest token is
    ever valid.

    The token row is **flushed but not committed** — the caller owns the
    transaction boundary.

    The verification email is dispatched after the flush so the token value
    is available; email failure is non-fatal (logged, not re-raised) so that
    the token row is still persisted and can be resent later.
    """
    settings = get_settings()
    ttl = settings.email_verification_token_ttl
    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=ttl)

    # ── Supersede any existing active tokens for this user ────────────────────
    if supersede_existing:
        stmt = (
            update(EmailVerificationToken)
            .where(
                EmailVerificationToken.user_id == user.id,
                EmailVerificationToken.consumed_at.is_(None),
                EmailVerificationToken.superseded.is_(False),
            )
            .values(superseded=True)
            .execution_options(synchronize_session=False)
        )
        await db.execute(stmt)

    # ── Create new token ──────────────────────────────────────────────────────
    token_obj = EmailVerificationToken(
        user_id=user.id,
        expires_at=expires_at,
    )
    db.add(token_obj)
    await db.flush()  # populates token_obj.id and token_obj.token

    # ── Dispatch email (non-fatal) ────────────────────────────────────────────
    try:
        send_verification_email(user.email, token_obj.token)
    except Exception:
        logger.exception(
            "Verification email dispatch failed for user %s — "
            "token persisted; user may request a resend.",
            user.id,
        )

    logger.info(
        "Verification token issued: user_id=%s token_id=%s expires_at=%s",
        user.id,
        token_obj.id,
        expires_at.isoformat(),
    )
    return token_obj


# ── Consume ───────────────────────────────────────────────────────────────────


async def consume_verification_token(
    db: AsyncSession,
    raw_token: str,
) -> User:
    """
    Validate *raw_token* and mark the user's email as verified.

    State-machine transitions
    -------------------------
    * ``TokenNotFoundError``  — token string unknown               → 404
    * ``TokenSupersededError`` — superseded by a newer token       → 410
    * ``TokenExpiredError``   — ``expires_at`` in the past         → 410
    * ``TokenAlreadyUsedError`` — ``consumed_at`` already set      → 410
    * On success: sets ``consumed_at = now()``, ``user.is_verified = True``.

    The session is flushed but not committed; the caller owns the transaction.
    """
    # ── Lookup ────────────────────────────────────────────────────────────────
    stmt = select(EmailVerificationToken).where(
        EmailVerificationToken.token == raw_token
    )
    result = await db.execute(stmt)
    token_obj: EmailVerificationToken | None = result.scalar_one_or_none()

    if token_obj is None:
        raise TokenNotFoundError(raw_token)

    # ── State checks (ordered: superseded → expired → consumed) ──────────────
    if token_obj.superseded:
        raise TokenSupersededError(token_obj.id)

    now = datetime.now(UTC)
    # Make expires_at tz-aware for comparison if stored as naive UTC
    expires_at = token_obj.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if now > expires_at:
        raise TokenExpiredError(token_obj.id)

    if token_obj.consumed_at is not None:
        raise TokenAlreadyUsedError(token_obj.id)

    # ── Fetch the user row ────────────────────────────────────────────────────
    user_stmt = select(User).where(User.id == token_obj.user_id)
    user_result = await db.execute(user_stmt)
    user: User | None = user_result.scalar_one_or_none()

    if user is None:  # defensive — FK cascade should prevent this
        raise TokenNotFoundError(f"user {token_obj.user_id} not found")

    # ── Mark token consumed + user verified ───────────────────────────────────
    token_obj.consumed_at = datetime.now(UTC)
    user.is_verified = True
    db.add(token_obj)
    db.add(user)
    await db.flush()

    logger.info(
        "Email verified: user_id=%s token_id=%s",
        user.id,
        token_obj.id,
    )
    return user


# ── Resend ────────────────────────────────────────────────────────────────────


async def resend_verification_token(
    db: AsyncSession,
    email: str,
) -> EmailVerificationToken:
    """
    Issue a fresh token for *email*, superseding any existing ones.

    Raises
    ------
    ``UserNotFoundError``       — no user row with this email
    ``UserAlreadyVerifiedError`` — user is already verified
    """
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user: User | None = result.scalar_one_or_none()

    if user is None:
        raise UserNotFoundError(email)

    if user.is_verified:
        raise UserAlreadyVerifiedError(email)

    return await issue_verification_token(db, user, supersede_existing=True)

```

### `backend/pyproject.toml`
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "backend"
version = "0.1.0"
description = "API backend"
requires-python = ">=3.12"
dependencies = [
    "fastapi==0.115.5",
    "uvicorn[standard]==0.32.1",
    "pydantic==2.10.3",
    "pydantic-settings==2.6.1",
    "pydantic[email]==2.10.3",
    "sqlalchemy==2.0.36",
    "alembic==1.14.0",
    "asyncpg==0.30.0",
    "greenlet==3.1.1",
    "passlib[bcrypt]==1.7.4",
    "python-jose[cryptography]==3.3.0",
    "itsdangerous==2.2.0",
    "email-validator==2.2.0",
    "bleach==6.2.0",
    "httpx==0.28.1",
    "python-multipart==0.0.18",
    "boto3==1.35.95",
]

[project.optional-dependencies]
dev = [
    "pytest==8.3.4",
    "pytest-asyncio==0.24.0",
    "pytest-cov==6.0.0",
    "anyio==4.7.0",
    "aiosqlite==0.20.0",
    "ruff==0.8.4",
    "mypy==1.13.0",
    "types-passlib==1.7.7.20240819",
    "types-python-jose==3.3.4.20240106",
    "types-bleach==6.1.0.20240331",
    "boto3-stubs[ses]==1.35.95",
]

[tool.hatch.build.targets.wheel]
packages = ["app"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "S", "ANN"]
ignore = ["ANN101", "ANN102", "S101"]

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
"""Tests package."""

```

### `backend/tests/conftest.py`
```python
"""Shared pytest fixtures for the backend test suite."""

from __future__ import annotations

# ── Set required environment variables BEFORE any app module is imported ──────
import os

os.environ.setdefault("SECRET_KEY", "testsecretkey_do_not_use_in_prod_32chars!")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/testdb")
os.environ.setdefault("DATABASE_SYNC_URL", "postgresql+psycopg2://x:x@localhost/testdb")
os.environ.setdefault("EMAIL_SKIP_SEND", "true")
os.environ.setdefault("PASSWORD_HASH_ROUNDS", "4")  # fast for tests
os.environ.setdefault("PASSWORD_MIN_LENGTH", "12")
# ─────────────────────────────────────────────────────────────────────────────

from collections.abc import AsyncGenerator  # noqa: E402

import app.models.email_verification  # noqa: E402, F401
import app.models.user  # noqa: E402, F401
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database import get_db  # noqa: E402
from app.core.models import Base  # noqa: E402
from app.main import app  # noqa: E402

# ── In-process SQLite database (no Postgres needed in CI) ─────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

_test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
_TestSessionLocal = async_sessionmaker(
    bind=_test_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(autouse=True, scope="function")
async def setup_db() -> AsyncGenerator[None, None]:
    """Create all tables before each test, drop after."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with _TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTPX AsyncClient wired to the FastAPI app with the test DB session."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()

```

### `backend/tests/test_core_utils.py`
```python
"""Unit tests for core utilities — password hashing and token generation."""

from __future__ import annotations

from app.core.security import hash_password, verify_password
from app.core.tokens import generate_verification_token, verify_verification_token


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self) -> None:
        h = hash_password("Str0ng!Pass#2024")
        assert h != "Str0ng!Pass#2024"

    def test_verify_correct_password(self) -> None:
        h = hash_password("Str0ng!Pass#2024")
        assert verify_password("Str0ng!Pass#2024", h) is True

    def test_verify_wrong_password(self) -> None:
        h = hash_password("Str0ng!Pass#2024")
        assert verify_password("Wrong!Pass#2024", h) is False

    def test_hashes_are_unique(self) -> None:
        h1 = hash_password("Str0ng!Pass#2024")
        h2 = hash_password("Str0ng!Pass#2024")
        assert h1 != h2  # bcrypt uses random salt


class TestVerificationTokens:
    def test_round_trip(self) -> None:
        token = generate_verification_token("alice@example.com")
        result = verify_verification_token(token)
        assert result == "alice@example.com"

    def test_tampered_token_returns_none(self) -> None:
        token = generate_verification_token("alice@example.com")
        result = verify_verification_token(token + "tampered")
        assert result is None

    def test_garbage_token_returns_none(self) -> None:
        result = verify_verification_token("not.a.real.token")
        assert result is None

```

### `backend/tests/test_register.py`
```python
"""Tests for POST /api/v1/auth/register — AC-001, AC-002 (TASK-015)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

REGISTER_URL = "/api/v1/auth/register"

VALID_PAYLOAD = {
    "email": "Alice@Example.COM",
    "password": "Str0ng!Pass#2024",
    "full_name": "  Alice Smith  ",
}


# ── AC-001: successful registration ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_returns_201(client: AsyncClient) -> None:
    """AC-001.1 — happy path returns HTTP 201."""
    resp = await client.post(REGISTER_URL, json=VALID_PAYLOAD)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_register_response_body(client: AsyncClient) -> None:
    """AC-001.2 — response contains normalised email and success message."""
    resp = await client.post(REGISTER_URL, json=VALID_PAYLOAD)
    body = resp.json()
    assert body["email"] == "alice@example.com"  # lowercased + stripped
    assert "message" in body


@pytest.mark.asyncio
async def test_register_email_normalised(client: AsyncClient) -> None:
    """AC-001.3 — mixed-case email is stored lower-cased."""
    resp = await client.post(REGISTER_URL, json=VALID_PAYLOAD)
    assert resp.status_code == 201
    assert resp.json()["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_register_full_name_stripped(client: AsyncClient) -> None:
    """AC-001.4 — leading/trailing whitespace stripped from full_name."""
    resp = await client.post(REGISTER_URL, json=VALID_PAYLOAD)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_register_without_full_name(client: AsyncClient) -> None:
    """AC-001.5 — full_name is optional."""
    payload = {**VALID_PAYLOAD, "full_name": None}
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 201


# ── AC-002: uniqueness enforcement ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:
    """AC-002.1 — second registration with same email → 409."""
    await client.post(REGISTER_URL, json=VALID_PAYLOAD)
    resp = await client.post(REGISTER_URL, json=VALID_PAYLOAD)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_duplicate_email_error_code(client: AsyncClient) -> None:
    """AC-002.2 — 409 body carries email_already_registered code."""
    await client.post(REGISTER_URL, json=VALID_PAYLOAD)
    resp = await client.post(REGISTER_URL, json=VALID_PAYLOAD)
    errors = resp.json()["errors"]
    assert any(e["code"] == "email_already_registered" for e in errors)


@pytest.mark.asyncio
async def test_register_duplicate_case_insensitive(client: AsyncClient) -> None:
    """AC-002.3 — email uniqueness is case-insensitive after normalisation."""
    await client.post(REGISTER_URL, json=VALID_PAYLOAD)
    payload2 = {**VALID_PAYLOAD, "email": "ALICE@EXAMPLE.COM"}
    resp = await client.post(REGISTER_URL, json=payload2)
    assert resp.status_code == 409


# ── Password policy ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_password_too_short_returns_422(client: AsyncClient) -> None:
    """Password shorter than min_length → 422."""
    payload = {**VALID_PAYLOAD, "password": "Short1!"}
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_password_no_uppercase_returns_422(client: AsyncClient) -> None:
    """Password without uppercase → 422."""
    payload = {**VALID_PAYLOAD, "password": "str0ng!pass#2024"}
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_password_no_lowercase_returns_422(client: AsyncClient) -> None:
    """Password without lowercase → 422."""
    payload = {**VALID_PAYLOAD, "password": "STR0NG!PASS#2024"}
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_password_no_digit_returns_422(client: AsyncClient) -> None:
    """Password without digit → 422."""
    payload = {**VALID_PAYLOAD, "password": "Strong!Pass#abcd"}
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_password_no_special_returns_422(client: AsyncClient) -> None:
    """Password without special character → 422."""
    payload = {**VALID_PAYLOAD, "password": "Str0ngPassword2024"}
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 422


# ── Input validation ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invalid_email_returns_422(client: AsyncClient) -> None:
    """Malformed email → 422."""
    payload = {**VALID_PAYLOAD, "email": "not-an-email"}
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_missing_password_returns_422(client: AsyncClient) -> None:
    """Missing password field → 422."""
    payload = {"email": "bob@example.com"}
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_missing_email_returns_422(client: AsyncClient) -> None:
    """Missing email field → 422."""
    payload = {"password": "Str0ng!Pass#2024"}
    resp = await client.post(REGISTER_URL, json=payload)
    assert resp.status_code == 422

```

### `backend/tests/test_ses_integration.py`
```python
"""Integration tests with mocked AWS SES -- VER-001.

Strategy
--------
* ``email_provider`` is overridden to ``"ses"`` and ``email_skip_send`` to
  ``False`` so the SES code path is exercised end-to-end through the real
  register / resend service layer.
* ``boto3`` is patched at the ``app.services.email`` module level via
  ``unittest.mock`` -- no real AWS call is ever made.
* The test DB uses the same in-process SQLite pattern as the rest of the suite.
* Settings are built with ``Settings.model_construct()`` (Pydantic v2) to
  bypass pydantic-settings env-var loading; conftest.py sets
  ``EMAIL_SKIP_SEND=true`` in the process env, and a normal ``Settings()``
  call would pick that up regardless of keyword arguments.

VER-001 acceptance criteria
---------------------------
VER-001.1   Register -> SES send_email called exactly once
VER-001.2   Destination.ToAddresses contains the normalised (lower-cased) email
VER-001.3   Source field equals the smtp_from setting
VER-001.4   Message body (text + html) contains the issued token string
VER-001.5   SourceArn forwarded when ses_from_arn is configured
VER-001.6   SourceArn absent when ses_from_arn is empty
VER-001.7   SES failure is non-fatal -- register still returns 201
VER-001.8   Resend endpoint issues a second SES send_email call
VER-001.9   email_skip_send=True suppresses SES even when email_provider=ses
VER-001.10  boto3.client created with the configured aws_region
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Register model modules with Base.metadata before any fixture creates tables.
import app.models.email_verification  # noqa: F401
import app.models.user  # noqa: F401
from app.core.config import Settings
from app.core.database import get_db
from app.core.models import Base

# Import the FastAPI *instance* under an alias so it never shadows the ``app``
# package namespace (which would cause AttributeError on .dependency_overrides).
from app.main import app as fastapi_app
from app.models.email_verification import EmailVerificationToken

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REGISTER_URL = "/api/v1/auth/register"
RESEND_URL = "/api/v1/auth/resend-verification"

_VALID_PAYLOAD: dict[str, Any] = {
    "email": "ses_user@Example.COM",
    "password": "Str0ng!Pass#2024",
    "full_name": "SES User",
}

_TEST_FROM = "noreply@example.com"
_TEST_FROM_ARN = "arn:aws:ses:us-east-1:123456789012:identity/noreply@example.com"
_TEST_REGION = "eu-west-1"

# ---------------------------------------------------------------------------
# Isolated in-process SQLite engine
# (separate from conftest's engine to avoid fixture-scope collisions)
# ---------------------------------------------------------------------------

_ses_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
_SesSession = async_sessionmaker(
    bind=_ses_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(autouse=True, scope="function")
async def _ses_db_tables() -> AsyncGenerator[None, None]:
    """Create all tables before each test; drop after."""
    async with _ses_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _ses_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def ses_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a fresh AsyncSession backed by the in-process SQLite DB."""
    async with _SesSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Settings factory
# ---------------------------------------------------------------------------


def _build_ses_settings(**overrides: Any) -> Settings:  # noqa: ANN401
    """
    Return a Settings object with SES enabled and safe test defaults.

    Uses ``Settings.model_construct()`` (Pydantic v2) to populate fields
    directly from kwargs **without** reading environment variables or the
    .env file.  This is required because conftest.py registers
    ``EMAIL_SKIP_SEND=true`` in ``os.environ``, and a normal
    ``Settings(**kwargs)`` call would pick that up and ignore the kwarg.
    """
    defaults: dict[str, Any] = {
        "secret_key": os.environ["SECRET_KEY"],
        "database_url": os.environ["DATABASE_URL"],
        "database_sync_url": os.environ["DATABASE_SYNC_URL"],
        "email_skip_send": False,
        "email_provider": "ses",
        "aws_region": _TEST_REGION,
        "smtp_from": _TEST_FROM,
        "ses_from_arn": "",
        "password_hash_rounds": 4,
        "password_min_length": 12,
        # Fields with model defaults that may be accessed during a request:
        "allowed_hosts": [],
        "app_env": "test",
        "email_verification_token_ttl": 86400,
        "smtp_host": "localhost",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_password": "",
    }
    defaults.update(overrides)
    return Settings.model_construct(**defaults)


# ---------------------------------------------------------------------------
# Client fixture
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def ses_client(ses_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTPX test client with SES settings and the isolated SQLite session."""
    cfg = _build_ses_settings()

    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        yield ses_db

    fastapi_app.dependency_overrides[get_db] = _override_db
    with (
        patch("app.core.config.get_settings", return_value=cfg),
        patch("app.services.email.get_settings", return_value=cfg),
        patch("app.services.identity.verify.get_settings", return_value=cfg),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app),
            base_url="http://testserver",
        ) as ac:
            yield ac

    fastapi_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


def _make_ses_client_mock() -> MagicMock:
    """Return a mock boto3 SES client whose send_email succeeds by default."""
    mock_ses = MagicMock()
    mock_ses.send_email.return_value = {
        "MessageId": "mock-ses-message-id-0001",
        "ResponseMetadata": {"HTTPStatusCode": 200},
    }
    return mock_ses


def _patch_boto3_module(mock_ses: MagicMock) -> Any:  # noqa: ANN401
    """Patch app.services.email.boto3 so .client() returns *mock_ses*."""
    mock_boto3 = MagicMock()
    mock_boto3.client.return_value = mock_ses
    return patch("app.services.email.boto3", mock_boto3)


async def _latest_token(db: AsyncSession) -> EmailVerificationToken | None:
    """Return the most recently created EmailVerificationToken row."""
    stmt = select(EmailVerificationToken).order_by(
        EmailVerificationToken.created_at.desc()
    )
    return (await db.execute(stmt)).scalars().first()


# ===========================================================================
# VER-001 test cases
# ===========================================================================


@pytest.mark.asyncio
async def test_ver001_1_ses_called_once_on_register(
    ses_client: AsyncClient,
) -> None:
    """VER-001.1 -- exactly one SES send_email call per registration."""
    mock_ses = _make_ses_client_mock()
    with _patch_boto3_module(mock_ses):
        resp = await ses_client.post(REGISTER_URL, json=_VALID_PAYLOAD)

    assert resp.status_code == 201
    mock_ses.send_email.assert_called_once()


@pytest.mark.asyncio
async def test_ver001_2_ses_recipient_is_normalised(
    ses_client: AsyncClient,
) -> None:
    """VER-001.2 -- Destination.ToAddresses contains the lower-cased email."""
    mock_ses = _make_ses_client_mock()
    with _patch_boto3_module(mock_ses):
        await ses_client.post(REGISTER_URL, json=_VALID_PAYLOAD)

    call_kwargs = mock_ses.send_email.call_args.kwargs
    assert call_kwargs["Destination"]["ToAddresses"] == ["ses_user@example.com"]


@pytest.mark.asyncio
async def test_ver001_3_ses_source_matches_smtp_from(
    ses_client: AsyncClient,
) -> None:
    """VER-001.3 -- Source field equals the configured smtp_from address."""
    mock_ses = _make_ses_client_mock()
    with _patch_boto3_module(mock_ses):
        await ses_client.post(REGISTER_URL, json=_VALID_PAYLOAD)

    call_kwargs = mock_ses.send_email.call_args.kwargs
    assert call_kwargs["Source"] == _TEST_FROM


@pytest.mark.asyncio
async def test_ver001_4_ses_body_contains_token(
    ses_client: AsyncClient,
    ses_db: AsyncSession,
) -> None:
    """VER-001.4 -- both Text and Html body parts contain the raw token."""
    mock_ses = _make_ses_client_mock()
    with _patch_boto3_module(mock_ses):
        await ses_client.post(REGISTER_URL, json=_VALID_PAYLOAD)

    token_row = await _latest_token(ses_db)
    assert token_row is not None, "Expected a token row to be persisted"

    call_kwargs = mock_ses.send_email.call_args.kwargs
    text_body: str = call_kwargs["Message"]["Body"]["Text"]["Data"]
    html_body: str = call_kwargs["Message"]["Body"]["Html"]["Data"]
    assert token_row.token in text_body, "token missing from text body"
    assert token_row.token in html_body, "token missing from html body"


@pytest.mark.asyncio
async def test_ver001_5_ses_source_arn_forwarded_when_set(
    ses_db: AsyncSession,
) -> None:
    """VER-001.5 -- SourceArn included in kwargs when ses_from_arn is set."""
    cfg = _build_ses_settings(ses_from_arn=_TEST_FROM_ARN)

    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        yield ses_db

    fastapi_app.dependency_overrides[get_db] = _override_db

    mock_ses = _make_ses_client_mock()
    mock_boto3 = MagicMock()
    mock_boto3.client.return_value = mock_ses

    with (
        patch("app.core.config.get_settings", return_value=cfg),
        patch("app.services.email.get_settings", return_value=cfg),
        patch("app.services.identity.verify.get_settings", return_value=cfg),
        patch("app.services.email.boto3", mock_boto3),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app),
            base_url="http://testserver",
        ) as ac:
            resp = await ac.post(REGISTER_URL, json=_VALID_PAYLOAD)

    fastapi_app.dependency_overrides.clear()

    assert resp.status_code == 201
    call_kwargs = mock_ses.send_email.call_args.kwargs
    assert call_kwargs.get("SourceArn") == _TEST_FROM_ARN


@pytest.mark.asyncio
async def test_ver001_6_ses_source_arn_absent_when_empty(
    ses_client: AsyncClient,
) -> None:
    """VER-001.6 -- SourceArn key NOT present when ses_from_arn is ''."""
    mock_ses = _make_ses_client_mock()
    with _patch_boto3_module(mock_ses):
        await ses_client.post(REGISTER_URL, json=_VALID_PAYLOAD)

    call_kwargs = mock_ses.send_email.call_args.kwargs
    assert "SourceArn" not in call_kwargs


@pytest.mark.asyncio
async def test_ver001_7_ses_failure_is_non_fatal(
    ses_client: AsyncClient,
) -> None:
    """VER-001.7 -- send_email exception does not prevent HTTP 201 response."""
    mock_ses = _make_ses_client_mock()
    mock_ses.send_email.side_effect = Exception(
        "Simulated SES ClientError: MessageRejected"
    )
    with _patch_boto3_module(mock_ses):
        resp = await ses_client.post(REGISTER_URL, json=_VALID_PAYLOAD)

    # Token row must still be persisted despite email dispatch failure.
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_ver001_8_ses_called_on_resend(
    ses_client: AsyncClient,
) -> None:
    """VER-001.8 -- POST /resend-verification issues a second send_email call."""
    mock_ses = _make_ses_client_mock()
    with _patch_boto3_module(mock_ses):
        await ses_client.post(REGISTER_URL, json=_VALID_PAYLOAD)
        resp = await ses_client.post(
            RESEND_URL, json={"email": "ses_user@example.com"}
        )

    assert resp.status_code == 200
    assert mock_ses.send_email.call_count == 2


@pytest.mark.asyncio
async def test_ver001_9_skip_send_suppresses_ses(
    ses_db: AsyncSession,
) -> None:
    """VER-001.9 -- email_skip_send=True suppresses SES even with provider=ses."""
    cfg = _build_ses_settings(email_skip_send=True)

    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        yield ses_db

    fastapi_app.dependency_overrides[get_db] = _override_db

    mock_ses = _make_ses_client_mock()
    mock_boto3 = MagicMock()
    mock_boto3.client.return_value = mock_ses

    with (
        patch("app.core.config.get_settings", return_value=cfg),
        patch("app.services.email.get_settings", return_value=cfg),
        patch("app.services.identity.verify.get_settings", return_value=cfg),
        patch("app.services.email.boto3", mock_boto3),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app),
            base_url="http://testserver",
        ) as ac:
            resp = await ac.post(REGISTER_URL, json=_VALID_PAYLOAD)

    fastapi_app.dependency_overrides.clear()

    assert resp.status_code == 201
    mock_ses.send_email.assert_not_called()


@pytest.mark.asyncio
async def test_ver001_10_boto3_client_uses_configured_region(
    ses_client: AsyncClient,
) -> None:
    """VER-001.10 -- boto3.client called with region_name matching aws_region."""
    mock_boto3 = MagicMock()
    mock_ses = _make_ses_client_mock()
    mock_boto3.client.return_value = mock_ses

    with patch("app.services.email.boto3", mock_boto3):
        await ses_client.post(REGISTER_URL, json=_VALID_PAYLOAD)

    mock_boto3.client.assert_called_once_with("ses", region_name=_TEST_REGION)

```

### `backend/tests/test_verify.py`
```python
"""Tests for email verification endpoints — TASK-016 / COMP-001.

Covers:
- POST /api/v1/auth/verify-email  (token consumption)
- POST /api/v1/auth/resend-verification  (resend / anti-enumeration)
- Service-layer unit tests (expired, already-used, superseded)
- VER-012: anti-enumeration on resend endpoint
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_verification import EmailVerificationToken
from app.models.user import User
from app.services.identity.verify import (
    TokenExpiredError,
    TokenNotFoundError,
    UserAlreadyVerifiedError,
    UserNotFoundError,
    consume_verification_token,
    issue_verification_token,
    resend_verification_token,
)

REGISTER_URL = "/api/v1/auth/register"
VERIFY_URL = "/api/v1/auth/verify-email"
RESEND_URL = "/api/v1/auth/resend-verification"

VALID_REGISTER = {
    "email": "alice@example.com",
    "password": "Str0ng!Pass#2024",
    "full_name": "Alice Smith",
}

# Sentinel used in place of a real bcrypt hash in direct DB fixture tests.
_FAKE_HASH = "not-a-real-hash"  # noqa: S105


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _register_and_get_token(
    client: AsyncClient,
    db: AsyncSession,
) -> tuple[str, EmailVerificationToken]:
    """Register a user and return the raw token string + first token row."""
    resp = await client.post(REGISTER_URL, json=VALID_REGISTER)
    assert resp.status_code == 201
    stmt = select(EmailVerificationToken)
    result = await db.execute(stmt)
    token_row = result.scalars().first()
    assert token_row is not None
    return token_row.token, token_row


# ── Token issuance ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_registration_creates_token_row(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Registering a user persists exactly one EmailVerificationToken row."""
    await client.post(REGISTER_URL, json=VALID_REGISTER)
    stmt = select(EmailVerificationToken)
    result = await db_session.execute(stmt)
    rows = result.scalars().all()
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_token_has_future_expiry(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """The issued token's expires_at is in the future."""
    await client.post(REGISTER_URL, json=VALID_REGISTER)
    stmt = select(EmailVerificationToken)
    result = await db_session.execute(stmt)
    token_row = result.scalars().first()
    assert token_row is not None
    expires_at = token_row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    assert expires_at > datetime.now(UTC)


@pytest.mark.asyncio
async def test_token_is_not_consumed_on_issuance(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Freshly issued token has consumed_at = NULL."""
    await client.post(REGISTER_URL, json=VALID_REGISTER)
    stmt = select(EmailVerificationToken)
    result = await db_session.execute(stmt)
    token_row = result.scalars().first()
    assert token_row is not None
    assert token_row.consumed_at is None


# ── Happy path: verify email ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_email_returns_200(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Valid token → HTTP 200."""
    raw_token, _ = await _register_and_get_token(client, db_session)
    resp = await client.post(VERIFY_URL, json={"token": raw_token})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_verify_email_response_body(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Valid token → response contains email and success message."""
    raw_token, _ = await _register_and_get_token(client, db_session)
    resp = await client.post(VERIFY_URL, json={"token": raw_token})
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert "verified" in body["message"].lower()


@pytest.mark.asyncio
async def test_verify_email_marks_user_verified(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """After a successful verify, user.is_verified is True."""
    raw_token, token_row = await _register_and_get_token(client, db_session)
    await client.post(VERIFY_URL, json={"token": raw_token})
    stmt = select(User).where(User.id == token_row.user_id)
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.is_verified is True


@pytest.mark.asyncio
async def test_verify_email_marks_token_consumed(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """After consumption the token row has consumed_at set."""
    raw_token, token_row = await _register_and_get_token(client, db_session)
    await client.post(VERIFY_URL, json={"token": raw_token})
    stmt = select(EmailVerificationToken).where(
        EmailVerificationToken.id == token_row.id
    )
    result = await db_session.execute(stmt)
    refreshed = result.scalar_one_or_none()
    assert refreshed is not None
    assert refreshed.consumed_at is not None


# ── 410 Gone: already used ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_already_used_returns_410(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Using the same token twice → HTTP 410."""
    raw_token, _ = await _register_and_get_token(client, db_session)
    await client.post(VERIFY_URL, json={"token": raw_token})
    resp = await client.post(VERIFY_URL, json={"token": raw_token})
    assert resp.status_code == 410


@pytest.mark.asyncio
async def test_verify_already_used_error_code(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Second use → error code is token_invalid."""
    raw_token, _ = await _register_and_get_token(client, db_session)
    await client.post(VERIFY_URL, json={"token": raw_token})
    resp = await client.post(VERIFY_URL, json={"token": raw_token})
    errors = resp.json()["errors"]
    assert any(e["code"] == "token_invalid" for e in errors)


# ── 410 Gone: expired token (service unit test) ───────────────────────────────


@pytest.mark.asyncio
async def test_verify_expired_token_raises(
    db_session: AsyncSession,
) -> None:
    """Service raises TokenExpiredError when expires_at is in the past."""
    user = User(
        email="bob@example.com",
        password_hash=_FAKE_HASH,
        is_verified=False,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    past = datetime.now(UTC) - timedelta(hours=1)
    token_obj = EmailVerificationToken(
        user_id=user.id,
        expires_at=past,
    )
    db_session.add(token_obj)
    await db_session.flush()
    with pytest.raises(TokenExpiredError):
        await consume_verification_token(db_session, token_obj.token)


# ── 410 Gone: superseded token ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_superseded_token_returns_410(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Token superseded by resend → HTTP 410."""
    raw_token, _ = await _register_and_get_token(client, db_session)
    # Resend issues a new token, superseding the old one
    await client.post(RESEND_URL, json={"email": "alice@example.com"})
    resp = await client.post(VERIFY_URL, json={"token": raw_token})
    assert resp.status_code == 410


# ── 404: unknown token ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_unknown_token_returns_404(client: AsyncClient) -> None:
    """Non-existent token → HTTP 404."""
    resp = await client.post(VERIFY_URL, json={"token": "totally-made-up-token"})
    assert resp.status_code == 404


# ── Service: TokenNotFoundError ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_service_raises_token_not_found(db_session: AsyncSession) -> None:
    """consume_verification_token raises TokenNotFoundError for garbage input."""
    with pytest.raises(TokenNotFoundError):
        await consume_verification_token(db_session, "no-such-token")


# ── Service: supersede_existing ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_issue_supersedes_previous_tokens(db_session: AsyncSession) -> None:
    """Issuing a second token marks the first one superseded."""
    user = User(
        email="carol@example.com",
        password_hash=_FAKE_HASH,
        is_verified=False,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    first = await issue_verification_token(db_session, user)
    _second = await issue_verification_token(db_session, user)
    stmt = select(EmailVerificationToken).where(
        EmailVerificationToken.id == first.id
    )
    result = await db_session.execute(stmt)
    refreshed = result.scalar_one_or_none()
    assert refreshed is not None
    assert refreshed.superseded is True


# ── Resend: happy path ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_resend_returns_200(client: AsyncClient) -> None:
    """POST /resend-verification always returns 200."""
    await client.post(REGISTER_URL, json=VALID_REGISTER)
    resp = await client.post(RESEND_URL, json={"email": "alice@example.com"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_resend_creates_new_token(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Resend creates a second token row for the user."""
    await client.post(REGISTER_URL, json=VALID_REGISTER)
    await client.post(RESEND_URL, json={"email": "alice@example.com"})
    stmt = select(EmailVerificationToken)
    result = await db_session.execute(stmt)
    rows = result.scalars().all()
    assert len(rows) == 2  # original + resent


@pytest.mark.asyncio
async def test_resend_supersedes_old_token(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """After resend the original token is superseded."""
    _, first_row = await _register_and_get_token(client, db_session)
    await client.post(RESEND_URL, json={"email": "alice@example.com"})
    stmt = select(EmailVerificationToken).where(
        EmailVerificationToken.id == first_row.id
    )
    result = await db_session.execute(stmt)
    refreshed = result.scalar_one_or_none()
    assert refreshed is not None
    assert refreshed.superseded is True


# ── VER-012: anti-enumeration on resend ──────────────────────────────────────


@pytest.mark.asyncio
async def test_resend_unknown_email_returns_200(client: AsyncClient) -> None:
    """VER-012: unknown email on resend still returns 200 (anti-enumeration)."""
    resp = await client.post(RESEND_URL, json={"email": "nobody@example.com"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_resend_already_verified_returns_200(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """VER-012: already-verified email returns 200 (anti-enumeration)."""
    raw_token, _ = await _register_and_get_token(client, db_session)
    await client.post(VERIFY_URL, json={"token": raw_token})
    resp = await client.post(RESEND_URL, json={"email": "alice@example.com"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_resend_response_body_indistinguishable(client: AsyncClient) -> None:
    """VER-012: response bodies for unknown and known emails are identical."""
    resp_known = await client.post(RESEND_URL, json={"email": "alice@example.com"})
    resp_unknown = await client.post(RESEND_URL, json={"email": "ghost@example.com"})
    assert resp_known.json() == resp_unknown.json()


# ── Resend: service layer ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_service_resend_raises_user_not_found(
    db_session: AsyncSession,
) -> None:
    """resend_verification_token raises UserNotFoundError for unknown email."""
    with pytest.raises(UserNotFoundError):
        await resend_verification_token(db_session, "ghost@example.com")


@pytest.mark.asyncio
async def test_service_resend_raises_already_verified(
    db_session: AsyncSession,
) -> None:
    """resend_verification_token raises UserAlreadyVerifiedError for verified users."""
    user = User(
        email="verified@example.com",
        password_hash=_FAKE_HASH,
        is_verified=True,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    with pytest.raises(UserAlreadyVerifiedError):
        await resend_verification_token(db_session, "verified@example.com")


# ── Input validation ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_missing_token_returns_422(client: AsyncClient) -> None:
    """Missing token field → HTTP 422."""
    resp = await client.post(VERIFY_URL, json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_resend_invalid_email_returns_422(client: AsyncClient) -> None:
    """Malformed email on resend → HTTP 422."""
    resp = await client.post(RESEND_URL, json={"email": "not-an-email"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_resend_email_normalised(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Resend accepts mixed-case email and normalises it."""
    await client.post(REGISTER_URL, json=VALID_REGISTER)
    resp = await client.post(RESEND_URL, json={"email": "ALICE@EXAMPLE.COM"})
    assert resp.status_code == 200

```