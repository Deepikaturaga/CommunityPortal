# Implementation Report

The backend uses an older setuptools. Let me fix the build system:

## Verification
- `python3 -c "
import os
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in {'.git','__pycache__','.mypy_cache','.pytest_cache','node_modules','.venv','venv'}]
    for f in files:
        print(os.path.join(root, f))
"` → exit 0
- `python3 -c "
import os, sys
results = []
for root, dirs, files in os.walk('/'):
    dirs[:] = [d for d in dirs if d not in {'.git','__pycache__','.mypy_cache','.pytest_cache','node_modules','.venv','venv','proc','sys','dev','run','tmp'}]
    for f in files:
        p = os.path.join(root, f)
        if 'backend' in p or 'app' in p or 'test' in p.lower():
            results.append(p)
for r in sorted(results)[:150]:
    print(r)
"` → exit 0
- `python3 -c "
import os
results = []
for root, dirs, files in os.walk('/workspace'):
    dirs[:] = [d for d in dirs if d not in {'.git','__pycache__','.mypy_cache','.pytest_cache','node_modules','.venv','venv'}]
    for f in files:
        results.append(os.path.join(root, f))
for r in sorted(results)[:200]:
    print(r)
"` → exit 0
- `python3 -c "
import os
cwd = os.getcwd()
print('CWD:', cwd)
items = os.listdir(cwd)
print('Root items:', sorted(items))
"` → exit 0
- `python3 -c "import sys; print(sys.version)"` → exit 0
- `pip3 list 2>/dev/null` → exit 0
- `pip3 list 2>/dev/null` → exit 0
- `pip3 show fastapi pydantic passlib httpx pytest pytest-asyncio anyio 2>/dev/null` → exit 0
- `pip3 show bcrypt aiosqlite sqlalchemy pydantic-settings 2>/dev/null` → exit 0
- `pip3 show backend identity-service api-edge 2>/dev/null` → exit 0
- `python3 -c "
import os
results = []
for root, dirs, files in os.walk('/tmp/archpilot_verify_zlautyjj/backend'):
    dirs[:] = [d for d in dirs if d not in {'__pycache__','.mypy_cache','.pytest_cache','.venv','venv'}]
    for f in files:
        results.append(os.path.join(root, f))
for r in sorted(results):
    print(r)
"` → exit 0
- `python3 -c "
import os
d = '/tmp/archpilot_verify_zlautyjj/backend'
print('exists:', os.path.exists(d))
print('listdir:', os.listdir(d) if os.path.exists(d) else 'N/A')
"` → exit 0
- `python3 -c "
import importlib.util, sys
spec = importlib.util.find_spec('app')
print('app spec:', spec)
import site
print('site-packages:', site.getsitepackages())
"` → exit 0
- `python3 -c "
import os
sp = '/usr/local/lib/python3.12/site-packages'
# look for backend-related packages
for item in sorted(os.listdir(sp)):
    if any(k in item.lower() for k in ['backend','app','fastapi','identity','edge','alembic']):
        print(item)
"` → exit 0
- `python3 -c "
sp = '/usr/local/lib/python3.12/site-packages'
import os
# read the pth files to find editable install paths
for f in ['__editable__.backend-0.1.0.pth', 'identity_service.pth']:
    fpath = os.path.join(sp, f)
    if os.path.exists(fpath):
        print(f'=== {f} ===')
        print(open(fpath).read())
"` → exit 0
- `python3 -c "
import __editable___backend_0_1_0_finder as f
print(dir(f))
# try to get path
import inspect
print(inspect.getfile(f))
src = open(inspect.getfile(f)).read()
print(src)
"` → exit 0
- `python3 -c "
import os
results = []
base = '/tmp/archpilot_verify_zlautyjj'
for root, dirs, files in os.walk(base):
    dirs[:] = [d for d in dirs if d not in {'__pycache__','.mypy_cache','.pytest_cache','.venv','venv','.git'}]
    for f in files:
        results.append(os.path.join(root, f))
for r in sorted(results):
    print(r)
"` → exit 0
- `python3 -c "
import os
base = '/tmp/archpilot_verify_zlautyjj'
print('exists:', os.path.exists(base))
import glob
hits = glob.glob('/tmp/archpilot_verify_*', recursive=False)
print('all archpilot_verify dirs:', hits)
"` → exit 0
- `python3 -c "
import os
results = []
base = '/tmp/archpilot_verify_zrc40wcm'
for root, dirs, files in os.walk(base):
    dirs[:] = [d for d in dirs if d not in {'__pycache__','.mypy_cache','.pytest_cache','.venv','venv','.git'}]
    for f in files:
        results.append(os.path.join(root, f))
for r in sorted(results):
    print(r)
"` → exit 0
- `python3 -c "
import os
base = '/tmp/archpilot_verify_zrc40wcm'
print('listdir:', os.listdir(base))
"` → exit 1
- `python3 -c "
import app
print(app.__file__)
import os
print(os.listdir(os.path.dirname(app.__file__)))
"` → exit 1
- `python3 -c "
import os
sp = '/usr/local/lib/python3.12/site-packages'
# read backend dist-info
bdir = os.path.join(sp, 'backend-0.1.0.dist-info')
for f in os.listdir(bdir):
    fpath = os.path.join(bdir, f)
    print(f'=== {f} ===')
    print(open(fpath).read()[:3000])
    print()
"` → exit 0
- `python3 -c "
import os
sp = '/usr/local/lib/python3.12/site-packages'
for dname in ['api_edge-0.1.0.dist-info', 'identity_service-0.1.0.dist-info']:
    d = os.path.join(sp, dname)
    if os.path.exists(d):
        for f in ['METADATA','RECORD','direct_url.json']:
            fpath = os.path.join(d, f)
            if os.path.exists(fpath):
                print(f'=== {dname}/{f} ===')
                print(open(fpath).read()[:2000])
"` → exit 0
- `python3 -c "
import os
sp = '/usr/local/lib/python3.12/site-packages'
f = open(os.path.join(sp, '__editable___api_edge_0_1_0_finder.py')).read()
import re
m = re.search(r\"MAPPING = (.+)\", f)
print('api-edge mapping:', m.group(1) if m else 'not found')
"` → exit 0
- `python3 -c "
import os
sp = '/usr/local/lib/python3.12/site-packages'
print(open(os.path.join(sp, '__editable___api_edge_0_1_0_finder.py')).read()[:2000])
"` → exit 0
- `pip install -e ".[dev]" --quiet` → exit 2

