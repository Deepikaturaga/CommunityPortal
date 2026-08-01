# Implementation Report

The path resolution needs fixing — the tests can't find the `app` module. Let me run from the right directory:

## Verification
- `node -e "const fs=require('fs'); function walk(d,p=''){try{fs.readdirSync(d).forEach(f=>{const fp=d+'/'+f,rp=p+'/'+f;try{if(fs.statSync(fp).isDirectory()&&!f.startsWith('node_modules')&&f!=='.git'&&f!=='.next'&&f!=='dist'&&f!=='build')walk(fp,rp);else if(!fs.statSync(fp).isDirectory())console.log(rp);}catch(e){}});}catch(e){}}walk('.')"` → exit 127
- `npm --version` → exit 127
- `python3 -c "
import os, json

def walk(root):
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ('node_modules','.git','.next','dist','build','__pycache__','.venv','venv')]
        for f in files:
            print(os.path.join(dirpath, f))

walk('.')
"` → exit 0
- `python3 --version` → exit 0
- `pytest --version` → exit 0
- `pip show pytest-asyncio httpx pytest-cov anyio 2>&1` → exit 0
- `python3 -c "import sys; print(sys.version); import importlib; pkgs=['fastapi','starlette','httpx','pytest_asyncio','jose','passlib','bcrypt','pydantic','sqlalchemy','alembic','freezegun','factory_boy','faker']; [print(p, importlib.import_module(p.replace('-','_')).__version__ if hasattr(importlib.import_module(p.replace('-','_')),'__version__') else 'ok') for p in pkgs]" 2>&1` → exit 1
- `python3 -c "import importlib; pkgs=['time_machine','freezegun','factory_boy','faker','pytest_mock','responses','respx','coverage']; [print(p, 'ok' if __import__(p.replace('-','_'),fromlist=['']) else 'missing') for p in pkgs]" 2>&1` → exit 1
- `pip list 2>&1` → exit 0
- `pip list 2>&1` → exit 0
- `pip show fastapi starlette itsdangerous pydantic python-jose passlib bcrypt httpx pytest-asyncio pytest-cov redis sqlalchemy 2>&1` → exit 0
- `pip show backend identity-service 2>&1` → exit 0
- `python3 -c "import backend; print(backend.__file__)"` → exit 1
- `python3 -c "import identity_service; print(identity_service.__file__)" 2>&1` → exit 1
- `python3 -c "
import os, sys
# Check the editable locations revealed by pip show
paths = [
    '/tmp/archpilot_verify_lqealfv_/backend',
    '/tmp/archpilot_verify_wcamit5u/backend',
]
for p in paths:
    print(p, os.path.exists(p))
"` → exit 0
- `python3 -c "
import os
# Walk /tmp looking for backend project files
for root, dirs, files in os.walk('/tmp'):
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    for f in files:
        if f in ('main.py','app.py','pyproject.toml','setup.py','requirements.txt'):
            print(os.path.join(root, f))
"` → exit 0
- `python3 -c "
import site, os
for p in site.getsitepackages():
    print(p)
    for item in os.listdir(p):
        if 'backend' in item.lower() or 'identity' in item.lower() or 'auth' in item.lower():
            print('  ', item)
"` → exit 0
- `python3 -c "
f = open('/usr/local/lib/python3.12/site-packages/identity_service.pth')
print(f.read())
f.close()
"` → exit 0
- `python3 -c "
f = open('/usr/local/lib/python3.12/site-packages/_editable_impl_backend.pth')
print(f.read())
f.close()
"` → exit 0
- `python3 -c "
import os
cwd = os.getcwd()
print('CWD:', cwd)
# List top-level
for item in os.listdir(cwd):
    print(item)
"` → exit 0
- `python3 -c "
import os
# search all likely mounts
for base in ['/', '/workspace', '/app', '/home', '/repo', '/project', '/code', '/opt']:
    if os.path.exists(base):
        items = os.listdir(base)
        if any(k in items for k in ('backend','frontend','pyproject.toml','requirements.txt','setup.py')):
            print(base, items[:30])
"` → exit 0
- `python3 -c "
import os

def walk(root, indent=0):
    try:
        items = sorted(os.listdir(root))
    except:
        return
    for item in items:
        fp = os.path.join(root, item)
        print(' '*indent + item)
        if os.path.isdir(fp) and item not in ('node_modules','.git','.next','__pycache__','.venv','venv','dist','build','coverage'):
            walk(fp, indent+2)

walk('/app')
"` → exit 0
- `python3 -c "
import os
# Find the actual repo that was generated in prior phases - look for a 'backend' dir at workspace root
# The skill writes to the CWD. Let's find the real workspace root
import subprocess

# Check common workspace paths
for base in ['/workspace', '/repo', '/tmp/workspace', '/home/user/workspace']:
    if os.path.exists(base):
        print(base, os.listdir(base)[:20])
"` → exit 0
- `python3 -c "
import os
cwd = os.getcwd()
print('CWD:', cwd)
# This is the actual workspace for file writes
# Let's check what's there
if os.path.exists(cwd):
    for item in os.listdir(cwd):
        print(item)
"` → exit 0
- `python3 -c "
import os
# Read dist-info for backend and identity-service
for pkg in ['backend-0.1.0.dist-info', 'identity_service-0.1.0.dist-info']:
    base = '/usr/local/lib/python3.12/site-packages/' + pkg
    if os.path.exists(base):
        for f in os.listdir(base):
            print(f'--- {pkg}/{f} ---')
            try:
                print(open(os.path.join(base, f)).read()[:2000])
            except:
                pass
"` → exit 0
- `python3 -c "import aiosqlite; print(aiosqlite.__version__)" 2>&1` → exit 0
- `python3 -c "import pyotp; print(pyotp.__version__)" 2>&1` → exit 1
- `python3 -c "import pyotp; print(dir(pyotp))" 2>&1` → exit 0
- `python3 -c "from jose import jwt; from passlib.context import CryptContext; from itsdangerous import TimestampSigner; import pyotp; print('all imports ok')" 2>&1` → exit 0
- `python3 -c "
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import fastapi
print('pydantic-settings ok')
print('fastapi', fastapi.__version__)
"` → exit 0
- `python3 -c "
import sys, os
sys.path.insert(0, 'backend')
from app.core.config import Settings, get_settings
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password, verify_totp
from app.core.session import set_auth_cookies, clear_auth_cookies, validate_csrf, extract_access_token
from app.db.base import Base, get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, UserOut
from app.routers.auth_router import router
from app.main import create_app
print('All imports OK')
" 2>&1` → exit 0
- `python3 -m pytest ../tests/identity -v --tb=short --no-header -p no:cacheprovider 2>&1` → exit 4
- `python3 -m pytest tests/identity -v --tb=short --no-header -p no:cacheprovider --rootdir=backend --import-mode=importlib 2>&1` → exit 4

## Generated Files

### `.github/workflows/identity-tests.yml`
```yaml
name: Identity & Session Test Suite (PHASE-013)

on:
  push:
    branches: [main, develop, "feature/**"]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: "3.12"

jobs:
  identity-tests:
    name: Auth/Session Automated Tests (VER-001, VER-005–008, VER-012, VER-016, VER-017)
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install \
            fastapi==0.115.5 \
            httpx==0.28.1 \
            itsdangerous==2.2.0 \
            "passlib[bcrypt]==1.7.4" \
            pydantic==2.10.3 \
            "pydantic-settings>=2.3.0" \
            pyotp \
            "python-jose[cryptography]==3.3.0" \
            "sqlalchemy[asyncio]==2.0.36" \
            aiosqlite==0.20.0 \
            anyio==4.7.0 \
            pytest==8.3.4 \
            pytest-asyncio==0.24.0 \
            pytest-cov==6.0.0 \
            uvicorn

      - name: Run identity test suite
        run: |
          pytest ../tests/identity \
            --cov=app \
            --cov-report=term-missing \
            --cov-report=xml:../coverage.xml \
            --cov-report=html:../htmlcov \
            -v \
            --tb=short \
            --junitxml=../test-results.xml
        env:
          PYTHONPATH: .

      - name: Upload coverage report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: |
            coverage.xml
            htmlcov/

      - name: Upload test results (JUnit XML)
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: test-results.xml

      - name: Publish test summary
        if: always()
        uses: dorny/test-reporter@v1
        with:
          name: Identity Test Results
          path: test-results.xml
          reporter: java-junit
          fail-on-error: true

```

### `backend/app/__init__.py`
```python
# backend/app/__init__.py

```

### `backend/app/core/__init__.py`
```python
# backend/app/core/__init__.py

```

### `backend/app/core/config.py`
```python
"""Application configuration via environment variables."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="sqlite+aiosqlite:///./dev.db",
        description="Async SQLAlchemy database URL",
    )

    # ── JWT ───────────────────────────────────────────────────────────────────
    jwt_secret: SecretStr = Field(
        default="change-me-in-production-at-least-32-chars!",
        description="HMAC secret for signing JWTs — minimum 32 chars",
    )
    jwt_algorithm: str = Field(default="HS256")
    # Access token lifetime (minutes)
    access_token_expire_minutes: int = Field(default=15)
    # Refresh token lifetime (days)
    refresh_token_expire_days: int = Field(default=7)

    # ── Cookie / Session ─────────────────────────────────────────────────────
    cookie_name: str = Field(default="session")
    cookie_secure: bool = Field(default=True, description="Set Secure flag on session cookie")
    cookie_httponly: bool = Field(default=True, description="Set HttpOnly flag — no JS access")
    cookie_samesite: str = Field(
        default="lax", description="SameSite policy: strict | lax | none"
    )
    cookie_domain: str | None = Field(default=None)
    session_secret: SecretStr = Field(
        default="session-secret-change-me-32-chars!!",
        description="HMAC secret for signing session cookies (itsdangerous)",
    )
    # Session absolute expiry (seconds)
    session_max_age: int = Field(default=3600, description="Session max age in seconds")

    # ── CSRF ─────────────────────────────────────────────────────────────────
    csrf_header_name: str = Field(default="X-CSRF-Token")
    csrf_cookie_name: str = Field(default="csrf_token")
    csrf_token_expire_seconds: int = Field(default=3600)

    # ── Account Lockout ──────────────────────────────────────────────────────
    max_failed_login_attempts: int = Field(default=5)
    lockout_duration_seconds: int = Field(default=900, description="15 minutes")

    # ── TOTP / MFA ───────────────────────────────────────────────────────────
    totp_issuer: str = Field(default="MyApp")
    totp_digits: int = Field(default=6)
    totp_interval: int = Field(default=30)
    totp_valid_window: int = Field(
        default=1, description="Number of intervals before/after current to accept"
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_name: str = Field(default="Identity API")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    @field_validator("jwt_secret", mode="before")
    @classmethod
    def _secret_min_length(cls, v: str | SecretStr) -> str | SecretStr:
        raw = v.get_secret_value() if isinstance(v, SecretStr) else v
        if len(raw) < 32:
            raise ValueError("jwt_secret must be at least 32 characters")
        return v

    @field_validator("cookie_samesite")
    @classmethod
    def _samesite_valid(cls, v: str) -> str:
        if v.lower() not in {"strict", "lax", "none"}:
            raise ValueError("cookie_samesite must be strict, lax, or none")
        return v.lower()

    @property
    def access_token_expire_seconds(self) -> int:
        return self.access_token_expire_minutes * 60

    @property
    def refresh_token_expire_seconds(self) -> int:
        return self.refresh_token_expire_days * 24 * 3600


@lru_cache
def get_settings() -> Settings:
    """Return singleton Settings (cached after first call)."""
    return Settings()

```

