# Implementation Report

### JRN-003 — Discussion Journey

## Verification
- `python3 -c "
import os, json
result = []
for root, dirs, files in os.walk('backend'):
    dirs[:] = [d for d in dirs if d not in ('__pycache__','.venv','venv','.git','node_modules')]
    for f in files:
        if f.endswith('.py') or f in ('pyproject.toml','requirements.txt','requirements-dev.txt','alembic.ini','.env.example'):
            result.append(os.path.join(root,f))
result.sort()
print('\n'.join(result))
"` → exit 0
- `python3 -c "
import os
result = []
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('__pycache__','.venv','venv','.git','node_modules','.mypy_cache','.pytest_cache')]
    for f in files:
        result.append(os.path.join(root,f))
result.sort()
print('\n'.join(result[:200]))
"` → exit 0
- `python3 -c "import os; print(os.getcwd()); print(os.listdir('.'))"` → exit 0
- `python3 -c "import sys; print(sys.version)"` → exit 0
- `pip show fastapi pydantic sqlalchemy pytest httpx pytest-asyncio` → exit 0
- `pip show alembic passlib python-jose python-multipart email-validator` → exit 0
- `pip show pydantic-settings bcrypt aiosqlite pytest-cov` → exit 0
- `pip show anyio asgi-lifespan` → exit 0
- `pip show backend` → exit 0
- `python3 -c "import backend; print(backend.__file__)"` → exit 1
- `python3 -c "import os; base='/tmp/archpilot_verify_o15owznv/backend'; print(os.listdir(base))"` → exit 1
- `python3 -c "
import subprocess, sys
result = subprocess.run([sys.executable, '-m', 'pip', 'show', '-f', 'backend'], capture_output=True, text=True)
print(result.stdout[:3000])
"` → exit 0
- `python3 -c "
import os
base = '/tmp/archpilot_verify_o15owznv'
result = []
for root, dirs, files in os.walk(base):
    dirs[:] = [d for d in dirs if d not in ('__pycache__','.venv','venv','.git','node_modules','.mypy_cache','.pytest_cache','site-packages')]
    for f in files:
        result.append(os.path.join(root,f).replace(base+'/', ''))
result.sort()
print('\n'.join(result))
"` → exit 0
- `python3 -c "import os; print(os.getcwd())"` → exit 0

## Generated Files

### `backend/.env.example`
```text
SECRET_KEY=changeme-dev-only-32-chars-minimum!!
DATABASE_URL=sqlite+aiosqlite:///./dev.db
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=["http://localhost:3000"]

```

### `backend/app/__init__.py`
```python
# backend/app/__init__.py

```

### `backend/app/core/__init__.py`
```python
from app.core.config import settings as settings
from app.core.database import Base as Base
from app.core.database import AsyncSessionLocal as AsyncSessionLocal
from app.core.database import engine as engine
from app.core.database import get_db as get_db
from app.core.database import create_all_tables as create_all_tables
from app.core.database import drop_all_tables as drop_all_tables
from app.core.security import hash_password as hash_password
from app.core.security import verify_password as verify_password
from app.core.security import create_access_token as create_access_token
from app.core.security import create_refresh_token as create_refresh_token
from app.core.deps import get_current_user as get_current_user
from app.core.deps import get_current_active_user as get_current_active_user
from app.core.deps import require_admin as require_admin

```

### `backend/app/core/config.py`
```python
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"

    # JWT
    SECRET_KEY: str = "changeme-dev-only-32-chars-minimum!!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # App
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100


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
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    # SQLite-specific: allow cross-thread usage in tests
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
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


async def create_all_tables() -> None:
    """Create all tables — used in tests and dev startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

```

### `backend/app/core/deps.py`
```python
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> "User":  # noqa: F821
    from app.models.user import User  # lazy import to avoid circular

    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        sub: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        if sub is None or token_type != "access":
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == int(sub)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exc
    return user


async def get_current_active_user(
    current_user: "User" = Depends(get_current_user),  # noqa: F821
) -> "User":  # noqa: F821
    return current_user


async def require_admin(
    current_user: "User" = Depends(get_current_user),  # noqa: F821
) -> "User":  # noqa: F821
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user

```

### `backend/app/core/error_handlers.py`
```python
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

```

### `backend/app/core/exceptions.py`
```python
from __future__ import annotations


class AppError(Exception):
    def __init__(self, detail: str, status_code: int = 400) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class NotFoundError(AppError):
    def __init__(self, detail: str = "Not found") -> None:
        super().__init__(detail, 404)


class ConflictError(AppError):
    def __init__(self, detail: str = "Conflict") -> None:
        super().__init__(detail, 409)


class ForbiddenError(AppError):
    def __init__(self, detail: str = "Forbidden") -> None:
        super().__init__(detail, 403)


class UnprocessableError(AppError):
    def __init__(self, detail: str = "Unprocessable") -> None:
        super().__init__(detail, 422)

```

### `backend/app/core/security.py`
```python
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": subject, "exp": expire, "type": "access"}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": subject, "exp": expire, "type": "refresh"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def decode_token_safe(token: str) -> dict[str, Any] | None:
    try:
        return decode_token(token)
    except JWTError:
        return None

```

### `backend/app/main.py`
```python
from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import create_all_tables
from app.core.exceptions import AppError
from app.routers.auth import router as auth_router, users_router
from app.routers.discussions import router as discussions_router, posts_router
from app.routers.kb import router as kb_router
from app.routers.search import router as search_router
from app.routers.notifications import router as notifications_router
from app.routers.admin import router as admin_router

# Ensure models are imported so metadata is populated
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    await create_all_tables()
    yield


app = FastAPI(
    title="Community Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global error handler
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ── Routers ────────────────────────────────────────────────────────────────
PREFIX = "/api/v1"

app.include_router(auth_router, prefix=PREFIX)
app.include_router(users_router, prefix=PREFIX)
app.include_router(discussions_router, prefix=PREFIX)
app.include_router(posts_router, prefix=PREFIX)
app.include_router(kb_router, prefix=PREFIX)
app.include_router(search_router, prefix=PREFIX)
app.include_router(notifications_router, prefix=PREFIX)
app.include_router(admin_router, prefix=PREFIX)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict:
    return {"status": "ready"}

```

### `backend/app/models/__init__.py`
```python
# Import all models so SQLAlchemy metadata is populated
from app.models.user import User as User, UserRole as UserRole
from app.models.discussion import Discussion as Discussion, DiscussionStatus as DiscussionStatus
from app.models.post import Post as Post
from app.models.kb_article import KBArticle as KBArticle, ArticleStatus as ArticleStatus
from app.models.notification import Notification as Notification, NotificationKind as NotificationKind
from app.models.audit_log import AuditLog as AuditLog

```

### `backend/app/models/audit_log.py`
```python
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AuditLog(Base):
    """Append-only admin audit trail — no update/delete on this table."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    actor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    actor: Mapped["User | None"] = relationship(  # noqa: F821
        "User", back_populates="audit_logs"
    )

```