## Generated Files

### `backend/.env.example`
```text
SECRET_KEY=dev-secret-key-change-in-production-min-32-chars!!
DATABASE_URL=sqlite+aiosqlite:///./dev.db
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

```

### `backend/app/__init__.py`
```python
"""App package."""

```

### `backend/app/auth/__init__.py`
```python
from app.auth.dependencies import get_current_user, require_min_role, require_role
from app.auth.passwords import hash_password, verify_password

__all__ = [
    "get_current_user",
    "require_role",
    "require_min_role",
    "hash_password",
    "verify_password",
]

```

### `backend/app/auth/dependencies.py`
```python
"""FastAPI dependencies for authentication and role-based authorization."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.enums import UserRole
from app.models.user import User

_bearer = HTTPBearer(auto_error=True)

_ROLE_RANK: dict[UserRole, int] = {
    UserRole.VIEWER: 0,
    UserRole.CONTRIBUTOR: 1,
    UserRole.EDITOR: 2,
    UserRole.ADMIN: 3,
    UserRole.SUPERADMIN: 4,
}


async def _get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(creds.credentials)
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


# Convenience typed alias
get_current_user = _get_current_user


def require_role(*roles: UserRole):
    """Return a dependency that enforces the caller has one of the given roles."""

    async def _check(current_user: User = Depends(_get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role '{current_user.role}' is not authorised for this operation. "
                    f"Required: {[r.value for r in roles]}"
                ),
            )
        return current_user

    return _check


def require_min_role(min_role: UserRole):
    """Return a dependency that enforces the caller's role rank >= min_role rank."""

    async def _check(current_user: User = Depends(_get_current_user)) -> User:
        if _ROLE_RANK[current_user.role] < _ROLE_RANK[min_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role '{current_user.role}' insufficient. "
                    f"Minimum required: '{min_role.value}'"
                ),
            )
        return current_user

    return _check

```

### `backend/app/auth/passwords.py`
```python
"""Password hashing utilities using passlib/bcrypt."""
from __future__ import annotations

from passlib.context import CryptContext

_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _ctx.verify(plain, hashed)

```

### `backend/app/core/__init__.py`
```python
from app.core.config import *  # noqa: F401, F403
from app.core.database import *  # noqa: F401, F403

```

### `backend/app/core/config.py`
```python
"""Application configuration validated at startup via pydantic-settings."""
from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Security
    secret_key: str = "dev-secret-key-change-in-production-min-32-chars!!"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Database
    database_url: str = "sqlite+aiosqlite:///./test.db"

    @field_validator("secret_key")
    @classmethod
    def _secret_key_min_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("secret_key must be at least 32 characters")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()

```

### `backend/app/core/database.py`
```python
"""Async SQLAlchemy engine + session factory."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _make_engine(url: str | None = None):
    settings = get_settings()
    db_url = url or settings.database_url
    connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
    return create_async_engine(db_url, echo=False, connect_args=connect_args)


# Module-level engine – overridden in tests via dependency override
_engine = _make_engine()
_session_factory = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _session_factory() as session:
        yield session


async def create_all_tables() -> None:
    """Create all tables (dev/test only)."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables() -> None:
    """Drop all tables (test only)."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

```

### `backend/app/core/exceptions.py`
```python
"""Shared exception types and global handlers."""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class NotFoundError(Exception):
    def __init__(self, detail: str = "Not found") -> None:
        self.detail = detail


class ForbiddenError(Exception):
    def __init__(self, detail: str = "Forbidden") -> None:
        self.detail = detail


class ConflictError(Exception):
    def __init__(self, detail: str = "Conflict") -> None:
        self.detail = detail


async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": exc.detail})


async def forbidden_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": exc.detail})


async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": exc.detail})

```

### `backend/app/core/security.py`
```python
"""JWT token utilities."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.core.config import get_settings


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify token; raises JWTError on failure."""
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


__all__ = ["create_access_token", "decode_access_token", "JWTError"]

```

### `backend/app/main.py`
```python
"""ASGI application entry-point."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import create_all_tables
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    conflict_handler,
    forbidden_handler,
    not_found_handler,
)
from app.routers.admin_router import router as admin_router
from app.routers.auth_router import router as auth_router
from app.routers.profile_router import router as profile_router
from app.routers.taxonomy_router import router as taxonomy_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Dev/test convenience – create tables on startup
    await create_all_tables()
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Backend API",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS – tighten in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handlers
    app.add_exception_handler(NotFoundError, not_found_handler)  # type: ignore[arg-type]
    app.add_exception_handler(ForbiddenError, forbidden_handler)  # type: ignore[arg-type]
    app.add_exception_handler(ConflictError, conflict_handler)  # type: ignore[arg-type]

    api_prefix = "/api/v1"
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(profile_router, prefix=api_prefix)
    app.include_router(admin_router, prefix=api_prefix)
    app.include_router(taxonomy_router, prefix=api_prefix)

    @app.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

```

### `backend/app/models/__init__.py`
```python
"""Models package – import all ORM models so Alembic autogenerate picks them up."""
from app.models.enums import UserRole
from app.models.taxonomy import TaxonomyTerm, TaxonomyVocabulary
from app.models.user import User

__all__ = ["User", "UserRole", "TaxonomyVocabulary", "TaxonomyTerm"]

```

### `backend/app/models/enums.py`
```python
"""User role enumeration – five canonical roles."""
from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    """Five roles used across profile / admin / taxonomy authorization."""

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    EDITOR = "editor"
    CONTRIBUTOR = "contributor"
    VIEWER = "viewer"

```