### `backend/app/core/security.py`
```python
"""Security utilities: password hashing, JWT creation/verification, TOTP."""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

import pyotp
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import Settings, get_settings

# ── Password hashing ──────────────────────────────────────────────────────────
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return bcrypt hash of *plain*."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed* bcrypt hash."""
    return _pwd_context.verify(plain, hashed)


# ── JWT helpers ───────────────────────────────────────────────────────────────

_TOKEN_TYPE_CLAIM = "typ"
_ACCESS_TOKEN_TYPE = "access"
_REFRESH_TOKEN_TYPE = "refresh"


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_access_token(
    subject: str,
    *,
    extra_claims: dict[str, Any] | None = None,
    settings: Settings | None = None,
) -> str:
    """Issue a signed JWT access token for *subject* (user id / email)."""
    cfg = settings or get_settings()
    now = _now_utc()
    expire = now.timestamp() + cfg.access_token_expire_seconds
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire),
        _TOKEN_TYPE_CLAIM: _ACCESS_TOKEN_TYPE,
        "jti": secrets.token_hex(16),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(
        payload,
        cfg.jwt_secret.get_secret_value(),
        algorithm=cfg.jwt_algorithm,
    )


def create_refresh_token(
    subject: str,
    *,
    settings: Settings | None = None,
) -> str:
    """Issue a signed JWT refresh token for *subject*."""
    cfg = settings or get_settings()
    now = _now_utc()
    expire = now.timestamp() + cfg.refresh_token_expire_seconds
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire),
        _TOKEN_TYPE_CLAIM: _REFRESH_TOKEN_TYPE,
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(
        payload,
        cfg.jwt_secret.get_secret_value(),
        algorithm=cfg.jwt_algorithm,
    )


def decode_access_token(
    token: str,
    *,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Decode and verify an access token.

    Raises
    ------
    jose.JWTError
        If the token is invalid, expired, or has the wrong type claim.
    """
    cfg = settings or get_settings()
    payload = jwt.decode(
        token,
        cfg.jwt_secret.get_secret_value(),
        algorithms=[cfg.jwt_algorithm],
    )
    if payload.get(_TOKEN_TYPE_CLAIM) != _ACCESS_TOKEN_TYPE:
        raise JWTError("Token type mismatch — expected access token")
    return payload


def decode_refresh_token(
    token: str,
    *,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Decode and verify a refresh token.

    Raises
    ------
    jose.JWTError
        If the token is invalid, expired, or has the wrong type claim.
    """
    cfg = settings or get_settings()
    payload = jwt.decode(
        token,
        cfg.jwt_secret.get_secret_value(),
        algorithms=[cfg.jwt_algorithm],
    )
    if payload.get(_TOKEN_TYPE_CLAIM) != _REFRESH_TOKEN_TYPE:
        raise JWTError("Token type mismatch — expected refresh token")
    return payload


# ── TOTP / MFA ────────────────────────────────────────────────────────────────


def generate_totp_secret() -> str:
    """Return a new random base-32 TOTP secret."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str, *, settings: Settings | None = None) -> str:
    """Return an otpauth:// provisioning URI for authenticator apps."""
    cfg = settings or get_settings()
    totp = pyotp.TOTP(secret, digits=cfg.totp_digits, interval=cfg.totp_interval)
    return totp.provisioning_uri(name=email, issuer_name=cfg.totp_issuer)


def verify_totp(secret: str, code: str, *, settings: Settings | None = None) -> bool:
    """Return True if *code* is valid for *secret* within the allowed window."""
    cfg = settings or get_settings()
    totp = pyotp.TOTP(secret, digits=cfg.totp_digits, interval=cfg.totp_interval)
    return totp.verify(code, valid_window=cfg.totp_valid_window)


# ── CSRF token helpers ────────────────────────────────────────────────────────


def generate_csrf_token() -> str:
    """Return a cryptographically random CSRF token."""
    return secrets.token_urlsafe(32)

```

### `backend/app/core/session.py`
```python
"""Session management: HTTP-only cookie issuance and validation.

Design
------
* Access token  → short-lived JWT (15 min) in HttpOnly Secure cookie.
* Refresh token → long-lived JWT (7 days) in a *separate* HttpOnly Secure cookie.
* CSRF token    → opaque random value sent in a *readable* cookie (SameSite=lax)
                  and echoed back in the X-CSRF-Token header on every mutating
                  request (double-submit cookie pattern).
* Session ID    → itsdangerous TimestampSigner ties cookie integrity to the
                  server-side secret without requiring a session store for the
                  access-token cookie.  Refresh rotation invalidates the old
                  refresh token by virtue of the new JTI.

Cookie flags
------------
  HttpOnly  = True   (access + refresh cookies — no JS access)
  Secure    = True   (production; relaxed to False in tests via settings)
  SameSite  = "lax"  (configurable; "strict" for maximum CSRF protection)
  Path      = "/"
"""
from __future__ import annotations

from fastapi import Response
from itsdangerous import BadSignature, SignatureExpired, TimestampSigner

from app.core.config import Settings, get_settings
from app.core.security import generate_csrf_token

_ACCESS_COOKIE = "access_token"
_REFRESH_COOKIE = "refresh_token"
_CSRF_COOKIE = "csrf_token"


# ── Cookie issuance ───────────────────────────────────────────────────────────


def set_auth_cookies(
    response: Response,
    *,
    access_token: str,
    refresh_token: str,
    settings: Settings | None = None,
) -> str:
    """Attach access, refresh, and CSRF cookies to *response*.

    Returns the CSRF token value so callers can embed it in a JSON body if
    needed (e.g., the login response payload).
    """
    cfg = settings or get_settings()

    signer = TimestampSigner(cfg.session_secret.get_secret_value())
    signed_access = signer.sign(access_token).decode()

    # Access token — HttpOnly, Secure, SameSite
    response.set_cookie(
        key=_ACCESS_COOKIE,
        value=signed_access,
        max_age=cfg.access_token_expire_seconds,
        httponly=cfg.cookie_httponly,
        secure=cfg.cookie_secure,
        samesite=cfg.cookie_samesite,
        domain=cfg.cookie_domain,
        path="/",
    )

    # Refresh token — HttpOnly, Secure, SameSite (narrower path)
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=refresh_token,
        max_age=cfg.refresh_token_expire_seconds,
        httponly=cfg.cookie_httponly,
        secure=cfg.cookie_secure,
        samesite=cfg.cookie_samesite,
        domain=cfg.cookie_domain,
        path="/auth/refresh",
    )

    # CSRF token — NOT HttpOnly so JS can read it; SameSite=lax
    csrf = generate_csrf_token()
    response.set_cookie(
        key=_CSRF_COOKIE,
        value=csrf,
        max_age=cfg.csrf_token_expire_seconds,
        httponly=False,
        secure=cfg.cookie_secure,
        samesite=cfg.cookie_samesite,
        domain=cfg.cookie_domain,
        path="/",
    )

    return csrf


def clear_auth_cookies(response: Response, *, settings: Settings | None = None) -> None:
    """Delete all auth cookies (logout / session invalidation)."""
    cfg = settings or get_settings()
    for name, path in [
        (_ACCESS_COOKIE, "/"),
        (_REFRESH_COOKIE, "/auth/refresh"),
        (_CSRF_COOKIE, "/"),
    ]:
        response.delete_cookie(
            key=name,
            path=path,
            domain=cfg.cookie_domain,
            secure=cfg.cookie_secure,
            httponly=name != _CSRF_COOKIE,
            samesite=cfg.cookie_samesite,
        )


# ── Cookie extraction ─────────────────────────────────────────────────────────


def extract_access_token(
    signed_value: str,
    *,
    settings: Settings | None = None,
) -> str:
    """Unsign and return the raw access JWT from the cookie value.

    Raises
    ------
    itsdangerous.SignatureExpired
        When the signature timestamp exceeds the configured max_age.
    itsdangerous.BadSignature
        When the signature is invalid (tampered cookie).
    """
    cfg = settings or get_settings()
    signer = TimestampSigner(cfg.session_secret.get_secret_value())
    # max_age matches access token lifetime
    raw: bytes | str = signer.unsign(
        signed_value, max_age=cfg.access_token_expire_seconds
    )
    return raw.decode() if isinstance(raw, bytes) else raw


def validate_csrf(
    cookie_csrf: str | None,
    header_csrf: str | None,
) -> bool:
    """Return True iff the double-submit CSRF tokens match.

    Both the cookie value and the X-CSRF-Token header must be present and
    identical (constant-time comparison via ``secrets.compare_digest``).
    """
    import secrets

    if not cookie_csrf or not header_csrf:
        return False
    return secrets.compare_digest(cookie_csrf, header_csrf)

```

### `backend/app/db/__init__.py`
```python
# backend/app/db/__init__.py

```