### `backend/app/models/discussion.py`
```python
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DiscussionStatus(str, enum.Enum):
    open = "open"
    closed = "closed"
    locked = "locked"
    archived = "archived"


class Discussion(Base):
    __tablename__ = "discussions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        Enum(DiscussionStatus, values_callable=lambda x: [e.value for e in x]),
        default=DiscussionStatus.open.value,
        nullable=False,
    )
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tags: Mapped[str | None] = mapped_column(String(500), nullable=True)  # comma-separated
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    author: Mapped["User"] = relationship("User", back_populates="discussions")  # noqa: F821
    posts: Mapped[list["Post"]] = relationship(  # noqa: F821
        "Post", back_populates="discussion", cascade="all, delete-orphan", lazy="select"
    )

```

### `backend/app/models/kb_article.py`
```python
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ArticleStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class KBArticle(Base):
    __tablename__ = "kb_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(350), unique=True, nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        Enum(ArticleStatus, values_callable=lambda x: [e.value for e in x]),
        default=ArticleStatus.draft.value,
        nullable=False,
    )
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    tags: Mapped[str | None] = mapped_column(String(500), nullable=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    author: Mapped["User"] = relationship("User", back_populates="kb_articles")  # noqa: F821

```

### `backend/app/models/notification.py`
```python
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class NotificationKind(str, enum.Enum):
    post_reply = "post_reply"
    discussion_reply = "discussion_reply"
    mention = "mention"
    kb_comment = "kb_comment"
    admin_notice = "admin_notice"
    system = "system"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recipient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(
        Enum(NotificationKind, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    recipient: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="notifications"
    )

```

### `backend/app/models/post.py`
```python
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    discussion_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("discussions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="SET NULL"), nullable=True
    )
    is_accepted_answer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    upvote_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    discussion: Mapped["Discussion"] = relationship(  # noqa: F821
        "Discussion", back_populates="posts"
    )
    author: Mapped["User"] = relationship("User", back_populates="posts")  # noqa: F821
    replies: Mapped[list["Post"]] = relationship(
        "Post", foreign_keys=[parent_id], lazy="select"
    )

```

### `backend/app/models/user.py`
```python
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    member = "member"
    moderator = "moderator"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.member.value,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # relationships
    discussions: Mapped[list["Discussion"]] = relationship(  # noqa: F821
        "Discussion", back_populates="author", lazy="select"
    )
    posts: Mapped[list["Post"]] = relationship(  # noqa: F821
        "Post", back_populates="author", lazy="select"
    )
    kb_articles: Mapped[list["KBArticle"]] = relationship(  # noqa: F821
        "KBArticle", back_populates="author", lazy="select"
    )
    notifications: Mapped[list["Notification"]] = relationship(  # noqa: F821
        "Notification", back_populates="recipient", lazy="select"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(  # noqa: F821
        "AuditLog", back_populates="actor", lazy="select"
    )

```

### `backend/app/routers/__init__.py`
```python
# backend/app/routers/__init__.py

```

### `backend/app/routers/admin.py`
```python
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_admin
from app.core.exceptions import AppError
from app.models.user import User
from app.schemas.misc_schemas import AuditLogResponse
from app.schemas.user_schemas import UserResponse
from app.services import audit_service, user_service

router = APIRouter(prefix="/admin", tags=["admin"])


def _err(e: AppError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/users", response_model=dict)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    from sqlalchemy import func
    count_q = select(func.count(User.id))
    total = (await db.execute(count_q)).scalar_one()
    q = select(User).order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    users = list((await db.execute(q)).scalars().all())
    return {
        "items": [UserResponse.model_validate(u).model_dump() for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.patch("/users/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        user = await user_service.admin_set_user_active(db, user_id, True)
        await audit_service.record(
            db, "admin.user.activate", actor=admin,
            resource_type="user", resource_id=str(user_id)
        )
        return user
    except AppError as e:
        raise _err(e)


@router.patch("/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        user = await user_service.admin_set_user_active(db, user_id, False)
        await audit_service.record(
            db, "admin.user.deactivate", actor=admin,
            resource_type="user", resource_id=str(user_id)
        )
        return user
    except AppError as e:
        raise _err(e)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def set_user_role(
    user_id: int,
    role: str = Query(...),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        user = await user_service.admin_set_user_role(db, user_id, role)
        await audit_service.record(
            db, "admin.user.role_change", actor=admin,
            resource_type="user", resource_id=str(user_id), detail=f"role={role}"
        )
        return user
    except AppError as e:
        raise _err(e)


@router.get("/audit-logs", response_model=dict)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: str | None = None,
    actor_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    items, total = await audit_service.list_audit_logs(db, page, page_size, action, actor_id)
    return {
        "items": [AuditLogResponse.model_validate(a).model_dump() for a in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/stats")
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    from sqlalchemy import func
    from app.models.discussion import Discussion
    from app.models.post import Post
    from app.models.kb_article import KBArticle

    user_count = (await db.execute(select(func.count(User.id)))).scalar_one()
    disc_count = (await db.execute(select(func.count(Discussion.id)))).scalar_one()
    post_count = (await db.execute(select(func.count(Post.id)))).scalar_one()
    kb_count = (await db.execute(select(func.count(KBArticle.id)))).scalar_one()
    return {
        "users": user_count,
        "discussions": disc_count,
        "posts": post_count,
        "kb_articles": kb_count,
    }

```

### `backend/app/routers/auth.py`
```python
    UserLoginRequest,

def _app_error(e: AppError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=e.detail)

        raise _app_error(e)
async def login(req: UserLoginRequest, db: AsyncSession = Depends(get_db)) -> dict:
        access, refresh = await user_service.authenticate_user(db, req)
        raise _app_error(e)
        raise _app_error(e)
        raise _app_error(e)
        raise _app_error(e)
        raise _app_error(e)
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.exceptions import AppError
from app.models.user import User
from app.schemas.user_schemas import (
    UserRegisterRequest,
    UserResponse,
    TokenResponse,
    RefreshRequest,
    PasswordChangeRequest,
    UserUpdateRequest,
)
from app.services import user_service
router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(req: UserRegisterRequest, db: AsyncSession = Depends(get_db)) -> User:
    try:
        return await user_service.register_user(db, req)
    except AppError as e:

@router.post("/token", response_model=TokenResponse)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> dict:

    try:
        access, refresh = await user_service.authenticate_user(
            db, UserLoginRequest(email=form_data.username, password=form_data.password)
        )
        return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}
    except AppError as e:


@router.post("/login", response_model=TokenResponse)

    try:
        return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}
    except AppError as e:






@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest, db: AsyncSession = Depends(get_db)) -> dict:
    try:
        access, new_refresh = await user_service.refresh_tokens(db, req.refresh_token)
        return {"access_token": access, "refresh_token": new_refresh, "token_type": "bearer"}
    except AppError as e:


@users_router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user


@users_router.put("/me", response_model=UserResponse)
async def update_me(
    req: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        return await user_service.update_user_profile(db, current_user, req)
    except AppError as e:


@users_router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    req: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await user_service.change_password(db, current_user, req)
    except AppError as e:


@users_router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)) -> User:
    try:
        return await user_service.get_user_by_id(db, user_id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

```