### `backend/app/models/taxonomy.py`
```python
"""Taxonomy ORM models."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TaxonomyVocabulary(Base):
    """Top-level vocabulary (e.g. 'genre', 'topic')."""

    __tablename__ = "taxonomy_vocabularies"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    terms: Mapped[list["TaxonomyTerm"]] = relationship(
        "TaxonomyTerm", back_populates="vocabulary", lazy="select", cascade="all, delete-orphan"
    )


class TaxonomyTerm(Base):
    """Term belonging to a vocabulary."""

    __tablename__ = "taxonomy_terms"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    vocabulary_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("taxonomy_vocabularies.id", ondelete="CASCADE"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    vocabulary: Mapped["TaxonomyVocabulary"] = relationship(
        "TaxonomyVocabulary", back_populates="terms"
    )
    created_by_user: Mapped["User | None"] = relationship(  # noqa: F821
        "User", back_populates="taxonomy_terms"
    )

```

### `backend/app/models/user.py`
```python
"""User ORM model."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole"), nullable=False, default=UserRole.VIEWER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    taxonomy_terms: Mapped[list["TaxonomyTerm"]] = relationship(  # noqa: F821
        "TaxonomyTerm", back_populates="created_by_user", lazy="select"
    )

```

### `backend/app/routers/__init__.py`
```python
from app.routers.auth_router import router as auth_router
from app.routers.admin_router import router as admin_router
from app.routers.profile_router import router as profile_router
from app.routers.taxonomy_router import router as taxonomy_router

__all__ = ["auth_router", "admin_router", "profile_router", "taxonomy_router"]

```

### `backend/app/routers/admin_router.py`
```python
"""Admin router – /api/v1/admin endpoints.

Authorization matrix:
  GET    /admin/users          → ADMIN, SUPERADMIN
  POST   /admin/users          → SUPERADMIN only
  PATCH  /admin/users/{id}     → ADMIN (role/is_active), SUPERADMIN
  DELETE /admin/users/{id}     → SUPERADMIN only
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_min_role, require_role
from app.auth.passwords import hash_password
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user_schemas import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserRead], summary="List all users")
async def list_users(
    _caller: User = Depends(require_min_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> list[UserRead]:
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [UserRead.model_validate(u) for u in users]


@router.post(
    "/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user (superadmin only)",
)
async def create_user(
    body: UserCreate,
    _caller: User = Depends(require_role(UserRole.SUPERADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        email=body.email,
        full_name=body.full_name,
        role=body.role,
        hashed_password=hash_password(body.password),
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserRead.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserRead, summary="Update a user")
async def update_user(
    user_id: str,
    body: UserUpdate,
    _caller: User = Depends(require_min_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if body.full_name is not None:
        user.full_name = body.full_name
    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserRead.model_validate(user)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user (superadmin only)",
)
async def delete_user(
    user_id: str,
    _caller: User = Depends(require_role(UserRole.SUPERADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await db.delete(user)
    await db.commit()

```

### `backend/app/routers/auth_router.py`
```python
"""Authentication router – login / token endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.passwords import verify_password
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.user_schemas import TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == form.username))
    user: User | None = result.scalar_one_or_none()
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    token = create_access_token(subject=user.id, extra_claims={"role": user.role.value})
    return TokenResponse(access_token=token)

```

### `backend/app/routers/profile_router.py`
```python
"""Profile router – /api/v1/profile endpoints.

Authorization matrix:
  GET    /profile/me       → any authenticated user (all 5 roles)
  PATCH  /profile/me       → any authenticated user (self-service: full_name only)
  GET    /profile/{id}     → ADMIN, SUPERADMIN only
  DELETE /profile/{id}     → SUPERADMIN only
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_min_role, require_role
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user_schemas import UserProfileUpdate, UserRead

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=UserRead, summary="Get own profile")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    """All authenticated roles can read their own profile."""
    return UserRead.model_validate(current_user)


@router.patch("/me", response_model=UserRead, summary="Update own profile")
async def update_my_profile(
    body: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """All authenticated roles can update their own full_name."""
    if body.full_name is not None:
        current_user.full_name = body.full_name
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return UserRead.model_validate(current_user)


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Get any user profile (admin+)",
)
async def get_profile_by_id(
    user_id: str,
    _caller: User = Depends(require_min_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """ADMIN and SUPERADMIN can look up any user profile."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserRead.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete any user profile (superadmin only)",
)
async def delete_profile(
    user_id: str,
    _caller: User = Depends(require_role(UserRole.SUPERADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Only SUPERADMIN can delete a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await db.delete(user)
    await db.commit()

```