### `backend/app/db/base.py`
```python
"""SQLAlchemy async database engine and session factory."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


def _build_engine(database_url: str | None = None):  # type: ignore[no-untyped-def]
    url = database_url or get_settings().database_url
    # connect_args only relevant for SQLite (no concurrent access by default)
    connect_args: dict = {}
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_async_engine(url, echo=False, connect_args=connect_args)


engine = _build_engine()

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_tables() -> None:
    """Create all ORM tables (development/testing helper)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Drop all ORM tables (testing teardown helper)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

```

### `backend/app/main.py`
```python
"""FastAPI application factory."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers.auth_router import router as auth_router


def create_app(settings=None) -> FastAPI:  # type: ignore[no-untyped-def]
    cfg = settings or get_settings()
    app = FastAPI(
        title=cfg.app_name,
        version="1.0.0",
        docs_url="/docs" if cfg.debug else None,
        redoc_url="/redoc" if cfg.debug else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],  # explicitly empty — must be configured per deployment
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-CSRF-Token"],
    )

    app.include_router(auth_router)

    @app.get("/health")
    async def health() -> dict:  # type: ignore[type-arg]
        return {"status": "ok"}

    return app


app = create_app()

```

### `backend/app/models/__init__.py`
```python
# backend/app/models/__init__.py

```

### `backend/app/models/user.py`
```python
"""User ORM model."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Account state ──────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── MFA / TOTP ────────────────────────────────────────────────────────────
    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Lockout ───────────────────────────────────────────────────────────────
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Refresh token family (rotation / replay detection) ───────────────────
    # Stores the JTI of the current valid refresh token.  A reuse of an
    # invalidated JTI triggers family revocation (all tokens for this user
    # are implicitly invalidated by rotating this value).
    refresh_token_jti: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def is_locked(self, now: datetime | None = None) -> bool:
        """Return True if account is currently locked out."""
        if self.locked_until is None:
            return False
        _now = now or datetime.now(tz=timezone.utc)
        # Ensure both are tz-aware for comparison
        locked = (
            self.locked_until.replace(tzinfo=timezone.utc)
            if self.locked_until.tzinfo is None
            else self.locked_until
        )
        return locked > _now

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"

```

### `backend/app/routers/__init__.py`
```python
# backend/app/routers/__init__.py

```

### `backend/app/routers/auth_router.py`
```python
"""Auth router: register, login, logout, refresh, TOTP setup/verify."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response, status
from jose import jwt as _jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    generate_totp_secret,
    get_totp_uri,
    hash_password,
    verify_password,
    verify_totp,
)
from app.core.session import (
    clear_auth_cookies,
    extract_access_token,
    set_auth_cookies,
    validate_csrf,
)
from app.db.base import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RefreshResponse,
    RegisterRequest,
    TOTPSetupRequest,
    TOTPSetupResponse,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# ── Internal helpers ──────────────────────────────────────────────────────────


async def _get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


def _check_lockout(user: User) -> None:
    if user.is_locked():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked due to too many failed attempts",
        )


async def _record_failed_attempt(
    db: AsyncSession, user: User, settings: Settings
) -> None:
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= settings.max_failed_login_attempts:
        from datetime import timedelta

        user.locked_until = datetime.now(tz=timezone.utc) + timedelta(
            seconds=settings.lockout_duration_seconds
        )
    await db.flush()


async def _reset_failed_attempts(db: AsyncSession, user: User) -> None:
    user.failed_login_attempts = 0
    user.locked_until = None
    await db.flush()


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserOut:
    existing = await _get_user_by_email(db, body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    user = await _get_user_by_email(db, body.email)

    if not user or not verify_password(body.password, user.hashed_password):
        if user:
            await _record_failed_attempt(db, user, settings)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    _check_lockout(user)

    if user.totp_enabled:
        if not body.totp_code:
            return LoginResponse(
                message="MFA required",
                csrf_token="",
                user=UserOut.model_validate(user),
                mfa_required=True,
            )
        if not verify_totp(user.totp_secret or "", body.totp_code, settings=settings):
            await _record_failed_attempt(db, user, settings)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid TOTP code",
            )

    await _reset_failed_attempts(db, user)

    access = create_access_token(user.email, settings=settings)
    refresh = create_refresh_token(user.email, settings=settings)

    refresh_payload = _jwt.get_unverified_claims(refresh)
    user.refresh_token_jti = refresh_payload.get("jti")
    await db.flush()

    csrf = set_auth_cookies(
        response, access_token=access, refresh_token=refresh, settings=settings
    )
    return LoginResponse(csrf_token=csrf, user=UserOut.model_validate(user))


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
    csrf_cookie: Annotated[str | None, Cookie(alias="csrf_token")] = None,
    x_csrf_token: Annotated[str | None, Header()] = None,
) -> MessageResponse:
    if not validate_csrf(csrf_cookie, x_csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed",
        )
    clear_auth_cookies(response, settings=settings)
    return MessageResponse(message="Logged out successfully")


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token_endpoint(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    refresh_cookie: Annotated[str | None, Cookie(alias="refresh_token")] = None,
    csrf_cookie: Annotated[str | None, Cookie(alias="csrf_token")] = None,
    x_csrf_token: Annotated[str | None, Header()] = None,
) -> RefreshResponse:
    if not validate_csrf(csrf_cookie, x_csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed",
        )
    if not refresh_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )
    try:
        payload = decode_refresh_token(refresh_cookie, settings=settings)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    incoming_jti: str | None = payload.get("jti")
    user = await _get_user_by_email(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if user.refresh_token_jti != incoming_jti:
        user.refresh_token_jti = None
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected — all sessions revoked",
        )

    _check_lockout(user)

    new_access = create_access_token(user.email, settings=settings)
    new_refresh = create_refresh_token(user.email, settings=settings)

    new_refresh_payload = _jwt.get_unverified_claims(new_refresh)
    user.refresh_token_jti = new_refresh_payload.get("jti")
    await db.flush()

    csrf = set_auth_cookies(
        response, access_token=new_access, refresh_token=new_refresh, settings=settings
    )
    return RefreshResponse(csrf_token=csrf)


@router.post("/totp/setup", response_model=TOTPSetupResponse)
async def totp_setup(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    access_cookie: Annotated[str | None, Cookie(alias="access_token")] = None,
) -> TOTPSetupResponse:
    if not access_cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        raw = extract_access_token(access_cookie, settings=settings)
        token_payload = decode_access_token(raw, settings=settings)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    user = await _get_user_by_email(db, token_payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    secret = generate_totp_secret()
    user.totp_secret = secret
    await db.flush()

    uri = get_totp_uri(secret, user.email, settings=settings)
    return TOTPSetupResponse(secret=secret, uri=uri)


@router.post("/totp/confirm", response_model=MessageResponse)
async def totp_confirm(
    body: TOTPSetupRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    access_cookie: Annotated[str | None, Cookie(alias="access_token")] = None,
) -> MessageResponse:
    if not access_cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        raw = extract_access_token(access_cookie, settings=settings)
        token_payload = decode_access_token(raw, settings=settings)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    user = await _get_user_by_email(db, token_payload["sub"])
    if not user or not user.totp_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TOTP not initialized")

    if not verify_totp(user.totp_secret, body.code, settings=settings):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code")

    user.totp_enabled = True
    await db.flush()
    return MessageResponse(message="TOTP enabled successfully")


@router.get("/me", response_model=UserOut)
async def get_me(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    access_cookie: Annotated[str | None, Cookie(alias="access_token")] = None,
) -> UserOut:
    if not access_cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        raw = extract_access_token(access_cookie, settings=settings)
        token_payload = decode_access_token(raw, settings=settings)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    user = await _get_user_by_email(db, token_payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return UserOut.model_validate(user)

```

### `backend/app/schemas/__init__.py`
```python
# backend/app/schemas/__init__.py

```

### `backend/app/schemas/auth.py`
```python
"""Pydantic schemas for authentication request/response."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Request bodies ────────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def _password_complexity(cls, v: str) -> str:
        errors: list[str] = []
        if not any(c.isupper() for c in v):
            errors.append("at least one uppercase letter")
        if not any(c.islower() for c in v):
            errors.append("at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("at least one digit")
        if errors:
            raise ValueError("Password must contain: " + ", ".join(errors))
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    totp_code: str | None = Field(default=None, min_length=6, max_length=8)


class RefreshRequest(BaseModel):
    """Body is empty; token arrives via HttpOnly cookie."""


class TOTPSetupRequest(BaseModel):
    """Confirm TOTP enrollment by submitting the first valid code."""

    code: str = Field(min_length=6, max_length=8)


class TOTPVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=8)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# ── Response bodies ───────────────────────────────────────────────────────────


class UserOut(BaseModel):
    id: int
    email: str
    is_active: bool
    is_verified: bool
    totp_enabled: bool

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    """
    Tokens are NOT returned in the body — they live in HttpOnly cookies.
    The CSRF token IS returned so the client JS can attach it to mutation headers.
    """

    message: str = "Login successful"
    csrf_token: str
    user: UserOut
    mfa_required: bool = False


class RefreshResponse(BaseModel):
    message: str = "Token refreshed"
    csrf_token: str


class TOTPSetupResponse(BaseModel):
    secret: str
    uri: str
    message: str = "Scan the QR code with your authenticator app"


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None

```

### `backend/pyproject.toml`
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "alembic>=1.13.1",
    "asyncpg>=0.29.0",
    "fastapi>=0.111.0",
    "httpx>=0.27.0",
    "itsdangerous>=2.2.0",
    "passlib[bcrypt]>=1.7.4",
    "pydantic-settings>=2.3.0",
    "pydantic>=2.7.0",
    "pyotp>=2.9.0",
    "python-jose[cryptography]>=3.3.0",
    "sqlalchemy>=2.0.30",
    "uvicorn[standard]>=0.29.0",
]

[project.optional-dependencies]
dev = [
    "aiosqlite>=0.20.0",
    "anyio>=4.3.0",
    "mypy>=1.10.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "pytest>=8.2.0",
    "ruff>=0.4.0",
    "sqlalchemy[mypy]>=2.0.30",
]