### `backend/app/routers/discussions.py`
```python
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user, require_admin
from app.core.exceptions import AppError
from app.models.user import User
from app.schemas.discussion_schemas import (
    DiscussionCreateRequest,
    DiscussionUpdateRequest,
    DiscussionResponse,
    PostCreateRequest,
    PostUpdateRequest,
    PostResponse,
)
from app.services import discussion_service

router = APIRouter(prefix="/discussions", tags=["discussions"])


def _err(e: AppError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=DiscussionResponse, status_code=status.HTTP_201_CREATED)
async def create_discussion(
    req: DiscussionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await discussion_service.create_discussion(db, current_user, req)
    except AppError as e:
        raise _err(e)


@router.get("", response_model=dict)
async def list_discussions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    items, total = await discussion_service.list_discussions(db, page, page_size, status_filter)
    from app.schemas.discussion_schemas import DiscussionResponse as DR
    return {
        "items": [DR.model_validate(d).model_dump() for d in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{discussion_id}", response_model=DiscussionResponse)
async def get_discussion(discussion_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await discussion_service.get_discussion(db, discussion_id)
    except AppError as e:
        raise _err(e)


@router.put("/{discussion_id}", response_model=DiscussionResponse)
async def update_discussion(
    discussion_id: int,
    req: DiscussionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await discussion_service.update_discussion(db, current_user, discussion_id, req)
    except AppError as e:
        raise _err(e)


@router.delete("/{discussion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_discussion(
    discussion_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        await discussion_service.delete_discussion(db, current_user, discussion_id)
    except AppError as e:
        raise _err(e)


# ── Posts ──────────────────────────────────────────────────────────────────

posts_router = APIRouter(prefix="/discussions/{discussion_id}/posts", tags=["posts"])


@posts_router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    discussion_id: int,
    req: PostCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await discussion_service.create_post(db, current_user, discussion_id, req)
    except AppError as e:
        raise _err(e)


@posts_router.get("", response_model=dict)
async def list_posts(
    discussion_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    items, total = await discussion_service.list_posts(db, discussion_id, page, page_size)
    from app.schemas.discussion_schemas import PostResponse as PR
    return {
        "items": [PR.model_validate(p).model_dump() for p in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@posts_router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    discussion_id: int,
    post_id: int,
    req: PostUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await discussion_service.update_post(db, current_user, post_id, req)
    except AppError as e:
        raise _err(e)


@posts_router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    discussion_id: int,
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        await discussion_service.delete_post(db, current_user, post_id)
    except AppError as e:
        raise _err(e)


@posts_router.post("/{post_id}/accept", response_model=PostResponse)
async def accept_answer(
    discussion_id: int,
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await discussion_service.mark_accepted_answer(db, current_user, discussion_id, post_id)
    except AppError as e:
        raise _err(e)

```

### `backend/app/routers/kb.py`
```python
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.exceptions import AppError
from app.models.user import User
from app.schemas.kb_schemas import (
    KBArticleCreateRequest,
    KBArticleUpdateRequest,
    KBArticleResponse,
)
from app.services import kb_service

router = APIRouter(prefix="/kb", tags=["knowledge-base"])


def _err(e: AppError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=KBArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    req: KBArticleCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await kb_service.create_article(db, current_user, req)
    except AppError as e:
        raise _err(e)


@router.get("", response_model=dict)
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    items, total = await kb_service.list_articles(db, page, page_size, status_filter, category)
    return {
        "items": [KBArticleResponse.model_validate(a).model_dump() for a in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/slug/{slug}", response_model=KBArticleResponse)
async def get_article_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    try:
        return await kb_service.get_article_by_slug(db, slug)
    except AppError as e:
        raise _err(e)


@router.get("/{article_id}", response_model=KBArticleResponse)
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await kb_service.get_article(db, article_id)
    except AppError as e:
        raise _err(e)


@router.put("/{article_id}", response_model=KBArticleResponse)
async def update_article(
    article_id: int,
    req: KBArticleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await kb_service.update_article(db, current_user, article_id, req)
    except AppError as e:
        raise _err(e)


@router.post("/{article_id}/publish", response_model=KBArticleResponse)
async def publish_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await kb_service.publish_article(db, current_user, article_id)
    except AppError as e:
        raise _err(e)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        await kb_service.delete_article(db, current_user, article_id)
    except AppError as e:
        raise _err(e)

```

### `backend/app/routers/notifications.py`
```python
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.exceptions import AppError
from app.models.user import User
from app.schemas.misc_schemas import NotificationResponse, NotificationMarkReadRequest
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _err(e: AppError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("", response_model=dict)
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    items, total = await notification_service.list_notifications(
        db, current_user, page, page_size, unread_only
    )
    return {
        "items": [NotificationResponse.model_validate(n).model_dump() for n in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "unread_count": await notification_service.get_unread_count(db, current_user),
    }


@router.post("/mark-read", status_code=status.HTTP_200_OK)
async def mark_read(
    req: NotificationMarkReadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    count = await notification_service.mark_read(db, current_user, req.notification_ids)
    return {"marked": count}


@router.post("/mark-all-read", status_code=status.HTTP_200_OK)
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    count = await notification_service.mark_all_read(db, current_user)
    return {"marked": count}


@router.get("/unread-count")
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    count = await notification_service.get_unread_count(db, current_user)
    return {"unread_count": count}

```

### `backend/app/routers/search.py`
```python
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import search_service

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search(
    q: str = Query(min_length=1, max_length=200),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await search_service.full_text_search(db, q, page, page_size)

```

### `backend/app/schemas/__init__.py`
```python
from app.schemas.user_schemas import (
    UserRegisterRequest as UserRegisterRequest,
    UserLoginRequest as UserLoginRequest,
    UserResponse as UserResponse,
    UserUpdateRequest as UserUpdateRequest,
    TokenResponse as TokenResponse,
    RefreshRequest as RefreshRequest,
    PasswordChangeRequest as PasswordChangeRequest,
)
from app.schemas.discussion_schemas import (
    DiscussionCreateRequest as DiscussionCreateRequest,
    DiscussionUpdateRequest as DiscussionUpdateRequest,
    DiscussionResponse as DiscussionResponse,
    PostCreateRequest as PostCreateRequest,
    PostUpdateRequest as PostUpdateRequest,
    PostResponse as PostResponse,
)
from app.schemas.kb_schemas import (
    KBArticleCreateRequest as KBArticleCreateRequest,
    KBArticleUpdateRequest as KBArticleUpdateRequest,
    KBArticleResponse as KBArticleResponse,
)
from app.schemas.misc_schemas import (
    NotificationResponse as NotificationResponse,
    NotificationMarkReadRequest as NotificationMarkReadRequest,
    SearchResponse as SearchResponse,
    AuditLogResponse as AuditLogResponse,
    PaginatedResponse as PaginatedResponse,
)

```

### `backend/app/schemas/discussion_schemas.py`
```python
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DiscussionCreateRequest(BaseModel):
    title: str = Field(min_length=5, max_length=300)
    body: str = Field(min_length=10)
    tags: str | None = Field(default=None, max_length=500)


class DiscussionUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=300)
    body: str | None = None
    tags: str | None = None
    status: str | None = None


class DiscussionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    body: str
    author_id: int
    status: str
    is_pinned: bool
    view_count: int
    tags: str | None
    created_at: datetime
    updated_at: datetime


class PostCreateRequest(BaseModel):
    body: str = Field(min_length=1)
    parent_id: int | None = None


class PostUpdateRequest(BaseModel):
    body: str = Field(min_length=1)


class PostResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    body: str
    discussion_id: int
    author_id: int
    parent_id: int | None
    is_accepted_answer: bool
    is_deleted: bool
    upvote_count: int
    created_at: datetime
    updated_at: datetime

```