### `backend/app/routers/taxonomy_router.py`
```python
"""Taxonomy router – /api/v1/taxonomy endpoints.

Authorization matrix:
  GET    /taxonomy/vocabularies          → all authenticated roles
  POST   /taxonomy/vocabularies          → EDITOR, ADMIN, SUPERADMIN
  PATCH  /taxonomy/vocabularies/{id}     → EDITOR, ADMIN, SUPERADMIN
  DELETE /taxonomy/vocabularies/{id}     → ADMIN, SUPERADMIN

  GET    /taxonomy/vocabularies/{id}/terms       → all authenticated roles
  POST   /taxonomy/vocabularies/{id}/terms       → CONTRIBUTOR, EDITOR, ADMIN, SUPERADMIN
  PATCH  /taxonomy/vocabularies/{id}/terms/{tid} → EDITOR, ADMIN, SUPERADMIN
  DELETE /taxonomy/vocabularies/{id}/terms/{tid} → ADMIN, SUPERADMIN
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_min_role, require_role
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.taxonomy import TaxonomyTerm, TaxonomyVocabulary
from app.models.user import User
from app.schemas.taxonomy_schemas import (
    TermCreate,
    TermRead,
    TermUpdate,
    VocabularyCreate,
    VocabularyRead,
    VocabularyUpdate,
)

router = APIRouter(prefix="/taxonomy", tags=["taxonomy"])

# ──────────────────────────────────────────────────────────────────────────────
# Vocabulary endpoints
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/vocabularies", response_model=list[VocabularyRead], summary="List vocabularies")
async def list_vocabularies(
    _caller: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[VocabularyRead]:
    result = await db.execute(select(TaxonomyVocabulary))
    return [VocabularyRead.model_validate(v) for v in result.scalars().all()]


@router.post(
    "/vocabularies",
    response_model=VocabularyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create vocabulary (editor+)",
)
async def create_vocabulary(
    body: VocabularyCreate,
    _caller: User = Depends(require_min_role(UserRole.EDITOR)),
    db: AsyncSession = Depends(get_db),
) -> VocabularyRead:
    result = await db.execute(
        select(TaxonomyVocabulary).where(TaxonomyVocabulary.slug == body.slug)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")
    vocab = TaxonomyVocabulary(slug=body.slug, name=body.name, description=body.description)
    db.add(vocab)
    await db.commit()
    await db.refresh(vocab)
    return VocabularyRead.model_validate(vocab)


@router.patch(
    "/vocabularies/{vocab_id}",
    response_model=VocabularyRead,
    summary="Update vocabulary (editor+)",
)
async def update_vocabulary(
    vocab_id: str,
    body: VocabularyUpdate,
    _caller: User = Depends(require_min_role(UserRole.EDITOR)),
    db: AsyncSession = Depends(get_db),
) -> VocabularyRead:
    result = await db.execute(
        select(TaxonomyVocabulary).where(TaxonomyVocabulary.id == vocab_id)
    )
    vocab = result.scalar_one_or_none()
    if vocab is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vocabulary not found")
    if body.name is not None:
        vocab.name = body.name
    if body.description is not None:
        vocab.description = body.description
    db.add(vocab)
    await db.commit()
    await db.refresh(vocab)
    return VocabularyRead.model_validate(vocab)


@router.delete(
    "/vocabularies/{vocab_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete vocabulary (admin+)",
)
async def delete_vocabulary(
    vocab_id: str,
    _caller: User = Depends(require_min_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(TaxonomyVocabulary).where(TaxonomyVocabulary.id == vocab_id)
    )
    vocab = result.scalar_one_or_none()
    if vocab is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vocabulary not found")
    await db.delete(vocab)
    await db.commit()


# ──────────────────────────────────────────────────────────────────────────────
# Term endpoints
# ──────────────────────────────────────────────────────────────────────────────


@router.get(
    "/vocabularies/{vocab_id}/terms",
    response_model=list[TermRead],
    summary="List terms",
)
async def list_terms(
    vocab_id: str,
    _caller: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TermRead]:
    result = await db.execute(
        select(TaxonomyTerm).where(TaxonomyTerm.vocabulary_id == vocab_id)
    )
    return [TermRead.model_validate(t) for t in result.scalars().all()]


@router.post(
    "/vocabularies/{vocab_id}/terms",
    response_model=TermRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create term (contributor+)",
)
async def create_term(
    vocab_id: str,
    body: TermCreate,
    caller: User = Depends(require_min_role(UserRole.CONTRIBUTOR)),
    db: AsyncSession = Depends(get_db),
) -> TermRead:
    result = await db.execute(
        select(TaxonomyVocabulary).where(TaxonomyVocabulary.id == vocab_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vocabulary not found")
    term = TaxonomyTerm(
        vocabulary_id=vocab_id,
        slug=body.slug,
        name=body.name,
        description=body.description,
        created_by=caller.id,
    )
    db.add(term)
    await db.commit()
    await db.refresh(term)
    return TermRead.model_validate(term)


@router.patch(
    "/vocabularies/{vocab_id}/terms/{term_id}",
    response_model=TermRead,
    summary="Update term (editor+)",
)
async def update_term(
    vocab_id: str,
    term_id: str,
    body: TermUpdate,
    _caller: User = Depends(require_min_role(UserRole.EDITOR)),
    db: AsyncSession = Depends(get_db),
) -> TermRead:
    result = await db.execute(
        select(TaxonomyTerm).where(
            TaxonomyTerm.id == term_id, TaxonomyTerm.vocabulary_id == vocab_id
        )
    )
    term = result.scalar_one_or_none()
    if term is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Term not found")
    if body.name is not None:
        term.name = body.name
    if body.description is not None:
        term.description = body.description
    db.add(term)
    await db.commit()
    await db.refresh(term)
    return TermRead.model_validate(term)


@router.delete(
    "/vocabularies/{vocab_id}/terms/{term_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete term (admin+)",
)
async def delete_term(
    vocab_id: str,
    term_id: str,
    _caller: User = Depends(require_min_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(TaxonomyTerm).where(
            TaxonomyTerm.id == term_id, TaxonomyTerm.vocabulary_id == vocab_id
        )
    )
    term = result.scalar_one_or_none()
    if term is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Term not found")
    await db.delete(term)
    await db.commit()

```

### `backend/app/schemas/__init__.py`
```python
from app.schemas.user_schemas import (
    TokenResponse,
    UserCreate,
    UserProfileUpdate,
    UserRead,
    UserUpdate,
)
from app.schemas.taxonomy_schemas import (
    TermCreate,
    TermRead,
    TermUpdate,
    VocabularyCreate,
    VocabularyRead,
    VocabularyUpdate,
)

__all__ = [
    "UserCreate",
    "UserUpdate",
    "UserRead",
    "UserProfileUpdate",
    "TokenResponse",
    "VocabularyCreate",
    "VocabularyUpdate",
    "VocabularyRead",
    "TermCreate",
    "TermUpdate",
    "TermRead",
]

```

### `backend/app/schemas/taxonomy_schemas.py`
```python
"""Taxonomy Pydantic schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class VocabularyCreate(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9-]+$", max_length=100)
    name: str = Field(max_length=255)
    description: str | None = None


class VocabularyUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None


class VocabularyRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    slug: str
    name: str
    description: str | None = None


class TermCreate(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9-]+$", max_length=100)
    name: str = Field(max_length=255)
    description: str | None = None


class TermUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None


class TermRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    vocabulary_id: str
    slug: str
    name: str
    description: str | None = None
    created_by: str | None = None

```