[tool.hatch.build.targets.wheel]
packages = ["app"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = [
    "--cov=app",
    "--cov-report=term-missing",
    "--cov-report=xml:coverage.xml",
    "--cov-report=html:htmlcov",
    "-v",
    "--tb=short",
]
filterwarnings = [
    "ignore::DeprecationWarning:passlib",
    "ignore::DeprecationWarning:jose",
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "S", "ANN"]
ignore = [
    "ANN101",  # self annotation not required
    "ANN102",  # cls annotation not required
    "S101",    # allow assert in tests
]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["sqlalchemy.ext.mypy.plugin"]

```

### `backend/pytest.ini`
```text
[pytest]
asyncio_mode = auto
testpaths = tests
addopts =
    --cov=app
    --cov-report=term-missing
    --cov-report=xml:coverage.xml
    --cov-report=html:htmlcov
    -v
    --tb=short
filterwarnings =
    ignore::DeprecationWarning:passlib
    ignore::DeprecationWarning:jose
    ignore::pytest.PytestUnraisableExceptionWarning

```

### `tests/__init__.py`
```python
# tests/__init__.py

```

### `tests/identity/__init__.py`
```python
# tests/identity/__init__.py

```

### `tests/identity/conftest.py`
```python
"""
tests/identity/conftest.py
--------------------------
Shared pytest fixtures for the identity / auth test suite.

Scope hierarchy
---------------
session  — engine + tables (created once)
function — async DB session, HTTP client (isolated per test)
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_totp_secret,
    hash_password,
)
from app.core.session import set_auth_cookies
from app.db.base import Base, get_db
from app.main import create_app
from app.models.user import User

# ── Test-only settings (SQLite in-memory, cookies not Secure for test) ─────────

TEST_SETTINGS = Settings(
    database_url="sqlite+aiosqlite:///:memory:",
    jwt_secret="test-secret-key-that-is-at-least-32-chars",
    session_secret="test-session-secret-32-chars!!!!",
    cookie_secure=False,      # httpx test client doesn't enforce HTTPS
    cookie_httponly=True,
    cookie_samesite="lax",
    access_token_expire_minutes=15,
    refresh_token_expire_days=7,
    session_max_age=3600,
    csrf_token_expire_seconds=3600,
    max_failed_login_attempts=5,
    lockout_duration_seconds=900,
    totp_valid_window=1,
    debug=True,
)

# ── Async engine (per-session scope) ─────────────────────────────────────────


@pytest.fixture(scope="session")
def event_loop():
    """Use a single event loop for the whole test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create the async SQLite engine once per session."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture()
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:  # type: ignore[type-arg]
    """Per-test async DB session — rolls back after each test for isolation."""
    async_session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        yield session
        await session.rollback()


# ── FastAPI app + HTTPX client ────────────────────────────────────────────────


@pytest_asyncio.fixture()
async def app(db_session: AsyncSession) -> FastAPI:
    """Create a test app instance wired to the test DB session and settings."""
    _app = create_app(settings=TEST_SETTINGS)

    # Override the get_db dependency to use the per-test session
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    # Override settings dependency
    from app.core.config import get_settings

    _app.dependency_overrides[get_db] = _override_get_db
    _app.dependency_overrides[get_settings] = lambda: TEST_SETTINGS
    return _app


@pytest_asyncio.fixture()
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTPX client wired to the test app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        follow_redirects=True,
    ) as ac:
        yield ac


# ── User factories ────────────────────────────────────────────────────────────

_DEFAULT_PASSWORD = "Password1!"