### `backend/app/schemas/kb_schemas.py`
```python
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class KBArticleCreateRequest(BaseModel):
    title: str = Field(min_length=5, max_length=300)
    body: str = Field(min_length=10)
    summary: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=100)
    tags: str | None = Field(default=None, max_length=500)


class KBArticleUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=300)
    body: str | None = None
    summary: str | None = None
    category: str | None = None
    tags: str | None = None
    status: str | None = None


class KBArticleResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    slug: str
    body: str
    summary: str | None
    author_id: int
    status: str
    category: str | None
    tags: str | None
    view_count: int
    created_at: datetime
    updated_at: datetime

```

### `backend/app/schemas/misc_schemas.py`
```python
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    recipient_id: int
    kind: str
    title: str
    body: str | None
    resource_url: str | None
    is_read: bool
    created_at: datetime


class NotificationMarkReadRequest(BaseModel):
    notification_ids: list[int]


class SearchResponse(BaseModel):
    query: str
    discussions: list[dict]
    kb_articles: list[dict]
    total: int


class AuditLogResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    actor_id: int | None
    action: str
    resource_type: str | None
    resource_id: str | None
    detail: str | None
    created_at: datetime


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    pages: int

```

### `backend/app/schemas/user_schemas.py`
```python
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_\-]+$")
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    email: str
    username: str
    display_name: str
    role: str
    is_active: bool
    is_verified: bool
    bio: str | None
    avatar_url: str | None
    created_at: datetime


class UserUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    bio: str | None = Field(default=None, max_length=1000)
    avatar_url: str | None = Field(default=None, max_length=500)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)

```

### `backend/app/services/__init__.py`
```python
from app.services.user_service import (
    register_user as register_user,
    authenticate_user as authenticate_user,
    refresh_tokens as refresh_tokens,
    get_user_by_id as get_user_by_id,
    update_user_profile as update_user_profile,
    change_password as change_password,
    admin_set_user_active as admin_set_user_active,
    admin_set_user_role as admin_set_user_role,
)
from app.services.discussion_service import (
    create_discussion as create_discussion,
    list_discussions as list_discussions,
    get_discussion as get_discussion,
    update_discussion as update_discussion,
    delete_discussion as delete_discussion,
    create_post as create_post,
    list_posts as list_posts,
    get_post as get_post,
    update_post as update_post,
    delete_post as delete_post,
    mark_accepted_answer as mark_accepted_answer,
)
from app.services.kb_service import (
    create_article as create_article,
    list_articles as list_articles,
    get_article as get_article,
    get_article_by_slug as get_article_by_slug,
    update_article as update_article,
    publish_article as publish_article,
    delete_article as delete_article,
)
from app.services.search_service import full_text_search as full_text_search
from app.services.notification_service import (
    create_notification as create_notification,
    list_notifications as list_notifications,
    mark_read as mark_read,
    mark_all_read as mark_all_read,
    get_unread_count as get_unread_count,
)
from app.services.audit_service import (
    record as record,
    list_audit_logs as list_audit_logs,
)

```

### `backend/app/services/audit_service.py`
```python
from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.user import User


async def record(
    db: AsyncSession,
    action: str,
    actor: User | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    detail: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_id=actor.id if actor else None,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        detail=detail,
    )
    db.add(entry)
    await db.flush()
    return entry


async def list_audit_logs(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 50,
    action: str | None = None,
    actor_id: int | None = None,
) -> tuple[list[AuditLog], int]:
    q = select(AuditLog)
    if action:
        q = q.where(AuditLog.action == action)
    if actor_id:
        q = q.where(AuditLog.actor_id == actor_id)
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()
    q = q.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return list(result.scalars().all()), total

```

### `backend/app/services/discussion_service.py`
```python
from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ForbiddenError
from app.models.discussion import Discussion, DiscussionStatus
from app.models.post import Post
from app.models.user import User
from app.schemas.discussion_schemas import (
    DiscussionCreateRequest,
    DiscussionUpdateRequest,
    PostCreateRequest,
    PostUpdateRequest,
)

# Allowed discussion state transitions
_DISCUSSION_TRANSITIONS: dict[str, list[str]] = {
    DiscussionStatus.open.value: [DiscussionStatus.closed.value, DiscussionStatus.locked.value],
    DiscussionStatus.closed.value: [DiscussionStatus.open.value, DiscussionStatus.archived.value],
    DiscussionStatus.locked.value: [DiscussionStatus.archived.value],
    DiscussionStatus.archived.value: [],
}


async def create_discussion(db: AsyncSession, author: User, req: DiscussionCreateRequest) -> Discussion:
    discussion = Discussion(
        title=req.title,
        body=req.body,
        author_id=author.id,
        tags=req.tags,
        status=DiscussionStatus.open.value,
    )
    db.add(discussion)
    await db.flush()
    return discussion


async def list_discussions(
    db: AsyncSession, page: int = 1, page_size: int = 20, status: str | None = None
) -> tuple[list[Discussion], int]:
    q = select(Discussion)
    if status:
        q = q.where(Discussion.status == status)
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()
    q = q.order_by(Discussion.is_pinned.desc(), Discussion.created_at.desc())
    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def get_discussion(db: AsyncSession, discussion_id: int) -> Discussion:
    result = await db.execute(select(Discussion).where(Discussion.id == discussion_id))
    d = result.scalar_one_or_none()
    if not d:
        raise NotFoundError("Discussion not found")
    # increment view count
    d.view_count += 1
    db.add(d)
    await db.flush()
    return d


async def update_discussion(
    db: AsyncSession, actor: User, discussion_id: int, req: DiscussionUpdateRequest
) -> Discussion:
    result = await db.execute(select(Discussion).where(Discussion.id == discussion_id))
    d = result.scalar_one_or_none()
    if not d:
        raise NotFoundError("Discussion not found")
    if d.author_id != actor.id and actor.role not in ("admin", "moderator"):
        raise ForbiddenError("Not allowed to update this discussion")
    if req.status and req.status != d.status:
        allowed = _DISCUSSION_TRANSITIONS.get(d.status, [])
        if req.status not in allowed:
            raise ConflictError(f"Cannot transition from {d.status} to {req.status}")
        d.status = req.status
    if req.title is not None:
        d.title = req.title
    if req.body is not None:
        d.body = req.body
    if req.tags is not None:
        d.tags = req.tags
    db.add(d)
    await db.flush()
    return d


async def delete_discussion(db: AsyncSession, actor: User, discussion_id: int) -> None:
    result = await db.execute(select(Discussion).where(Discussion.id == discussion_id))
    d = result.scalar_one_or_none()
    if not d:
        raise NotFoundError("Discussion not found")
    if d.author_id != actor.id and actor.role not in ("admin", "moderator"):
        raise ForbiddenError("Not allowed to delete this discussion")
    await db.delete(d)
    await db.flush()


# ── Posts ──────────────────────────────────────────────────────────────────


async def create_post(
    db: AsyncSession, author: User, discussion_id: int, req: PostCreateRequest
) -> Post:
    result = await db.execute(select(Discussion).where(Discussion.id == discussion_id))
    d = result.scalar_one_or_none()
    if not d:
        raise NotFoundError("Discussion not found")
    if d.status in (DiscussionStatus.locked.value, DiscussionStatus.archived.value):
        raise ConflictError("Discussion is locked or archived")
    post = Post(
        body=req.body,
        discussion_id=discussion_id,
        author_id=author.id,
        parent_id=req.parent_id,
    )
    db.add(post)
    await db.flush()
    return post


async def list_posts(
    db: AsyncSession, discussion_id: int, page: int = 1, page_size: int = 20
) -> tuple[list[Post], int]:
    q = select(Post).where(Post.discussion_id == discussion_id, Post.is_deleted == False)  # noqa: E712
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()
    q = q.order_by(Post.created_at.asc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def get_post(db: AsyncSession, post_id: int) -> Post:
    result = await db.execute(select(Post).where(Post.id == post_id, Post.is_deleted == False))  # noqa: E712
    post = result.scalar_one_or_none()
    if not post:
        raise NotFoundError("Post not found")
    return post


async def update_post(db: AsyncSession, actor: User, post_id: int, req: PostUpdateRequest) -> Post:
    post = await get_post(db, post_id)
    if post.author_id != actor.id and actor.role not in ("admin", "moderator"):
        raise ForbiddenError("Not allowed to edit this post")
    post.body = req.body
    db.add(post)
    await db.flush()
    return post


async def delete_post(db: AsyncSession, actor: User, post_id: int) -> None:
    post = await get_post(db, post_id)
    if post.author_id != actor.id and actor.role not in ("admin", "moderator"):
        raise ForbiddenError("Not allowed to delete this post")
    post.is_deleted = True
    db.add(post)
    await db.flush()


async def mark_accepted_answer(db: AsyncSession, actor: User, discussion_id: int, post_id: int) -> Post:
    result = await db.execute(select(Discussion).where(Discussion.id == discussion_id))
    d = result.scalar_one_or_none()
    if not d:
        raise NotFoundError("Discussion not found")
    if d.author_id != actor.id and actor.role not in ("admin", "moderator"):
        raise ForbiddenError("Only discussion author or moderator can mark accepted answer")
    post = await get_post(db, post_id)
    if post.discussion_id != discussion_id:
        raise ConflictError("Post does not belong to this discussion")
    # unmark any existing
    existing = await db.execute(
        select(Post).where(Post.discussion_id == discussion_id, Post.is_accepted_answer == True)  # noqa: E712
    )
    for p in existing.scalars().all():
        p.is_accepted_answer = False
        db.add(p)
    post.is_accepted_answer = True
    db.add(post)
    await db.flush()
    return post

```