### `backend/app/schemas/user_schemas.py`
```python
"""User Pydantic schemas (request/response DTOs)."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    role: UserRole = UserRole.VIEWER


class UserCreate(UserBase):
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserRead(UserBase):
    model_config = {"from_attributes": True}

    id: str
    is_active: bool
    is_verified: bool


class UserProfileUpdate(BaseModel):
    """Fields a user can update on their own profile."""

    full_name: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

```

### `backend/pyproject.toml`
```toml
[build-system]
requires = ["setuptools>=68"]
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
    "python-jose[cryptography]>=3.3.0",
    "passlib>=1.7.4",
    "python-multipart>=0.0.19",
    "httpx>=0.28.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.4",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.8.4",
    "mypy>=1.13.0",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["app*"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["."]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "N", "S", "B", "A"]
ignore = ["S101", "S105", "S106", "B008", "A003"]

[tool.mypy]
python_version = "3.12"
strict = false
ignore_missing_imports = true

```

### `backend/tests/__init__.py`
```python
# tests package

```

### `backend/tests/profile_admin/__init__.py`
```python
# tests/profile_admin package

```

### `backend/tests/profile_admin/conftest.py`
```python
"""Shared pytest fixtures for profile/admin/taxonomy auth tests."""
from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.passwords import hash_password
from app.core.database import Base, get_db
from app.main import create_app
from app.models.enums import UserRole
from app.models.user import User
# Import taxonomy models so Base.metadata knows about them
from app.models.taxonomy import TaxonomyVocabulary, TaxonomyTerm  # noqa: F401

# ──────────────────────────────────────────────────────────────────────────────
# In-memory SQLite engine (isolated per test session)
# ──────────────────────────────────────────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture(scope="session")
def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture()
async def db_session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI test client with DB override
# ──────────────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture()
async def client(session_factory) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ──────────────────────────────────────────────────────────────────────────────
# User factory helpers
# ──────────────────────────────────────────────────────────────────────────────

PASSWORD = "Test1234!"


async def _create_user(db: AsyncSession, role: UserRole, suffix: str = "") -> User:
    uid = str(uuid.uuid4())
    tag = suffix or uid[:8]
    user = User(
        id=uid,
        email=f"{role.value}-{tag}@test.example",
        hashed_password=hash_password(PASSWORD),
        full_name=f"{role.value.title()} User",
        role=role,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _get_token(client: AsyncClient, email: str, password: str = PASSWORD) -> str:
    resp = await client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": password},
    )
    assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
    return resp.json()["access_token"]


@pytest_asyncio.fixture()
async def users(db_session: AsyncSession) -> dict[str, User]:
    """Create one user per role, keyed by role value."""
    return {
        role.value: await _create_user(db_session, role)
        for role in UserRole
    }


@pytest_asyncio.fixture()
async def tokens(client: AsyncClient, users: dict[str, User]) -> dict[str, str]:
    """Return JWT tokens keyed by role value."""
    result: dict[str, str] = {}
    for role_val, user in users.items():
        result[role_val] = await _get_token(client, user.email)
    return result


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

```