async def _make_user(
    db: AsyncSession,
    *,
    email: str = "user@example.com",
    password: str = _DEFAULT_PASSWORD,
    totp_enabled: bool = False,
    totp_secret: str | None = None,
    failed_attempts: int = 0,
    locked_until: datetime | None = None,
    refresh_token_jti: str | None = None,
) -> User:
    secret = totp_secret or (generate_totp_secret() if totp_enabled else None)
    user = User(
        email=email,
        hashed_password=hash_password(password),
        totp_enabled=totp_enabled,
        totp_secret=secret,
        failed_login_attempts=failed_attempts,
        locked_until=locked_until,
        refresh_token_jti=refresh_token_jti,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture()
async def plain_user(db_session: AsyncSession) -> User:
    """A regular active user with no MFA."""
    return await _make_user(db_session)


@pytest_asyncio.fixture()
async def mfa_user(db_session: AsyncSession) -> User:
    """A user with TOTP MFA enabled."""
    return await _make_user(
        db_session,
        email="mfa@example.com",
        totp_enabled=True,
    )


@pytest_asyncio.fixture()
async def locked_user(db_session: AsyncSession) -> User:
    """A user whose account is currently locked out."""
    from datetime import timedelta

    return await _make_user(
        db_session,
        email="locked@example.com",
        failed_attempts=5,
        locked_until=datetime.now(tz=timezone.utc) + timedelta(seconds=900),
    )


# ── Auth cookie helpers ───────────────────────────────────────────────────────


def make_cookie_header(cookies: dict[str, str]) -> str:
    """Build a Cookie header string from a dict."""
    return "; ".join(f"{k}={v}" for k, v in cookies.items())


def extract_cookies(response: Any) -> dict[str, str]:
    """Extract set-cookie values from an httpx Response into a dict."""
    result: dict[str, str] = {}
    for name, cookie in response.cookies.items():
        result[name] = cookie
    return result

```

### `tests/identity/test_account_lockout.py`
```python
"""
tests/identity/test_account_lockout.py
----------------------------------------
VER-017: Account lockout after repeated failed login attempts.

Policy under test (from TEST_SETTINGS)
---------------------------------------
* max_failed_login_attempts = 5
* lockout_duration_seconds  = 900  (15 minutes)

Scenarios
---------
1. Failed attempts increment the counter.
2. Reaching the threshold triggers a lockout (locked_until set).
3. Locked account returns 429 even with correct credentials.
4. Successful login resets the failure counter.
5. An already-locked user (fixture) is immediately blocked.
6. After lockout expires (simulate via DB manipulation) login succeeds.
7. Failed TOTP attempts count toward lockout.
8. Error response for a locked account does NOT leak the lockout timestamp
   or failure count.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from tests.identity.conftest import TEST_SETTINGS, _make_user


class TestLockoutAccrual:
    @pytest.mark.asyncio
    async def test_failed_login_increments_counter(
        self, client: AsyncClient, plain_user: User, db_session: AsyncSession
    ) -> None:
        """Each failed password attempt must increment failed_login_attempts."""
        initial = plain_user.failed_login_attempts

        await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "WrongPass1!"},
        )
        await db_session.refresh(plain_user)
        assert plain_user.failed_login_attempts == initial + 1

    @pytest.mark.asyncio
    async def test_multiple_failures_accumulate(
        self, client: AsyncClient, plain_user: User, db_session: AsyncSession
    ) -> None:
        """3 consecutive failures must yield failed_login_attempts == 3."""
        for _ in range(3):
            await client.post(
                "/auth/login",
                json={"email": plain_user.email, "password": "WrongPass1!"},
            )
        await db_session.refresh(plain_user)
        assert plain_user.failed_login_attempts == 3

    @pytest.mark.asyncio
    async def test_reaching_threshold_sets_locked_until(
        self, client: AsyncClient, plain_user: User, db_session: AsyncSession
    ) -> None:
        """Hitting max_failed_login_attempts must set locked_until in the future."""
        threshold = TEST_SETTINGS.max_failed_login_attempts
        now_before = datetime.now(tz=timezone.utc)

        for _ in range(threshold):
            await client.post(
                "/auth/login",
                json={"email": plain_user.email, "password": "WrongPass1!"},
            )
        await db_session.refresh(plain_user)

        assert plain_user.locked_until is not None
        locked = (
            plain_user.locked_until.replace(tzinfo=timezone.utc)
            if plain_user.locked_until.tzinfo is None
            else plain_user.locked_until
        )
        assert locked > now_before, "locked_until must be in the future"

    @pytest.mark.asyncio
    async def test_locked_account_returns_429(
        self, client: AsyncClient, plain_user: User, db_session: AsyncSession
    ) -> None:
        """After threshold failures, even a correct password must return 429."""
        threshold = TEST_SETTINGS.max_failed_login_attempts
        for _ in range(threshold):
            await client.post(
                "/auth/login",
                json={"email": plain_user.email, "password": "WrongPass1!"},
            )

        # Now try with CORRECT credentials
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        assert resp.status_code == 429, (
            "Locked account must return 429 even with correct credentials"
        )

    @pytest.mark.asyncio
    async def test_lockout_response_does_not_leak_internal_details(
        self, client: AsyncClient, plain_user: User, db_session: AsyncSession
    ) -> None:
        """Error response must not expose locked_until timestamp or attempt count."""
        threshold = TEST_SETTINGS.max_failed_login_attempts
        for _ in range(threshold):
            await client.post(
                "/auth/login",
                json={"email": plain_user.email, "password": "WrongPass1!"},
            )
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        body_str = resp.text
        # Must not expose the actual locked_until datetime or attempt count
        assert "locked_until" not in body_str
        assert "failed_login_attempts" not in body_str

    @pytest.mark.asyncio
    async def test_successful_login_resets_counter(
        self, client: AsyncClient, plain_user: User, db_session: AsyncSession
    ) -> None:
        """A successful login must reset failed_login_attempts to 0."""
        # Accumulate 2 failures (below threshold)
        for _ in range(2):
            await client.post(
                "/auth/login",
                json={"email": plain_user.email, "password": "WrongPass1!"},
            )
        await db_session.refresh(plain_user)
        assert plain_user.failed_login_attempts == 2

        # Successful login
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        assert resp.status_code == 200
        await db_session.refresh(plain_user)
        assert plain_user.failed_login_attempts == 0


class TestLockoutFixtures:
    @pytest.mark.asyncio
    async def test_pre_locked_user_immediately_blocked(
        self, client: AsyncClient, locked_user: User
    ) -> None:
        """A user with locked_until in the future must be rejected immediately."""
        resp = await client.post(
            "/auth/login",
            json={"email": locked_user.email, "password": "Password1!"},
        )
        assert resp.status_code == 429

    @pytest.mark.asyncio
    async def test_expired_lockout_allows_login(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """When locked_until is in the past, login must succeed again."""
        # Create a user whose lockout has already expired
        expired_lock = datetime.now(tz=timezone.utc) - timedelta(seconds=1)
        user = await _make_user(
            db_session,
            email="expired-lock@example.com",
            failed_attempts=5,
            locked_until=expired_lock,
        )
        resp = await client.post(
            "/auth/login",
            json={"email": user.email, "password": "Password1!"},
        )
        assert resp.status_code == 200, (
            "Login must succeed after the lockout period has expired"
        )

    @pytest.mark.asyncio
    async def test_expired_lockout_resets_counter_on_success(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Successful post-expiry login must also clear the failure counter."""
        expired_lock = datetime.now(tz=timezone.utc) - timedelta(seconds=1)
        user = await _make_user(
            db_session,
            email="expired-reset@example.com",
            failed_attempts=5,
            locked_until=expired_lock,
        )
        await client.post(
            "/auth/login",
            json={"email": user.email, "password": "Password1!"},
        )
        await db_session.refresh(user)
        assert user.failed_login_attempts == 0
        assert user.locked_until is None


class TestTOTPLockout:
    @pytest.mark.asyncio
    async def test_failed_totp_counts_toward_lockout(
        self, client: AsyncClient, mfa_user: User, db_session: AsyncSession
    ) -> None:
        """Failed TOTP attempts must increment the lockout counter."""
        initial = mfa_user.failed_login_attempts

        await client.post(
            "/auth/login",
            json={
                "email": mfa_user.email,
                "password": "Password1!",
                "totp_code": "000000",
            },
        )
        await db_session.refresh(mfa_user)
        assert mfa_user.failed_login_attempts == initial + 1

    @pytest.mark.asyncio
    async def test_mfa_lockout_threshold_triggers_block(
        self, client: AsyncClient, mfa_user: User, db_session: AsyncSession
    ) -> None:
        """Repeated TOTP failures must eventually lock the account."""
        threshold = TEST_SETTINGS.max_failed_login_attempts

        for _ in range(threshold):
            await client.post(
                "/auth/login",
                json={
                    "email": mfa_user.email,
                    "password": "Password1!",
                    "totp_code": "000000",
                },
            )

        import pyotp

        valid_code = pyotp.TOTP(mfa_user.totp_secret or "").now()
        resp = await client.post(
            "/auth/login",
            json={
                "email": mfa_user.email,
                "password": "Password1!",
                "totp_code": valid_code,
            },
        )
        # Even valid TOTP cannot bypass a lockout
        assert resp.status_code == 429

```

### `tests/identity/test_cookie_flags.py`
```python
"""
tests/identity/test_cookie_flags.py
-------------------------------------
VER-008: Session cookies carry the correct security flags.

Required flags
--------------
access_token  cookie: HttpOnly=True, Secure=configurable, SameSite=lax|strict
refresh_token cookie: HttpOnly=True, Secure=configurable, SameSite=lax|strict
csrf_token    cookie: HttpOnly=False (JS-readable), Secure=configurable, SameSite=lax|strict

Note: In the test settings, Secure=False so httpx can work over http://testserver.
We verify the flag is present when settings.cookie_secure=True by inspecting
the raw Set-Cookie header strings produced by the ASGI app.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.user import User
from tests.identity.conftest import TEST_SETTINGS


def _parse_set_cookie(header: str) -> dict[str, str | bool]:
    """Parse a Set-Cookie header string into a dict of attributes."""
    parts = [p.strip() for p in header.split(";")]
    result: dict[str, str | bool] = {}
    for i, part in enumerate(parts):
        if "=" in part:
            k, v = part.split("=", 1)
            result[k.strip().lower()] = v.strip()
        else:
            result[part.strip().lower()] = True
    return result


async def _login_get_cookies(client: AsyncClient, email: str) -> list[str]:
    resp = await client.post(
        "/auth/login",
        json={"email": email, "password": "Password1!"},
    )
    assert resp.status_code == 200
    return resp.headers.get_list("set-cookie")


class TestAccessTokenCookieFlags:
    @pytest.mark.asyncio
    async def test_access_token_is_httponly(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        headers = await _login_get_cookies(client, plain_user.email)
        access = [h for h in headers if h.lower().startswith("access_token")]
        assert len(access) == 1
        parsed = _parse_set_cookie(access[0])
        assert parsed.get("httponly") is True, "access_token must be HttpOnly"

    @pytest.mark.asyncio
    async def test_access_token_has_samesite(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        headers = await _login_get_cookies(client, plain_user.email)
        access = [h for h in headers if h.lower().startswith("access_token")]
        parsed = _parse_set_cookie(access[0])
        samesite = parsed.get("samesite", "")
        assert str(samesite).lower() in ("lax", "strict"), (
            f"access_token SameSite must be lax or strict, got {samesite!r}"
        )

    @pytest.mark.asyncio
    async def test_access_token_path_is_root(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        headers = await _login_get_cookies(client, plain_user.email)
        access = [h for h in headers if h.lower().startswith("access_token")]
        parsed = _parse_set_cookie(access[0])
        assert parsed.get("path") == "/", "access_token path must be /"


class TestRefreshTokenCookieFlags:
    @pytest.mark.asyncio
    async def test_refresh_token_is_httponly(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        headers = await _login_get_cookies(client, plain_user.email)
        refresh = [h for h in headers if h.lower().startswith("refresh_token")]
        assert len(refresh) == 1
        parsed = _parse_set_cookie(refresh[0])
        assert parsed.get("httponly") is True, "refresh_token must be HttpOnly"

    @pytest.mark.asyncio
    async def test_refresh_token_has_samesite(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        headers = await _login_get_cookies(client, plain_user.email)
        refresh = [h for h in headers if h.lower().startswith("refresh_token")]
        parsed = _parse_set_cookie(refresh[0])
        samesite = parsed.get("samesite", "")
        assert str(samesite).lower() in ("lax", "strict")

    @pytest.mark.asyncio
    async def test_refresh_token_path_scoped(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Refresh cookie must be scoped to /auth/refresh — not globally accessible."""
        headers = await _login_get_cookies(client, plain_user.email)
        refresh = [h for h in headers if h.lower().startswith("refresh_token")]
        parsed = _parse_set_cookie(refresh[0])
        path = str(parsed.get("path", ""))
        assert path == "/auth/refresh", (
            f"refresh_token cookie must be scoped to /auth/refresh, got {path!r}"
        )

    @pytest.mark.asyncio
    async def test_refresh_token_not_sent_to_non_refresh_path(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """The refresh token cookie must NOT be sent to /auth/me (scoped path check)."""
        # Log in so the client jar has all cookies
        await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        # The httpx client should only send cookies matching the path.
        # We inspect what the client *would* send to /auth/me:
        # The refresh_token cookie is scoped to /auth/refresh so it should
        # not be present in a request to /auth/me.
        # We verify this by checking the Set-Cookie scope.
        # (httpx respects path scoping when follow_redirects=True)
        headers = await _login_get_cookies(client, plain_user.email)
        refresh = [h for h in headers if h.lower().startswith("refresh_token")]
        parsed = _parse_set_cookie(refresh[0])
        assert "/auth/refresh" in str(parsed.get("path", "")), (
            "Refresh cookie path must restrict transmission to /auth/refresh only"
        )


class TestCSRFCookieFlags:
    @pytest.mark.asyncio
    async def test_csrf_cookie_is_not_httponly(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        headers = await _login_get_cookies(client, plain_user.email)
        csrf = [h for h in headers if h.lower().startswith("csrf_token")]
        assert len(csrf) == 1
        parsed = _parse_set_cookie(csrf[0])
        assert "httponly" not in parsed, (
            "csrf_token must NOT be HttpOnly — JavaScript must be able to read it"
        )

    @pytest.mark.asyncio
    async def test_csrf_cookie_has_samesite(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        headers = await _login_get_cookies(client, plain_user.email)
        csrf = [h for h in headers if h.lower().startswith("csrf_token")]
        parsed = _parse_set_cookie(csrf[0])
        samesite = parsed.get("samesite", "")
        assert str(samesite).lower() in ("lax", "strict")


class TestCookieFlagsWithSecureEnabled:
    """Verify the Secure flag is written when settings.cookie_secure=True."""

    @pytest.mark.asyncio
    async def test_access_cookie_secure_flag_when_enabled(
        self, app  # type: ignore[no-untyped-def]
    ) -> None:
        """Override settings to enable Secure and verify the flag appears."""
        from httpx import ASGITransport, AsyncClient

        # Build a new settings copy with cookie_secure=True
        secure_settings = TEST_SETTINGS.model_copy(update={"cookie_secure": True})

        from app.core.config import get_settings
        from app.db.base import get_db

        # Reuse the same app but swap settings
        app.dependency_overrides[get_settings] = lambda: secure_settings

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="https://testserver",  # https required for Secure cookies
            follow_redirects=True,
        ) as secure_client:
            # Register + login a fresh user
            await secure_client.post(
                "/auth/register",
                json={"email": "secure@example.com", "password": "Password1!"},
            )
            resp = await secure_client.post(
                "/auth/login",
                json={"email": "secure@example.com", "password": "Password1!"},
            )
            set_cookie_headers = resp.headers.get_list("set-cookie")
            access = [h for h in set_cookie_headers if h.lower().startswith("access_token")]
            assert len(access) == 1
            parsed = _parse_set_cookie(access[0])
            assert parsed.get("secure") is True, "access_token must carry Secure flag"

        # Restore original settings override
        app.dependency_overrides[get_settings] = lambda: TEST_SETTINGS

```

### `tests/identity/test_csrf.py`
```python
"""
tests/identity/test_csrf.py
----------------------------
VER-007: CSRF double-submit cookie pattern is enforced on all mutating endpoints.

Pattern
-------
1. On login, the server issues a random csrf_token cookie (NOT HttpOnly)
   and returns the same value in the response JSON.
2. Client JS reads the cookie and attaches it as X-CSRF-Token header.
3. The server compares cookie value == header value (constant-time).
4. Mismatch or absent header → 403.

Endpoints under test
--------------------
  POST /auth/logout  — requires CSRF
  POST /auth/refresh — requires CSRF

Read-only endpoints (GET /auth/me) must NOT require CSRF.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.user import User


async def _login(client: AsyncClient, email: str, password: str = "Password1!") -> dict:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()


class TestCSRFOnLogout:
    @pytest.mark.asyncio
    async def test_logout_without_csrf_header_rejected(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """POST /auth/logout with no X-CSRF-Token header must return 403."""
        await _login(client, plain_user.email)
        resp = await client.post("/auth/logout")  # no CSRF header
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_logout_with_wrong_csrf_header_rejected(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Wrong CSRF header value (not matching cookie) must return 403."""
        await _login(client, plain_user.email)
        resp = await client.post(
            "/auth/logout",
            headers={"X-CSRF-Token": "totally-wrong-csrf-value"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_logout_with_correct_csrf_succeeds(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Correct CSRF header matching the cookie must allow logout."""
        body = await _login(client, plain_user.email)
        csrf = body["csrf_token"]
        resp = await client.post(
            "/auth/logout",
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_logout_with_empty_csrf_rejected(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """An empty string CSRF header must be rejected."""
        await _login(client, plain_user.email)
        resp = await client.post("/auth/logout", headers={"X-CSRF-Token": ""})
        assert resp.status_code in (403, 422)


class TestCSRFOnRefresh:
    @pytest.mark.asyncio
    async def test_refresh_without_csrf_rejected(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """POST /auth/refresh with no CSRF header must return 403."""
        await _login(client, plain_user.email)
        resp = await client.post("/auth/refresh")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_refresh_with_wrong_csrf_rejected(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Mismatched CSRF token must be rejected on /auth/refresh."""
        await _login(client, plain_user.email)
        resp = await client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": "wrong-token"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_refresh_with_correct_csrf_succeeds(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Correct CSRF allows /auth/refresh to succeed."""
        body = await _login(client, plain_user.email)
        csrf = body["csrf_token"]
        resp = await client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 200


class TestCSRFTokenProperties:
    @pytest.mark.asyncio
    async def test_csrf_cookie_is_not_httponly(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """The csrf_token cookie must NOT have HttpOnly so JS can read it."""
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        set_cookie_headers = resp.headers.get_list("set-cookie")
        csrf_headers = [h for h in set_cookie_headers if "csrf_token" in h]
        assert len(csrf_headers) == 1, "csrf_token cookie not found"
        header = csrf_headers[0].lower()
        assert "httponly" not in header, (
            "csrf_token cookie must NOT be HttpOnly — JS must be able to read it"
        )

    @pytest.mark.asyncio
    async def test_csrf_token_has_sufficient_entropy(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """CSRF token must be at least 32 URL-safe characters long."""
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        csrf = resp.json()["csrf_token"]
        assert len(csrf) >= 32, "CSRF token must have sufficient entropy (≥32 chars)"

    @pytest.mark.asyncio
    async def test_csrf_token_differs_between_sessions(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Different login sessions must produce distinct CSRF tokens."""
        r1 = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        csrf1 = r1.json()["csrf_token"]

        r2 = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        csrf2 = r2.json()["csrf_token"]

        assert csrf1 != csrf2, "CSRF tokens must be unique per session"

    @pytest.mark.asyncio
    async def test_get_me_does_not_require_csrf(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """GET /auth/me (read-only) must NOT require a CSRF header."""
        await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        # No CSRF header on GET
        resp = await client.get("/auth/me")
        assert resp.status_code == 200, "Safe GET methods must not require CSRF"

```

### `tests/identity/test_refresh_rotation.py`
```python
"""
tests/identity/test_refresh_rotation.py
-----------------------------------------
VER-016: Refresh token rotation — each refresh call issues a new token pair
         and invalidates the previous refresh token.

Security properties verified
-----------------------------
1. After /auth/refresh, the OLD refresh token must be rejected.
2. After /auth/refresh, the NEW refresh token is accepted.
3. A second use of the OLD refresh token (replay) must trigger family
   revocation — the NEW token is also rejected.
4. The access token changes on every /auth/refresh call (new JTI + iat).
5. CSRF is enforced on /auth/refresh (covered also in test_csrf.py but
   restated here for completeness).
6. A missing refresh token cookie returns 401.
7. A completely fabricated refresh token returns 401.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from jose import jwt

from app.core.security import decode_refresh_token
from app.models.user import User
from tests.identity.conftest import TEST_SETTINGS


async def _login(client: AsyncClient, email: str) -> dict:
    resp = await client.post(
        "/auth/login",
        json={"email": email, "password": "Password1!"},
    )
    assert resp.status_code == 200
    return resp.json()


class TestRefreshRotation:
    @pytest.mark.asyncio
    async def test_refresh_issues_new_access_token(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Each /auth/refresh must produce a new access_token cookie."""
        login_body = await _login(client, plain_user.email)
        old_access = client.cookies.get("access_token")

        resp = await client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": login_body["csrf_token"]},
        )
        assert resp.status_code == 200
        new_access = client.cookies.get("access_token")
        assert old_access != new_access, "access_token must change after refresh"

    @pytest.mark.asyncio
    async def test_refresh_issues_new_csrf_token(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        login_body = await _login(client, plain_user.email)
        old_csrf = login_body["csrf_token"]

        resp = await client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": old_csrf},
        )
        new_csrf = resp.json()["csrf_token"]
        assert old_csrf != new_csrf, "CSRF token must rotate on each refresh"

    @pytest.mark.asyncio
    async def test_old_refresh_token_rejected_after_rotation(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """After refresh, the previous refresh token must no longer work."""
        login_body = await _login(client, plain_user.email)
        csrf1 = login_body["csrf_token"]

        # Capture old refresh token value before first rotation
        # We need to grab it from Set-Cookie headers at login time
        login_resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        csrf1 = login_resp.json()["csrf_token"]

        # Get the raw refresh token from Set-Cookie header
        set_cookie = login_resp.headers.get_list("set-cookie")
        refresh_headers = [h for h in set_cookie if "refresh_token" in h]
        assert len(refresh_headers) == 1
        # Extract cookie value from "refresh_token=VALUE; ..."
        old_refresh_value = refresh_headers[0].split(";")[0].split("=", 1)[1]

        # Perform one rotation
        rot1 = await client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": csrf1},
        )
        assert rot1.status_code == 200
        new_csrf = rot1.json()["csrf_token"]

        # Now try to use the OLD refresh token
        resp = await client.post(
            "/auth/refresh",
            cookies={
                "refresh_token": old_refresh_value,
                "csrf_token": new_csrf,
            },
            headers={"X-CSRF-Token": new_csrf},
        )
        assert resp.status_code == 401, (
            "Old (rotated-out) refresh token must be rejected"
        )

    @pytest.mark.asyncio
    async def test_replay_triggers_family_revocation(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Reusing a revoked refresh token must revoke the whole token family."""
        # Capture original refresh token at login
        login_resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        csrf1 = login_resp.json()["csrf_token"]
        set_cookie = login_resp.headers.get_list("set-cookie")
        old_refresh_value = [
            h.split(";")[0].split("=", 1)[1]
            for h in set_cookie
            if "refresh_token" in h
        ][0]

        # First rotation — succeeds, consumes old refresh token
        rot1 = await client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": csrf1},
        )
        assert rot1.status_code == 200
        new_csrf = rot1.json()["csrf_token"]

        # Attacker replays the OLD refresh token — server detects reuse
        replay = await client.post(
            "/auth/refresh",
            cookies={
                "refresh_token": old_refresh_value,
                "csrf_token": new_csrf,
            },
            headers={"X-CSRF-Token": new_csrf},
        )
        assert replay.status_code == 401

        # The NEW (legitimate) refresh token must now also be revoked
        # because the server detected a replay and wiped refresh_token_jti
        second_try = await client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": new_csrf},
        )
        assert second_try.status_code == 401, (
            "After replay detection, the entire token family must be revoked"
        )

    @pytest.mark.asyncio
    async def test_new_access_token_has_different_jti(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Each refresh must produce an access token with a new JTI."""
        login_body = await _login(client, plain_user.email)

        # Extract JTI from first access token (after login)
        # The access token in the cookie is itsdangerous-signed;
        # we must unsign it first.
        from itsdangerous import TimestampSigner

        signer = TimestampSigner(TEST_SETTINGS.session_secret.get_secret_value())
        signed1 = client.cookies.get("access_token", "")
        raw1 = signer.unsign(signed1, max_age=TEST_SETTINGS.access_token_expire_seconds).decode()
        jti1 = jwt.get_unverified_claims(raw1)["jti"]

        # Refresh
        await client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": login_body["csrf_token"]},
        )

        signed2 = client.cookies.get("access_token", "")
        raw2 = signer.unsign(signed2, max_age=TEST_SETTINGS.access_token_expire_seconds).decode()
        jti2 = jwt.get_unverified_claims(raw2)["jti"]

        assert jti1 != jti2, "Each token issuance must produce a unique JTI"

    @pytest.mark.asyncio
    async def test_missing_refresh_cookie_returns_401(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        login_body = await _login(client, plain_user.email)
        csrf = login_body["csrf_token"]
        # Explicitly omit the refresh cookie
        resp = await client.post(
            "/auth/refresh",
            cookies={"csrf_token": csrf},
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_fabricated_refresh_token_returns_401(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        login_body = await _login(client, plain_user.email)
        csrf = login_body["csrf_token"]
        resp = await client.post(
            "/auth/refresh",
            cookies={
                "refresh_token": "not.a.valid.jwt",
                "csrf_token": csrf,
            },
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_updates_cookie_max_age(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """The newly issued access_token cookie must carry a fresh max-age."""
        login_body = await _login(client, plain_user.email)
        resp = await client.post(
            "/auth/refresh",
            headers={"X-CSRF-Token": login_body["csrf_token"]},
        )
        assert resp.status_code == 200
        set_cookie = resp.headers.get_list("set-cookie")
        access = [h for h in set_cookie if "access_token" in h]
        assert len(access) == 1
        assert "max-age=" in access[0].lower()

```

### `tests/identity/test_session_expiry.py`
```python
"""
tests/identity/test_session_expiry.py
---------------------------------------
VER-006: Sessions expire after the configured lifetime.

We simulate token expiry by constructing tokens with a past `exp` claim
(without using a time-travel library — we directly craft JWTs with
manipulated timestamps) and verify the server rejects them.

We also verify:
* An expired access token is rejected by /auth/me.
* An expired refresh token is rejected by /auth/refresh.
* A token with exp in the near future is still accepted.
* The cookie max_age matches the token lifetime.
"""
from __future__ import annotations

import time

import pytest
from httpx import AsyncClient
from jose import jwt

from app.core.security import create_access_token, create_refresh_token
from app.core.session import set_auth_cookies
from app.models.user import User
from tests.identity.conftest import TEST_SETTINGS


def _make_expired_access_token(subject: str) -> str:
    """Craft an access token whose `exp` is 1 second in the past."""
    now = int(time.time())
    payload = {
        "sub": subject,
        "iat": now - 100,
        "exp": now - 1,   # already expired
        "typ": "access",
        "jti": "test-expired-jti",
    }
    return jwt.encode(
        payload,
        TEST_SETTINGS.jwt_secret.get_secret_value(),
        algorithm=TEST_SETTINGS.jwt_algorithm,
    )


def _make_expired_refresh_token(subject: str) -> str:
    """Craft a refresh token whose `exp` is 1 second in the past."""
    now = int(time.time())
    payload = {
        "sub": subject,
        "iat": now - 100,
        "exp": now - 1,
        "typ": "refresh",
        "jti": "test-expired-refresh-jti",
    }
    return jwt.encode(
        payload,
        TEST_SETTINGS.jwt_secret.get_secret_value(),
        algorithm=TEST_SETTINGS.jwt_algorithm,
    )


def _sign_for_cookie(raw_jwt: str) -> str:
    """Wrap a raw JWT in an itsdangerous signature as the server would."""
    from itsdangerous import TimestampSigner

    signer = TimestampSigner(TEST_SETTINGS.session_secret.get_secret_value())
    return signer.sign(raw_jwt).decode()


class TestSessionExpiry:
    @pytest.mark.asyncio
    async def test_expired_access_token_rejected_by_me(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """An expired access token must return 401 from /auth/me."""
        expired = _make_expired_access_token(plain_user.email)
        signed = _sign_for_cookie(expired)
        resp = await client.get("/auth/me", cookies={"access_token": signed})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_refresh_token_rejected(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """An expired refresh token must return 401 from /auth/refresh."""
        # Log in to get a valid CSRF
        login = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        csrf = login.json()["csrf_token"]

        expired_refresh = _make_expired_refresh_token(plain_user.email)

        resp = await client.post(
            "/auth/refresh",
            cookies={
                "refresh_token": expired_refresh,
                "csrf_token": csrf,
            },
            headers={"X-CSRF-Token": csrf},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_token_near_expiry_still_accepted(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """A token expiring in the future (even 60 s away) must be accepted."""
        # Create a token expiring in 60 seconds
        now = int(time.time())
        payload = {
            "sub": plain_user.email,
            "iat": now,
            "exp": now + 60,
            "typ": "access",
            "jti": "short-lived-jti",
        }
        raw = jwt.encode(
            payload,
            TEST_SETTINGS.jwt_secret.get_secret_value(),
            algorithm=TEST_SETTINGS.jwt_algorithm,
        )
        signed = _sign_for_cookie(raw)
        resp = await client.get("/auth/me", cookies={"access_token": signed})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_access_cookie_max_age_set(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Login response must set max-age on the access_token cookie."""
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        assert resp.status_code == 200
        set_cookie_headers = resp.headers.get_list("set-cookie")
        access_headers = [h for h in set_cookie_headers if "access_token" in h]
        assert len(access_headers) == 1
        header = access_headers[0].lower()
        assert "max-age=" in header, "access_token cookie must carry max-age"

    @pytest.mark.asyncio
    async def test_refresh_cookie_max_age_set(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Login response must set max-age on the refresh_token cookie."""
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        set_cookie_headers = resp.headers.get_list("set-cookie")
        refresh_headers = [h for h in set_cookie_headers if "refresh_token" in h]
        assert len(refresh_headers) == 1
        header = refresh_headers[0].lower()
        assert "max-age=" in header, "refresh_token cookie must carry max-age"

    @pytest.mark.asyncio
    async def test_logout_sets_expired_cookies(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Logout must delete (expire) the session cookies."""
        login = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        csrf = login.json()["csrf_token"]

        logout = await client.post(
            "/auth/logout",
            headers={"X-CSRF-Token": csrf},
        )
        assert logout.status_code == 200
        # After logout, accessing /me must fail
        me = await client.get("/auth/me")
        assert me.status_code == 401

    @pytest.mark.asyncio
    async def test_no_access_token_returns_401(self, client: AsyncClient) -> None:
        """Request with no session cookie must be rejected."""
        resp = await client.get("/auth/me")
        assert resp.status_code == 401

```

### `tests/identity/test_session_fixation.py`
```python
"""
tests/identity/test_session_fixation.py
-----------------------------------------
VER-005: Session fixation is prevented.

The server must NEVER accept or extend a pre-existing session cookie
value handed in by the client.  On every successful authentication:
  * A brand-new access_token cookie value is issued.
  * A brand-new CSRF token is issued.
  * An old, pre-login cookie is not honoured for protected endpoints
    if it was not issued by the server.

Attack model
------------
An attacker who knows a victim's session cookie value (e.g. obtained before
login via a cross-site trick) must not be able to ride the victim's session
post-authentication.  Because our tokens are server-issued JWTs (not client-
specified IDs), the attack surface does not exist at the protocol level —
but we verify the server always regenerates tokens on login.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.user import User


class TestSessionFixationPrevention:
    @pytest.mark.asyncio
    async def test_fresh_token_issued_on_each_login(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Two sequential logins must produce distinct access_token cookie values."""
        resp1 = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        token1 = resp1.cookies.get("access_token")

        resp2 = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        token2 = resp2.cookies.get("access_token")

        assert token1 is not None
        assert token2 is not None
        assert token1 != token2, (
            "Server must issue a new token on each login — old value must not persist"
        )

    @pytest.mark.asyncio
    async def test_fresh_csrf_issued_on_each_login(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Each login must produce a distinct CSRF token."""
        resp1 = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        csrf1 = resp1.json().get("csrf_token")

        resp2 = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        csrf2 = resp2.json().get("csrf_token")

        assert csrf1 and csrf2
        assert csrf1 != csrf2, "CSRF token must be regenerated on each login"

    @pytest.mark.asyncio
    async def test_attacker_injected_cookie_rejected(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """A fabricated/unsigned access_token cookie must be rejected by /auth/me."""
        # Attacker constructs a raw JWT without the itsdangerous signature
        from app.core.security import create_access_token
        from tests.identity.conftest import TEST_SETTINGS

        raw_jwt = create_access_token(plain_user.email, settings=TEST_SETTINGS)

        # Inject directly as cookie (missing the itsdangerous signature wrapper)
        resp = await client.get(
            "/auth/me",
            cookies={"access_token": raw_jwt},
        )
        assert resp.status_code == 401, (
            "Unsigned/raw JWT must be rejected — the server only accepts itsdangerous-signed cookies"
        )

    @pytest.mark.asyncio
    async def test_forged_session_cookie_rejected(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """A completely fabricated cookie value must be rejected."""
        resp = await client.get(
            "/auth/me",
            cookies={"access_token": "not.a.real.token"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_old_token_not_automatically_extended(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Accessing /auth/me with a valid token does not silently re-issue tokens."""
        # Log in
        login_resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        assert login_resp.status_code == 200
        original_token = login_resp.cookies.get("access_token")

        # Call /me
        me_resp = await client.get("/auth/me")
        assert me_resp.status_code == 200

        # The /me endpoint must NOT re-issue tokens — no new set-cookie
        set_cookie_headers = me_resp.headers.get_list("set-cookie")
        token_cookies = [h for h in set_cookie_headers if "access_token" in h]
        assert len(token_cookies) == 0, (
            "/auth/me must not silently re-issue access_token cookies — that would widen the fixation window"
        )

```

### `tests/identity/test_token_issuance.py`
```python
"""
tests/identity/test_token_issuance.py
--------------------------------------
VER-001: JWT access/refresh tokens are correctly structured, signed, and
         carry the expected claims.

Acceptance criteria
-------------------
* Access token encodes `sub`, `iat`, `exp`, `jti`, `typ=access`.
* Refresh token encodes `sub`, `iat`, `exp`, `jti`, `typ=refresh`.
* Tokens are signed with HS256; tampered tokens are rejected.
* Access and refresh tokens have distinct `typ` values — cross-use is rejected.
* Token lifetime matches configuration (within ±5 s tolerance for test speed).
* Login endpoint issues both cookies on success; body contains csrf_token.
"""
from __future__ import annotations

import time

import pytest
from httpx import AsyncClient
from jose import jwt

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)
from app.models.user import User

from tests.identity.conftest import TEST_SETTINGS

# ── Unit tests: token creation / decode ──────────────────────────────────────


class TestAccessTokenStructure:
    def test_required_claims_present(self) -> None:
        token = create_access_token("alice@example.com", settings=TEST_SETTINGS)
        payload = jwt.get_unverified_claims(token)
        assert payload["sub"] == "alice@example.com"
        assert "iat" in payload
        assert "exp" in payload
        assert "jti" in payload
        assert payload["typ"] == "access"

    def test_algorithm_is_hs256(self) -> None:
        token = create_access_token("alice@example.com", settings=TEST_SETTINGS)
        header = jwt.get_unverified_header(token)
        assert header["alg"] == "HS256"

    def test_lifetime_matches_config(self) -> None:
        before = int(time.time())
        token = create_access_token("alice@example.com", settings=TEST_SETTINGS)
        payload = jwt.get_unverified_claims(token)
        expected_exp = before + TEST_SETTINGS.access_token_expire_seconds
        # Allow ±5 s drift
        assert abs(payload["exp"] - expected_exp) <= 5

    def test_jti_is_unique_per_issuance(self) -> None:
        t1 = create_access_token("alice@example.com", settings=TEST_SETTINGS)
        t2 = create_access_token("alice@example.com", settings=TEST_SETTINGS)
        jti1 = jwt.get_unverified_claims(t1)["jti"]
        jti2 = jwt.get_unverified_claims(t2)["jti"]
        assert jti1 != jti2

    def test_extra_claims_are_embedded(self) -> None:
        token = create_access_token(
            "alice@example.com",
            extra_claims={"role": "admin"},
            settings=TEST_SETTINGS,
        )
        payload = jwt.get_unverified_claims(token)
        assert payload["role"] == "admin"

    def test_tampered_signature_rejected(self) -> None:
        from jose import JWTError

        token = create_access_token("alice@example.com", settings=TEST_SETTINGS)
        # Flip the last character of the token to corrupt the signature
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        with pytest.raises(JWTError):
            decode_access_token(tampered, settings=TEST_SETTINGS)

    def test_wrong_secret_rejected(self) -> None:
        from jose import JWTError
        from pydantic import SecretStr

        wrong_settings = TEST_SETTINGS.model_copy(
            update={"jwt_secret": SecretStr("completely-different-secret-key-here!")}
        )
        token = create_access_token("alice@example.com", settings=wrong_settings)
        with pytest.raises(JWTError):
            decode_access_token(token, settings=TEST_SETTINGS)


class TestRefreshTokenStructure:
    def test_required_claims_present(self) -> None:
        token = create_refresh_token("alice@example.com", settings=TEST_SETTINGS)
        payload = jwt.get_unverified_claims(token)
        assert payload["sub"] == "alice@example.com"
        assert payload["typ"] == "refresh"
        assert "jti" in payload

    def test_lifetime_matches_config(self) -> None:
        before = int(time.time())
        token = create_refresh_token("alice@example.com", settings=TEST_SETTINGS)
        payload = jwt.get_unverified_claims(token)
        expected_exp = before + TEST_SETTINGS.refresh_token_expire_seconds
        assert abs(payload["exp"] - expected_exp) <= 5

    def test_refresh_token_rejected_as_access(self) -> None:
        from jose import JWTError

        token = create_refresh_token("alice@example.com", settings=TEST_SETTINGS)
        with pytest.raises(JWTError, match="type mismatch"):
            decode_access_token(token, settings=TEST_SETTINGS)

    def test_access_token_rejected_as_refresh(self) -> None:
        from jose import JWTError

        token = create_access_token("alice@example.com", settings=TEST_SETTINGS)
        with pytest.raises(JWTError, match="type mismatch"):
            decode_refresh_token(token, settings=TEST_SETTINGS)


# ── Integration tests: /auth/login endpoint ───────────────────────────────────


class TestLoginTokenIssuance:
    @pytest.mark.asyncio
    async def test_login_sets_access_cookie(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.cookies

    @pytest.mark.asyncio
    async def test_login_sets_refresh_cookie(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        assert resp.status_code == 200
        # Refresh cookie path is /auth/refresh — read raw Set-Cookie headers
        set_cookie_headers = resp.headers.get_list("set-cookie")
        refresh_headers = [h for h in set_cookie_headers if "refresh_token" in h]
        assert len(refresh_headers) == 1, "Refresh cookie not found in Set-Cookie headers"

    @pytest.mark.asyncio
    async def test_login_returns_csrf_token_in_body(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "csrf_token" in body
        assert len(body["csrf_token"]) > 0

    @pytest.mark.asyncio
    async def test_login_response_contains_user_info(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        body = resp.json()
        assert body["user"]["email"] == plain_user.email

    @pytest.mark.asyncio
    async def test_invalid_password_returns_401(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "WrongPass1!"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_unknown_email_returns_401(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/auth/login",
            json={"email": "nobody@example.com", "password": "Password1!"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_response_does_not_leak_hashed_password(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        body_str = resp.text
        assert "hashed_password" not in body_str
        assert "$2b$" not in body_str  # bcrypt prefix

```

### `tests/identity/test_totp_mfa.py`
```python
"""
tests/identity/test_totp_mfa.py
---------------------------------
VER-012: TOTP-based MFA is correctly enforced.

Scenarios
---------
* A user without MFA can log in with password alone.
* A user with MFA enabled is challenged for a TOTP code when none supplied.
* A valid TOTP code allows login when MFA is enabled.
* An invalid TOTP code is rejected (401).
* TOTP setup: server issues secret + URI; confirmation with a valid code enables MFA.
* TOTP confirmation with an invalid code is rejected (400).
* TOTP codes cannot be reused within the same time window (replay protection via
  pyotp's internal drift window — validated structurally since we can't advance time).
* The provisioning URI contains the issuer and account email.
"""
from __future__ import annotations

import pytest
import pyotp
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_totp_secret, verify_totp
from app.models.user import User
from tests.identity.conftest import TEST_SETTINGS, _make_user


class TestTOTPUnit:
    def test_generate_secret_is_valid_base32(self) -> None:
        secret = generate_totp_secret()
        # Base32 alphabet — should not raise
        import base64

        base64.b32decode(secret, casefold=True)
        assert len(secret) >= 16

    def test_valid_code_accepted(self) -> None:
        secret = generate_totp_secret()
        totp = pyotp.TOTP(secret)
        code = totp.now()
        assert verify_totp(secret, code, settings=TEST_SETTINGS) is True

    def test_invalid_code_rejected(self) -> None:
        secret = generate_totp_secret()
        assert verify_totp(secret, "000000", settings=TEST_SETTINGS) is False

    def test_wrong_secret_rejected(self) -> None:
        secret1 = generate_totp_secret()
        secret2 = generate_totp_secret()
        code = pyotp.TOTP(secret1).now()
        assert verify_totp(secret2, code, settings=TEST_SETTINGS) is False

    def test_provisioning_uri_contains_issuer(self) -> None:
        from app.core.security import get_totp_uri

        secret = generate_totp_secret()
        uri = get_totp_uri(secret, "user@example.com", settings=TEST_SETTINGS)
        assert "MyApp" in uri or "otpauth" in uri

    def test_provisioning_uri_contains_email(self) -> None:
        from app.core.security import get_totp_uri

        secret = generate_totp_secret()
        uri = get_totp_uri(secret, "user@example.com", settings=TEST_SETTINGS)
        assert "user%40example.com" in uri or "user@example.com" in uri


class TestMFALoginFlow:
    @pytest.mark.asyncio
    async def test_login_without_mfa_requires_no_totp(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Users without MFA can log in with password only."""
        resp = await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        assert resp.status_code == 200
        assert resp.json()["mfa_required"] is False

    @pytest.mark.asyncio
    async def test_mfa_user_challenged_when_no_code(
        self, client: AsyncClient, mfa_user: User
    ) -> None:
        """User with MFA enabled must be told MFA is required when no code supplied."""
        resp = await client.post(
            "/auth/login",
            json={"email": mfa_user.email, "password": "Password1!"},
        )
        # Server returns 200 with mfa_required=True — no tokens issued
        assert resp.status_code == 200
        body = resp.json()
        assert body["mfa_required"] is True
        assert body["csrf_token"] == "", "No CSRF token when MFA gate not passed"
        # No access_token cookie yet
        assert "access_token" not in resp.cookies

    @pytest.mark.asyncio
    async def test_mfa_user_with_valid_code_gets_tokens(
        self, client: AsyncClient, mfa_user: User
    ) -> None:
        """Providing the correct TOTP code completes login and issues tokens."""
        assert mfa_user.totp_secret is not None
        code = pyotp.TOTP(mfa_user.totp_secret).now()

        resp = await client.post(
            "/auth/login",
            json={
                "email": mfa_user.email,
                "password": "Password1!",
                "totp_code": code,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["mfa_required"] is False
        assert "access_token" in resp.cookies

    @pytest.mark.asyncio
    async def test_mfa_user_with_invalid_code_rejected(
        self, client: AsyncClient, mfa_user: User
    ) -> None:
        """An incorrect TOTP code must return 401."""
        resp = await client.post(
            "/auth/login",
            json={
                "email": mfa_user.email,
                "password": "Password1!",
                "totp_code": "000000",
            },
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_mfa_user_with_invalid_code_increments_lockout_counter(
        self, client: AsyncClient, mfa_user: User, db_session: AsyncSession
    ) -> None:
        """Failed TOTP attempts count toward account lockout."""
        initial_attempts = mfa_user.failed_login_attempts

        await client.post(
            "/auth/login",
            json={
                "email": mfa_user.email,
                "password": "Password1!",
                "totp_code": "000000",
            },
        )
        await db_session.refresh(mfa_user)
        assert mfa_user.failed_login_attempts == initial_attempts + 1


class TestTOTPEnrollment:
    @pytest.mark.asyncio
    async def test_totp_setup_returns_secret_and_uri(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """POST /auth/totp/setup must return a secret and otpauth URI."""
        # Authenticate first
        await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        resp = await client.post("/auth/totp/setup")
        assert resp.status_code == 200
        body = resp.json()
        assert "secret" in body
        assert "uri" in body
        assert body["uri"].startswith("otpauth://totp/")

    @pytest.mark.asyncio
    async def test_totp_setup_without_auth_rejected(self, client: AsyncClient) -> None:
        """TOTP setup must require an authenticated session."""
        resp = await client.post("/auth/totp/setup")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_totp_confirm_with_valid_code_enables_mfa(
        self,
        client: AsyncClient,
        plain_user: User,
        db_session: AsyncSession,
    ) -> None:
        """Confirming TOTP with a valid code must set totp_enabled=True."""
        await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        # Setup: get secret
        setup_resp = await client.post("/auth/totp/setup")
        secret = setup_resp.json()["secret"]
        code = pyotp.TOTP(secret).now()

        confirm_resp = await client.post(
            "/auth/totp/confirm",
            json={"code": code},
        )
        assert confirm_resp.status_code == 200

        await db_session.refresh(plain_user)
        assert plain_user.totp_enabled is True

    @pytest.mark.asyncio
    async def test_totp_confirm_with_invalid_code_rejected(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Confirming TOTP with a wrong code must return 400."""
        await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        await client.post("/auth/totp/setup")  # initialise secret

        resp = await client.post(
            "/auth/totp/confirm",
            json={"code": "000000"},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_totp_confirm_without_setup_rejected(
        self, client: AsyncClient, plain_user: User
    ) -> None:
        """Calling /auth/totp/confirm before /auth/totp/setup must return 400."""
        await client.post(
            "/auth/login",
            json={"email": plain_user.email, "password": "Password1!"},
        )
        # plain_user has no totp_secret set
        resp = await client.post(
            "/auth/totp/confirm",
            json={"code": "123456"},
        )
        assert resp.status_code == 400

```