### `backend/app/services/kb_service.py`
```python
from __future__ import annotations

import re

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ForbiddenError
from app.models.kb_article import KBArticle, ArticleStatus
from app.models.user import User
from app.schemas.kb_schemas import KBArticleCreateRequest, KBArticleUpdateRequest


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:300]


async def _unique_slug(db: AsyncSession, base_slug: str) -> str:
    slug = base_slug
    i = 1
    while True:
        result = await db.execute(select(KBArticle).where(KBArticle.slug == slug))
        if not result.scalar_one_or_none():
            return slug
        slug = f"{base_slug}-{i}"
        i += 1


async def create_article(db: AsyncSession, author: User, req: KBArticleCreateRequest) -> KBArticle:
    slug = await _unique_slug(db, _slugify(req.title))
    article = KBArticle(
        title=req.title,
        slug=slug,
        body=req.body,
        summary=req.summary,
        author_id=author.id,
        category=req.category,
        tags=req.tags,
        status=ArticleStatus.draft.value,
    )
    db.add(article)
    await db.flush()
    return article


async def list_articles(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    category: str | None = None,
) -> tuple[list[KBArticle], int]:
    q = select(KBArticle)
    if status:
        q = q.where(KBArticle.status == status)
    if category:
        q = q.where(KBArticle.category == category)
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()
    q = q.order_by(KBArticle.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def get_article(db: AsyncSession, article_id: int) -> KBArticle:
    result = await db.execute(select(KBArticle).where(KBArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise NotFoundError("Article not found")
    article.view_count += 1
    db.add(article)
    await db.flush()
    return article


async def get_article_by_slug(db: AsyncSession, slug: str) -> KBArticle:
    result = await db.execute(select(KBArticle).where(KBArticle.slug == slug))
    article = result.scalar_one_or_none()
    if not article:
        raise NotFoundError("Article not found")
    article.view_count += 1
    db.add(article)
    await db.flush()
    return article


async def update_article(
    db: AsyncSession, actor: User, article_id: int, req: KBArticleUpdateRequest
) -> KBArticle:
    result = await db.execute(select(KBArticle).where(KBArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise NotFoundError("Article not found")
    if article.author_id != actor.id and actor.role not in ("admin", "moderator"):
        raise ForbiddenError("Not allowed to update this article")
    if req.title is not None:
        article.title = req.title
    if req.body is not None:
        article.body = req.body
    if req.summary is not None:
        article.summary = req.summary
    if req.category is not None:
        article.category = req.category
    if req.tags is not None:
        article.tags = req.tags
    if req.status is not None:
        valid = [s.value for s in ArticleStatus]
        if req.status not in valid:
            raise ConflictError(f"Invalid status: {req.status}")
        article.status = req.status
    db.add(article)
    await db.flush()
    return article


async def publish_article(db: AsyncSession, actor: User, article_id: int) -> KBArticle:
    result = await db.execute(select(KBArticle).where(KBArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise NotFoundError("Article not found")
    if article.author_id != actor.id and actor.role not in ("admin", "moderator"):
        raise ForbiddenError("Not allowed to publish this article")
    article.status = ArticleStatus.published.value
    db.add(article)
    await db.flush()
    return article


async def delete_article(db: AsyncSession, actor: User, article_id: int) -> None:
    result = await db.execute(select(KBArticle).where(KBArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise NotFoundError("Article not found")
    if article.author_id != actor.id and actor.role not in ("admin", "moderator"):
        raise ForbiddenError("Not allowed to delete this article")
    await db.delete(article)
    await db.flush()

```