### `backend/tests/profile_admin/test_auth_matrix.py`
```python
"""
TASK-031 – Authorization negative-test matrix across all 5 roles.

Covers: profile / admin / taxonomy endpoints.

Matrix legend
─────────────
Role rank:   viewer(0) < contributor(1) < editor(2) < admin(3) < superadmin(4)

Profile endpoints
─────────────────
  GET  /api/v1/profile/me        → 200 for ALL roles (positive baseline)
  PATCH /api/v1/profile/me       → 200 for ALL roles (self-service baseline)
  GET  /api/v1/profile/{id}      → 403 for viewer, contributor, editor  | 200 for admin, superadmin
  DELETE /api/v1/profile/{id}    → 403 for viewer, contributor, editor, admin | 204 for superadmin

Admin endpoints
───────────────
  GET  /api/v1/admin/users       → 403 for viewer, contributor, editor | 200 for admin, superadmin
  POST /api/v1/admin/users       → 403 for viewer, contributor, editor, admin | 201 for superadmin
  PATCH /api/v1/admin/users/{id} → 403 for viewer, contributor, editor | 200 for admin, superadmin
  DELETE /api/v1/admin/users/{id}→ 403 for viewer, contributor, editor, admin | 204 for superadmin

Taxonomy – vocabulary endpoints
──────────────────────────────
  GET  /api/v1/taxonomy/vocabularies     → 200 for ALL roles (positive baseline)
  POST /api/v1/taxonomy/vocabularies     → 403 for viewer, contributor | 201 for editor, admin, superadmin
  PATCH /api/v1/taxonomy/vocabularies/{id} → 403 for viewer, contributor | 200 for editor, admin, superadmin
  DELETE /api/v1/taxonomy/vocabularies/{id}→ 403 for viewer, contributor, editor | 204 for admin, superadmin

Taxonomy – term endpoints
─────────────────────────
  GET  /api/v1/taxonomy/vocabularies/{id}/terms   → 200 for ALL roles
  POST /api/v1/taxonomy/vocabularies/{id}/terms   → 403 for viewer | 201 for contributor, editor, admin, superadmin
  PATCH /api/v1/taxonomy/vocabularies/{id}/terms/{tid} → 403 for viewer, contributor | 200 for editor+
  DELETE /api/v1/taxonomy/vocabularies/{id}/terms/{tid}→ 403 for viewer, contributor, editor | 204 for admin+

Unauthenticated
───────────────
  Every protected endpoint → 403 (no bearer) for anon
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.taxonomy import TaxonomyTerm, TaxonomyVocabulary
from app.models.user import User
from tests.profile_admin.conftest import _create_user, auth_headers
from app.models.enums import UserRole

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

ALL_ROLES = [r.value for r in UserRole]
VIEWER = UserRole.VIEWER.value
CONTRIBUTOR = UserRole.CONTRIBUTOR.value
EDITOR = UserRole.EDITOR.value
ADMIN = UserRole.ADMIN.value
SUPERADMIN = UserRole.SUPERADMIN.value


# ──────────────────────────────────────────────────────────────────────────────
# Additional fixtures: vocabulary + term seeds
# ──────────────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture()
async def vocab(db_session: AsyncSession) -> TaxonomyVocabulary:
    v = TaxonomyVocabulary(
        id=str(uuid.uuid4()), slug="test-vocab", name="Test Vocab"
    )
    db_session.add(v)
    await db_session.commit()
    await db_session.refresh(v)
    return v


@pytest_asyncio.fixture()
async def term(db_session: AsyncSession, vocab: TaxonomyVocabulary) -> TaxonomyTerm:
    t = TaxonomyTerm(
        id=str(uuid.uuid4()),
        vocabulary_id=vocab.id,
        slug="test-term",
        name="Test Term",
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


# ──────────────────────────────────────────────────────────────────────────────
# Section 1: Unauthenticated → 403 everywhere
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestUnauthenticated:
    async def test_profile_me_anon(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/profile/me")
        assert resp.status_code == 403, resp.text

    async def test_profile_by_id_anon(self, client: AsyncClient, users: dict[str, User]) -> None:
        resp = await client.get(f"/api/v1/profile/{users[VIEWER].id}")
        assert resp.status_code == 403, resp.text

    async def test_profile_delete_anon(self, client: AsyncClient, users: dict[str, User]) -> None:
        resp = await client.delete(f"/api/v1/profile/{users[VIEWER].id}")
        assert resp.status_code == 403, resp.text

    async def test_admin_list_users_anon(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/admin/users")
        assert resp.status_code == 403, resp.text

    async def test_admin_create_user_anon(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/admin/users", json={
            "email": "anon@test.example",
            "password": "Test1234!",
            "role": "viewer",
        })
        assert resp.status_code == 403, resp.text

    async def test_taxonomy_vocabs_anon(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/taxonomy/vocabularies")
        assert resp.status_code == 403, resp.text

    async def test_taxonomy_create_vocab_anon(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/taxonomy/vocabularies", json={
            "slug": "anon-vocab", "name": "Anon"
        })
        assert resp.status_code == 403, resp.text

    async def test_taxonomy_terms_anon(
        self, client: AsyncClient, vocab: TaxonomyVocabulary
    ) -> None:
        resp = await client.get(f"/api/v1/taxonomy/vocabularies/{vocab.id}/terms")
        assert resp.status_code == 403, resp.text


# ──────────────────────────────────────────────────────────────────────────────
# Section 2: Profile /me – positive baseline (all roles get 200)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestProfileMeAllRoles:
    @pytest.mark.parametrize("role", ALL_ROLES)
    async def test_get_my_profile(
        self, client: AsyncClient, tokens: dict[str, str], role: str
    ) -> None:
        resp = await client.get("/api/v1/profile/me", headers=auth_headers(tokens[role]))
        assert resp.status_code == 200, f"role={role}: {resp.text}"
        assert resp.json()["role"] == role

    @pytest.mark.parametrize("role", ALL_ROLES)
    async def test_patch_my_profile(
        self, client: AsyncClient, tokens: dict[str, str], role: str
    ) -> None:
        resp = await client.patch(
            "/api/v1/profile/me",
            headers=auth_headers(tokens[role]),
            json={"full_name": f"{role} Updated"},
        )
        assert resp.status_code == 200, f"role={role}: {resp.text}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 3: Profile GET /{id} – admin+ allowed; viewer/contributor/editor → 403
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestProfileGetById:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR, EDITOR])
    async def test_forbidden_for_low_roles(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        users: dict[str, User],
        role: str,
    ) -> None:
        target_id = users[VIEWER].id
        resp = await client.get(
            f"/api/v1/profile/{target_id}", headers=auth_headers(tokens[role])
        )
        assert resp.status_code == 403, f"Expected 403 for role={role}, got {resp.status_code}"

    @pytest.mark.parametrize("role", [ADMIN, SUPERADMIN])
    async def test_allowed_for_admin_plus(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        users: dict[str, User],
        role: str,
    ) -> None:
        target_id = users[VIEWER].id
        resp = await client.get(
            f"/api/v1/profile/{target_id}", headers=auth_headers(tokens[role])
        )
        assert resp.status_code == 200, f"Expected 200 for role={role}, got {resp.status_code}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 4: Profile DELETE /{id} – superadmin only; all others → 403
# ──────────────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture()
async def deletable_user(db_session: AsyncSession) -> User:
    return await _create_user(db_session, UserRole.VIEWER, suffix="deletable")


@pytest.mark.asyncio
class TestProfileDelete:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR, EDITOR, ADMIN])
    async def test_forbidden_for_non_superadmin(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        deletable_user: User,
        role: str,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/profile/{deletable_user.id}", headers=auth_headers(tokens[role])
        )
        assert resp.status_code == 403, f"Expected 403 for role={role}, got {resp.status_code}"

    async def test_superadmin_can_delete(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        deletable_user: User,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/profile/{deletable_user.id}",
            headers=auth_headers(tokens[SUPERADMIN]),
        )
        assert resp.status_code == 204, f"Expected 204, got {resp.status_code}: {resp.text}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 5: Admin GET /users – admin+ allowed; low roles → 403
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestAdminListUsers:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR, EDITOR])
    async def test_forbidden(
        self, client: AsyncClient, tokens: dict[str, str], role: str
    ) -> None:
        resp = await client.get("/api/v1/admin/users", headers=auth_headers(tokens[role]))
        assert resp.status_code == 403, f"role={role}: {resp.status_code}"

    @pytest.mark.parametrize("role", [ADMIN, SUPERADMIN])
    async def test_allowed(
        self, client: AsyncClient, tokens: dict[str, str], role: str
    ) -> None:
        resp = await client.get("/api/v1/admin/users", headers=auth_headers(tokens[role]))
        assert resp.status_code == 200, f"role={role}: {resp.status_code}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 6: Admin POST /users – superadmin only
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestAdminCreateUser:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR, EDITOR, ADMIN])
    async def test_forbidden_for_non_superadmin(
        self, client: AsyncClient, tokens: dict[str, str], role: str
    ) -> None:
        resp = await client.post(
            "/api/v1/admin/users",
            headers=auth_headers(tokens[role]),
            json={"email": f"new-{role}@x.example", "password": "Test1234!", "role": "viewer"},
        )
        assert resp.status_code == 403, f"role={role}: {resp.status_code}"

    async def test_superadmin_can_create(
        self, client: AsyncClient, tokens: dict[str, str]
    ) -> None:
        resp = await client.post(
            "/api/v1/admin/users",
            headers=auth_headers(tokens[SUPERADMIN]),
            json={
                "email": f"created-{uuid.uuid4().hex[:6]}@x.example",
                "password": "Test1234!",
                "role": "viewer",
            },
        )
        assert resp.status_code == 201, resp.text


# ──────────────────────────────────────────────────────────────────────────────
# Section 7: Admin PATCH /users/{id} – admin+ allowed; low roles → 403
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestAdminUpdateUser:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR, EDITOR])
    async def test_forbidden(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        users: dict[str, User],
        role: str,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/admin/users/{users[VIEWER].id}",
            headers=auth_headers(tokens[role]),
            json={"full_name": "hacked"},
        )
        assert resp.status_code == 403, f"role={role}: {resp.status_code}"

    @pytest.mark.parametrize("role", [ADMIN, SUPERADMIN])
    async def test_allowed(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        users: dict[str, User],
        role: str,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/admin/users/{users[VIEWER].id}",
            headers=auth_headers(tokens[role]),
            json={"full_name": f"Updated by {role}"},
        )
        assert resp.status_code == 200, f"role={role}: {resp.status_code}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 8: Admin DELETE /users/{id} – superadmin only
# ──────────────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture()
async def admin_deletable_user(db_session: AsyncSession) -> User:
    return await _create_user(db_session, UserRole.VIEWER, suffix="admin-del")


@pytest.mark.asyncio
class TestAdminDeleteUser:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR, EDITOR, ADMIN])
    async def test_forbidden_for_non_superadmin(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        admin_deletable_user: User,
        role: str,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/admin/users/{admin_deletable_user.id}",
            headers=auth_headers(tokens[role]),
        )
        assert resp.status_code == 403, f"role={role}: {resp.status_code}"

    async def test_superadmin_can_delete(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        admin_deletable_user: User,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/admin/users/{admin_deletable_user.id}",
            headers=auth_headers(tokens[SUPERADMIN]),
        )
        assert resp.status_code == 204, resp.text


# ──────────────────────────────────────────────────────────────────────────────
# Section 9: Taxonomy GET /vocabularies – all roles 200
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestTaxonomyListVocabularies:
    @pytest.mark.parametrize("role", ALL_ROLES)
    async def test_all_roles_can_list(
        self, client: AsyncClient, tokens: dict[str, str], role: str
    ) -> None:
        resp = await client.get(
            "/api/v1/taxonomy/vocabularies", headers=auth_headers(tokens[role])
        )
        assert resp.status_code == 200, f"role={role}: {resp.status_code}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 10: Taxonomy POST /vocabularies – editor+ allowed; viewer/contributor → 403
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestTaxonomyCreateVocabulary:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR])
    async def test_forbidden(
        self, client: AsyncClient, tokens: dict[str, str], role: str
    ) -> None:
        resp = await client.post(
            "/api/v1/taxonomy/vocabularies",
            headers=auth_headers(tokens[role]),
            json={"slug": f"slug-{role}", "name": "Vocab"},
        )
        assert resp.status_code == 403, f"role={role}: {resp.status_code}"

    @pytest.mark.parametrize("role", [EDITOR, ADMIN, SUPERADMIN])
    async def test_allowed(
        self, client: AsyncClient, tokens: dict[str, str], role: str
    ) -> None:
        slug = f"vocab-{role}-{uuid.uuid4().hex[:6]}"
        resp = await client.post(
            "/api/v1/taxonomy/vocabularies",
            headers=auth_headers(tokens[role]),
            json={"slug": slug, "name": f"Vocab {role}"},
        )
        assert resp.status_code == 201, f"role={role}: {resp.text}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 11: Taxonomy PATCH /vocabularies/{id} – editor+ allowed; viewer/contributor → 403
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestTaxonomyUpdateVocabulary:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR])
    async def test_forbidden(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        vocab: TaxonomyVocabulary,
        role: str,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/taxonomy/vocabularies/{vocab.id}",
            headers=auth_headers(tokens[role]),
            json={"name": "Hacked"},
        )
        assert resp.status_code == 403, f"role={role}: {resp.status_code}"

    @pytest.mark.parametrize("role", [EDITOR, ADMIN, SUPERADMIN])
    async def test_allowed(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        vocab: TaxonomyVocabulary,
        role: str,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/taxonomy/vocabularies/{vocab.id}",
            headers=auth_headers(tokens[role]),
            json={"name": f"Updated by {role}"},
        )
        assert resp.status_code == 200, f"role={role}: {resp.text}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 12: Taxonomy DELETE /vocabularies/{id} – admin+ allowed; viewer/contributor/editor → 403
# ──────────────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture()
async def deletable_vocab(db_session: AsyncSession) -> TaxonomyVocabulary:
    v = TaxonomyVocabulary(
        id=str(uuid.uuid4()), slug=f"del-vocab-{uuid.uuid4().hex[:6]}", name="Deletable"
    )
    db_session.add(v)
    await db_session.commit()
    await db_session.refresh(v)
    return v


@pytest_asyncio.fixture()
async def deletable_vocab_for_admin(db_session: AsyncSession) -> TaxonomyVocabulary:
    v = TaxonomyVocabulary(
        id=str(uuid.uuid4()), slug=f"del-admin-{uuid.uuid4().hex[:6]}", name="Deletable Admin"
    )
    db_session.add(v)
    await db_session.commit()
    await db_session.refresh(v)
    return v


@pytest.mark.asyncio
class TestTaxonomyDeleteVocabulary:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR, EDITOR])
    async def test_forbidden(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        deletable_vocab: TaxonomyVocabulary,
        role: str,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/taxonomy/vocabularies/{deletable_vocab.id}",
            headers=auth_headers(tokens[role]),
        )
        assert resp.status_code == 403, f"role={role}: {resp.status_code}"

    async def test_admin_can_delete(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        deletable_vocab_for_admin: TaxonomyVocabulary,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/taxonomy/vocabularies/{deletable_vocab_for_admin.id}",
            headers=auth_headers(tokens[ADMIN]),
        )
        assert resp.status_code == 204, resp.text

    async def test_superadmin_can_delete(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        db_session: AsyncSession,
    ) -> None:
        v = TaxonomyVocabulary(
            id=str(uuid.uuid4()), slug=f"sa-del-{uuid.uuid4().hex[:6]}", name="SA Del"
        )
        db_session.add(v)
        await db_session.commit()
        resp = await client.delete(
            f"/api/v1/taxonomy/vocabularies/{v.id}",
            headers=auth_headers(tokens[SUPERADMIN]),
        )
        assert resp.status_code == 204, resp.text


# ──────────────────────────────────────────────────────────────────────────────
# Section 13: Term GET – all roles 200
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestTermListAllRoles:
    @pytest.mark.parametrize("role", ALL_ROLES)
    async def test_all_roles_can_list_terms(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        vocab: TaxonomyVocabulary,
        role: str,
    ) -> None:
        resp = await client.get(
            f"/api/v1/taxonomy/vocabularies/{vocab.id}/terms",
            headers=auth_headers(tokens[role]),
        )
        assert resp.status_code == 200, f"role={role}: {resp.status_code}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 14: Term POST – viewer → 403; contributor+ → 201
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestTermCreate:
    async def test_viewer_forbidden(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        vocab: TaxonomyVocabulary,
    ) -> None:
        resp = await client.post(
            f"/api/v1/taxonomy/vocabularies/{vocab.id}/terms",
            headers=auth_headers(tokens[VIEWER]),
            json={"slug": "blocked-term", "name": "Blocked"},
        )
        assert resp.status_code == 403, resp.text

    @pytest.mark.parametrize("role", [CONTRIBUTOR, EDITOR, ADMIN, SUPERADMIN])
    async def test_contributor_plus_allowed(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        vocab: TaxonomyVocabulary,
        role: str,
    ) -> None:
        slug = f"term-{role}-{uuid.uuid4().hex[:6]}"
        resp = await client.post(
            f"/api/v1/taxonomy/vocabularies/{vocab.id}/terms",
            headers=auth_headers(tokens[role]),
            json={"slug": slug, "name": f"Term {role}"},
        )
        assert resp.status_code == 201, f"role={role}: {resp.text}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 15: Term PATCH – editor+ allowed; viewer/contributor → 403
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestTermUpdate:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR])
    async def test_forbidden(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        vocab: TaxonomyVocabulary,
        term: TaxonomyTerm,
        role: str,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/taxonomy/vocabularies/{vocab.id}/terms/{term.id}",
            headers=auth_headers(tokens[role]),
            json={"name": "Hacked"},
        )
        assert resp.status_code == 403, f"role={role}: {resp.status_code}"

    @pytest.mark.parametrize("role", [EDITOR, ADMIN, SUPERADMIN])
    async def test_allowed(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        vocab: TaxonomyVocabulary,
        term: TaxonomyTerm,
        role: str,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/taxonomy/vocabularies/{vocab.id}/terms/{term.id}",
            headers=auth_headers(tokens[role]),
            json={"name": f"Updated by {role}"},
        )
        assert resp.status_code == 200, f"role={role}: {resp.text}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 16: Term DELETE – admin+ allowed; viewer/contributor/editor → 403
# ──────────────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture()
async def deletable_term(
    db_session: AsyncSession, vocab: TaxonomyVocabulary
) -> TaxonomyTerm:
    t = TaxonomyTerm(
        id=str(uuid.uuid4()),
        vocabulary_id=vocab.id,
        slug=f"del-term-{uuid.uuid4().hex[:6]}",
        name="Deletable Term",
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture()
async def deletable_term_for_admin(
    db_session: AsyncSession, vocab: TaxonomyVocabulary
) -> TaxonomyTerm:
    t = TaxonomyTerm(
        id=str(uuid.uuid4()),
        vocabulary_id=vocab.id,
        slug=f"del-term-admin-{uuid.uuid4().hex[:6]}",
        name="Deletable Term Admin",
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


@pytest.mark.asyncio
class TestTermDelete:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR, EDITOR])
    async def test_forbidden(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        vocab: TaxonomyVocabulary,
        deletable_term: TaxonomyTerm,
        role: str,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/taxonomy/vocabularies/{vocab.id}/terms/{deletable_term.id}",
            headers=auth_headers(tokens[role]),
        )
        assert resp.status_code == 403, f"role={role}: {resp.status_code}"

    async def test_admin_can_delete(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        vocab: TaxonomyVocabulary,
        deletable_term_for_admin: TaxonomyTerm,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/taxonomy/vocabularies/{vocab.id}/terms/{deletable_term_for_admin.id}",
            headers=auth_headers(tokens[ADMIN]),
        )
        assert resp.status_code == 204, resp.text

    async def test_superadmin_can_delete(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        vocab: TaxonomyVocabulary,
        db_session: AsyncSession,
    ) -> None:
        t = TaxonomyTerm(
            id=str(uuid.uuid4()),
            vocabulary_id=vocab.id,
            slug=f"sa-del-term-{uuid.uuid4().hex[:6]}",
            name="SA Del Term",
        )
        db_session.add(t)
        await db_session.commit()
        resp = await client.delete(
            f"/api/v1/taxonomy/vocabularies/{vocab.id}/terms/{t.id}",
            headers=auth_headers(tokens[SUPERADMIN]),
        )
        assert resp.status_code == 204, resp.text

```