### `backend/app/services/notification_service.py`
```python
from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationKind
from app.models.user import User


async def create_notification(
    db: AsyncSession,
    recipient_id: int,
    kind: NotificationKind,
    title: str,
    body: str | None = None,
    resource_url: str | None = None,
) -> Notification:
    notif = Notification(
        recipient_id=recipient_id,
        kind=kind.value,
        title=title,
        body=body,
        resource_url=resource_url,
        is_read=False,
    )
    db.add(notif)
    await db.flush()
    return notif


async def list_notifications(
    db: AsyncSession, recipient: User, page: int = 1, page_size: int = 20, unread_only: bool = False
) -> tuple[list[Notification], int]:
    q = select(Notification).where(Notification.recipient_id == recipient.id)
    if unread_only:
        q = q.where(Notification.is_read == False)  # noqa: E712
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()
    q = q.order_by(Notification.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def mark_read(db: AsyncSession, recipient: User, notification_ids: list[int]) -> int:
    result = await db.execute(
        select(Notification).where(
            Notification.id.in_(notification_ids),
            Notification.recipient_id == recipient.id,
        )
    )
    notifications = result.scalars().all()
    count = 0
    for n in notifications:
        if not n.is_read:
            n.is_read = True
            db.add(n)
            count += 1
    await db.flush()
    return count


async def mark_all_read(db: AsyncSession, recipient: User) -> int:
    result = await db.execute(
        select(Notification).where(
            Notification.recipient_id == recipient.id,
            Notification.is_read == False,  # noqa: E712
        )
    )
    notifications = result.scalars().all()
    for n in notifications:
        n.is_read = True
        db.add(n)
    await db.flush()
    return len(notifications)


async def get_unread_count(db: AsyncSession, recipient: User) -> int:
    result = await db.execute(
        select(func.count()).where(
            Notification.recipient_id == recipient.id,
            Notification.is_read == False,  # noqa: E712
        )
    )
    return result.scalar_one()

```

### `backend/app/services/search_service.py`
```python
from __future__ import annotations

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discussion import Discussion
from app.models.kb_article import KBArticle, ArticleStatus


async def full_text_search(
    db: AsyncSession, query: str, page: int = 1, page_size: int = 20
) -> dict:
    """Simple LIKE-based search over discussions and KB articles."""
    pattern = f"%{query}%"

    # Discussions
    disc_q = select(Discussion).where(
        or_(Discussion.title.ilike(pattern), Discussion.body.ilike(pattern))
    )
    disc_count = (await db.execute(select(func.count()).select_from(disc_q.subquery()))).scalar_one()
    disc_q = disc_q.order_by(Discussion.created_at.desc()).limit(page_size)
    discussions = list((await db.execute(disc_q)).scalars().all())

    # KB articles (published only)
    kb_q = select(KBArticle).where(
        KBArticle.status == ArticleStatus.published.value,
        or_(KBArticle.title.ilike(pattern), KBArticle.body.ilike(pattern)),
    )
    kb_count = (await db.execute(select(func.count()).select_from(kb_q.subquery()))).scalar_one()
    kb_q = kb_q.order_by(KBArticle.updated_at.desc()).limit(page_size)
    articles = list((await db.execute(kb_q)).scalars().all())

    return {
        "query": query,
        "discussions": [
            {"id": d.id, "title": d.title, "status": d.status, "created_at": d.created_at.isoformat()}
            for d in discussions
        ],
        "kb_articles": [
            {"id": a.id, "title": a.title, "slug": a.slug, "category": a.category}
            for a in articles
        ],
        "total": disc_count + kb_count,
    }

```

### `backend/app/services/user_service.py`
```python
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ForbiddenError
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token_safe
from app.models.user import User, UserRole
from app.schemas.user_schemas import UserRegisterRequest, UserLoginRequest, UserUpdateRequest, PasswordChangeRequest


async def register_user(db: AsyncSession, req: UserRegisterRequest) -> User:
    # duplicate check
    existing = await db.execute(
        select(User).where((User.email == req.email) | (User.username == req.username))
    )
    if existing.scalar_one_or_none():
        raise ConflictError("Email or username already registered")

    user = User(
        email=req.email,
        username=req.username,
        display_name=req.display_name,
        hashed_password=hash_password(req.password),
        role=UserRole.member.value,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()
    return user


async def authenticate_user(db: AsyncSession, req: UserLoginRequest) -> tuple[str, str]:
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise ForbiddenError("Invalid credentials")
    if not user.is_active:
        raise ForbiddenError("Account is disabled")
    access = create_access_token(str(user.id), {"role": user.role})
    refresh = create_refresh_token(str(user.id))
    return access, refresh


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> tuple[str, str]:
    payload = decode_token_safe(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise ForbiddenError("Invalid refresh token")
    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise ForbiddenError("User not found or inactive")
    access = create_access_token(str(user.id), {"role": user.role})
    new_refresh = create_refresh_token(str(user.id))
    return access, new_refresh


async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found")
    return user


async def update_user_profile(db: AsyncSession, user: User, req: UserUpdateRequest) -> User:
    if req.display_name is not None:
        user.display_name = req.display_name
    if req.bio is not None:
        user.bio = req.bio
    if req.avatar_url is not None:
        user.avatar_url = req.avatar_url
    db.add(user)
    await db.flush()
    return user


async def change_password(db: AsyncSession, user: User, req: PasswordChangeRequest) -> None:
    if not verify_password(req.current_password, user.hashed_password):
        raise ForbiddenError("Current password is incorrect")
    user.hashed_password = hash_password(req.new_password)
    db.add(user)
    await db.flush()


async def admin_set_user_active(db: AsyncSession, target_id: int, is_active: bool) -> User:
    user = await get_user_by_id(db, target_id)
    user.is_active = is_active
    db.add(user)
    await db.flush()
    return user


async def admin_set_user_role(db: AsyncSession, target_id: int, role: str) -> User:
    if role not in [r.value for r in UserRole]:
        raise ConflictError(f"Invalid role: {role}")
    user = await get_user_by_id(db, target_id)
    user.role = role
    db.add(user)
    await db.flush()
    return user

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
    "fastapi==0.115.5",
    "uvicorn[standard]>=0.30",
    "sqlalchemy==2.0.36",
    "alembic==1.14.0",
    "aiosqlite==0.20.0",
    "pydantic==2.10.3",
    "pydantic-settings==2.6.1",
    "passlib[bcrypt]==1.7.4",
    "python-jose[cryptography]==3.3.0",
    "python-multipart==0.0.18",
    "email-validator==2.2.0",
    "httpx==0.27.2",
]

[project.optional-dependencies]
dev = [
    "pytest==8.3.4",
    "pytest-asyncio==0.24.0",
    "pytest-cov==6.0.0",
    "ruff>=0.8",
    "mypy>=1.13",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["app*"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.12"
strict = false
ignore_missing_imports = true

```

### `backend/tests/__init__.py`
```python
# backend/tests/__init__.py

```

### `backend/tests/conftest.py`
```python
"""
Shared pytest fixtures for the E2E test suite.

Every test gets:
  - a fresh in-memory SQLite database (per test function)
  - an HTTPX AsyncClient wired to the FastAPI app via ASGITransport
  - helper factories to create and authenticate users
"""
from __future__ import annotations

import sys
import os

# Ensure backend/ is on sys.path so `from app...` imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import User, UserRole
from app.models.notification import Notification, NotificationKind


# ── Per-test isolated in-memory database ──────────────────────────────────

@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    factory = async_sessionmaker(
        bind=db_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """HTTPX AsyncClient backed by in-memory DB via dependency override."""

    async def _override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── User factories ─────────────────────────────────────────────────────────

async def _create_user(
    db: AsyncSession,
    *,
    email: str,
    username: str,
    password: str = "Password1",
    display_name: str | None = None,
    role: str = UserRole.member.value,
    is_active: bool = True,
    is_verified: bool = True,
) -> User:
    user = User(
        email=email,
        username=username,
        display_name=display_name or username,
        hashed_password=hash_password(password),
        role=role,
        is_active=is_active,
        is_verified=is_verified,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def member_user(db_session: AsyncSession) -> User:
    return await _create_user(
        db_session, email="member@example.com", username="member1"
    )


@pytest_asyncio.fixture
async def second_user(db_session: AsyncSession) -> User:
    return await _create_user(
        db_session, email="second@example.com", username="member2"
    )


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    return await _create_user(
        db_session,
        email="admin@example.com",
        username="admin1",
        role=UserRole.admin.value,
    )


@pytest_asyncio.fixture
async def moderator_user(db_session: AsyncSession) -> User:
    return await _create_user(
        db_session,
        email="mod@example.com",
        username="mod1",
        role=UserRole.moderator.value,
    )


# ── Token helpers ──────────────────────────────────────────────────────────

def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(str(user.id), {"role": user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def member_headers(member_user: User) -> dict[str, str]:
    return auth_headers(member_user)


@pytest.fixture
def admin_headers(admin_user: User) -> dict[str, str]:
    return auth_headers(admin_user)


@pytest.fixture
def moderator_headers(moderator_user: User) -> dict[str, str]:
    return auth_headers(moderator_user)


# ── Notification factory ───────────────────────────────────────────────────

async def create_test_notification(
    db: AsyncSession,
    recipient: User,
    kind: NotificationKind = NotificationKind.system,
    title: str = "Test notification",
) -> Notification:
    n = Notification(
        recipient_id=recipient.id,
        kind=kind.value,
        title=title,
        is_read=False,
    )
    db.add(n)
    await db.flush()
    await db.refresh(n)
    return n

```

### `backend/tests/e2e/__init__.py`
```python
# backend/tests/e2e/__init__.py

```

### `backend/tests/e2e/test_jrn001_registration.py`
```python
"""
JRN-001: User Registration Journey
Happy path + key alternates:
  - HP: Register with valid data → 201, user object returned
  - ALT-1: Duplicate email → 409
  - ALT-2: Duplicate username → 409
  - ALT-3: Weak password (no digit) → 422
  - ALT-4: Invalid email format → 422
  - ALT-5: Short username → 422
  - ALT-6: Profile visible after registration (GET /users/{id})
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestJRN001Registration:
    async def test_hp_register_returns_201_with_user(self, client: AsyncClient) -> None:
        """HP: successful registration returns 201 and user payload."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "alice@example.com",
                "username": "alice",
                "display_name": "Alice Smith",
                "password": "Secure1pass",
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["email"] == "alice@example.com"
        assert body["username"] == "alice"
        assert body["display_name"] == "Alice Smith"
        assert body["role"] == "member"
        assert body["is_active"] is True
        # password must not be exposed
        assert "password" not in body
        assert "hashed_password" not in body

    async def test_hp_registered_user_gets_an_id(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "bob@example.com",
                "username": "bob99",
                "display_name": "Bob",
                "password": "Bobpass1",
            },
        )
        assert resp.status_code == 201
        assert isinstance(resp.json()["id"], int)

    async def test_alt1_duplicate_email_returns_409(self, client: AsyncClient) -> None:
        payload = {
            "email": "dup@example.com",
            "username": "unique1",
            "display_name": "User",
            "password": "Password1",
        }
        r1 = await client.post("/api/v1/auth/register", json=payload)
        assert r1.status_code == 201
        payload["username"] = "unique2"
        r2 = await client.post("/api/v1/auth/register", json=payload)
        assert r2.status_code == 409

    async def test_alt2_duplicate_username_returns_409(self, client: AsyncClient) -> None:
        payload = {
            "email": "first@example.com",
            "username": "sameuser",
            "display_name": "User",
            "password": "Password1",
        }
        r1 = await client.post("/api/v1/auth/register", json=payload)
        assert r1.status_code == 201
        payload["email"] = "second@example.com"
        r2 = await client.post("/api/v1/auth/register", json=payload)
        assert r2.status_code == 409

    async def test_alt3_password_without_digit_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "nodigit@example.com",
                "username": "nodigit",
                "display_name": "User",
                "password": "NoDigitHere",
            },
        )
        assert resp.status_code == 422

    async def test_alt4_invalid_email_format_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "username": "bademail",
                "display_name": "User",
                "password": "Password1",
            },
        )
        assert resp.status_code == 422

    async def test_alt5_short_username_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "short@example.com",
                "username": "ab",  # < 3 chars
                "display_name": "User",
                "password": "Password1",
            },
        )
        assert resp.status_code == 422

    async def test_alt6_profile_visible_after_registration(self, client: AsyncClient) -> None:
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "visible@example.com",
                "username": "visibleuser",
                "display_name": "Visible User",
                "password": "Password1",
            },
        )
        assert reg.status_code == 201
        user_id = reg.json()["id"]
        prof = await client.get(f"/api/v1/users/{user_id}")
        assert prof.status_code == 200
        assert prof.json()["id"] == user_id

    async def test_alt7_missing_required_field_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "miss@example.com", "username": "missingpw"},  # no password
        )
        assert resp.status_code == 422

```

### `backend/tests/e2e/test_jrn002_login.py`
```python
"""
JRN-002: Login and Token Management Journey
Happy path + key alternates:
  - HP: Valid credentials → 200, access + refresh tokens
  - HP2: OAuth2 form login (/token endpoint)
  - HP3: Refresh token rotates both tokens
  - ALT-1: Wrong password → 403
  - ALT-2: Non-existent email → 403
  - ALT-3: Deactivated account → 403
  - ALT-4: Access /users/me without token → 401
  - ALT-5: Access /users/me with valid token → 200
  - ALT-6: Profile update via PUT /users/me
  - ALT-7: Password change
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import _create_user, auth_headers


@pytest.mark.asyncio
class TestJRN002Login:
    async def _register(self, client: AsyncClient, suffix: str = "x") -> dict:
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"login{suffix}@example.com",
                "username": f"loginuser{suffix}",
                "display_name": "Login User",
                "password": "Password1",
            },
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    async def test_hp_login_returns_tokens(self, client: AsyncClient) -> None:
        await self._register(client, "a")
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "logina@example.com", "password": "Password1"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    async def test_hp2_oauth2_form_login(self, client: AsyncClient) -> None:
        await self._register(client, "b")
        resp = await client.post(
            "/api/v1/auth/token",
            data={"username": "loginb@example.com", "password": "Password1"},
        )
        assert resp.status_code == 200, resp.text
        assert "access_token" in resp.json()

    async def test_hp3_refresh_rotates_tokens(self, client: AsyncClient) -> None:
        await self._register(client, "c")
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "loginc@example.com", "password": "Password1"},
        )
        refresh_token = login.json()["refresh_token"]
        original_access = login.json()["access_token"]

        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        # tokens must be new
        assert body["access_token"] != original_access

    async def test_alt1_wrong_password_returns_403(self, client: AsyncClient) -> None:
        await self._register(client, "d")
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "logind@example.com", "password": "WrongPass9"},
        )
        assert resp.status_code == 403

    async def test_alt2_nonexistent_email_returns_403(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "Password1"},
        )
        assert resp.status_code == 403

    async def test_alt3_deactivated_account_returns_403(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        user = await _create_user(
            db_session,
            email="inactive@example.com",
            username="inactive1",
            is_active=False,
        )
        await db_session.commit()
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@example.com", "password": "Password1"},
        )
        assert resp.status_code == 403

    async def test_alt4_no_token_returns_401(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/users/me")
        assert resp.status_code == 401

    async def test_alt5_valid_token_returns_me(
        self, client: AsyncClient, member_user, member_headers
    ) -> None:
        resp = await client.get("/api/v1/users/me", headers=member_headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == member_user.email

    async def test_alt6_profile_update(
        self, client: AsyncClient, member_user, member_headers
    ) -> None:
        resp = await client.put(
            "/api/v1/users/me",
            headers=member_headers,
            json={"display_name": "New Name", "bio": "Hello world"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["display_name"] == "New Name"
        assert body["bio"] == "Hello world"

    async def test_alt7_password_change(
        self, client: AsyncClient, member_user, member_headers
    ) -> None:
        resp = await client.post(
            "/api/v1/users/me/change-password",
            headers=member_headers,
            json={"current_password": "Password1", "new_password": "NewPass99"},
        )
        assert resp.status_code == 204
        # should now be able to login with new password
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": member_user.email, "password": "NewPass99"},
        )
        assert login.status_code == 200

    async def test_invalid_refresh_token_returns_403(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "completely.invalid.token"},
        )
        assert resp.status_code == 403

```

### `backend/tests/e2e/test_jrn003_discussion.py`
```python
"""
JRN-003: Discussion Journey
Happy path + key alternates:
  - HP: Authenticated user creates a discussion → 201
  - HP2: List discussions (paginated)
  - HP3: Get discussion increments view count
  - HP4: Author updates own discussion
  - HP5: Author closes discussion (state transition: open → closed)
  - ALT-1: Unauthenticated create → 401
  - ALT-2: Empty title → 422
  - ALT-3: Non-author cannot update → 403
  - ALT-4: Invalid state transition (open → archived) → 409
  - ALT-5: Delete discussion removes it
  - ALT-6: Non-author cannot delete → 403
  - ALT-7: Moderator can update any discussion
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestJRN003Discussion:
    _DISC_PAYLOAD = {
        "title": "How do I configure CORS?",
        "body": "I am trying to configure CORS in my FastAPI app.",
        "tags": "fastapi,cors",
    }

    async def _create(self, client: AsyncClient, headers: dict, payload: dict | None = None) -> dict:
        resp = await client.post(
            "/api/v1/discussions",
            headers=headers,
            json=payload or self._DISC_PAYLOAD,
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    async def test_hp_create_discussion(
        self, client: AsyncClient, member_headers
    ) -> None:
        d = await self._create(client, member_headers)
        assert d["title"] == "How do I configure CORS?"
        assert d["status"] == "open"
        assert d["view_count"] == 0
        assert d["tags"] == "fastapi,cors"

    async def test_hp2_list_discussions_paginated(
        self, client: AsyncClient, member_headers
    ) -> None:
        for i in range(3):
            await self._create(
                client,
                member_headers,
                {"title": f"Discussion {i} about something", "body": "Some body text here yes"},
            )
        resp = await client.get("/api/v1/discussions?page=1&page_size=2")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert body["total"] >= 3
        assert len(body["items"]) <= 2

    async def test_hp3_get_discussion_increments_view_count(
        self, client: AsyncClient, member_headers
    ) -> None:
        d = await self._create(client, member_headers)
        disc_id = d["id"]
        r1 = await client.get(f"/api/v1/discussions/{disc_id}")
        assert r1.status_code == 200
        assert r1.json()["view_count"] == 1
        r2 = await client.get(f"/api/v1/discussions/{disc_id}")
        assert r2.json()["view_count"] == 2

    async def test_hp4_author_updates_own_discussion(
        self, client: AsyncClient, member_headers
    ) -> None:
        d = await self._create(client, member_headers)
        resp = await client.put(
            f"/api/v1/discussions/{d['id']}",
            headers=member_headers,
            json={"title": "Updated: How do I configure CORS properly?"},
        )
        assert resp.status_code == 200
        assert "Updated" in resp.json()["title"]

    async def test_hp5_close_discussion_state_transition(
        self, client: AsyncClient, member_headers
    ) -> None:
        d = await self._create(client, member_headers)
        resp = await client.put(
            f"/api/v1/discussions/{d['id']}",
            headers=member_headers,
            json={"status": "closed"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "closed"

    async def test_alt1_unauthenticated_create_returns_401(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post("/api/v1/discussions", json=self._DISC_PAYLOAD)
        assert resp.status_code == 401

    async def test_alt2_empty_title_returns_422(
        self, client: AsyncClient, member_headers
    ) -> None:
        resp = await client.post(
            "/api/v1/discussions",
            headers=member_headers,
            json={"title": "ab", "body": "body here is fine"},  # title < 5 chars
        )
        assert resp.status_code == 422

    async def test_alt3_non_author_cannot_update(
        self, client: AsyncClient, member_headers, second_user, db_session
    ) -> None:
        from tests.conftest import auth_headers
        d = await self._create(client, member_headers)
        second_hdrs = auth_headers(second_user)
        resp = await client.put(
            f"/api/v1/discussions/{d['id']}",
            headers=second_hdrs,
            json={"title": "Updated by someone else again here"},
        )
        assert resp.status_code == 403

    async def test_alt4_invalid_state_transition_returns_409(
        self, client: AsyncClient, member_headers
    ) -> None:
        d = await self._create(client, member_headers)
        # open → archived is NOT allowed (must go open→closed first)
        resp = await client.put(
            f"/api/v1/discussions/{d['id']}",
            headers=member_headers,
            json={"status": "archived"},
        )
        assert resp.status_code == 409

    async def test_alt5_delete_removes_discussion(
        self, client: AsyncClient, member_headers
    ) -> None:
        d = await self._create(client, member_headers)
        del_resp = await client.delete(
            f"/api/v1/discussions/{d['id']}", headers=member_headers
        )
        assert del_resp.status_code == 204
        get_resp = await client.get(f"/api/v1/discussions/{d['id']}")
        assert get_resp.status_code == 404

    async def test_alt6_non_author_cannot_delete(
        self, client: AsyncClient, member_headers, second_user
    ) -> None:
        from tests.conftest import auth_headers
        d = await self._create(client, member_headers)
        second_hdrs = auth_headers(second_user)
        resp = await client.delete(
            f"/api/v1/discussions/{d['id']}", headers=second_hdrs
        )
        assert resp.status_code == 403

    async def test_alt7_moderator_can_update_any_discussion(
        self, client: AsyncClient, member_headers, moderator_headers
    ) -> None:
        d = await self._create(client, member_headers)
        resp = await client.put(
            f"/api/v1/discussions/{d['id']}",
            headers=moderator_headers,
            json={"title": "Moderated: how to configure CORS"},
        )
        assert resp.status_code == 200

    async def test_get_nonexistent_discussion_returns_404(
        self, client: AsyncClient
    ) -> None:
        resp = await client.get("/api/v1/discussions/999999")
        assert resp.status_code == 404

```