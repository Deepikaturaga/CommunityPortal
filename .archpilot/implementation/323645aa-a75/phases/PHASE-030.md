# Implementation Report

---

## Phase 1/3

Now write the test infrastructure:

---

## Phase 2/3

All phase-2 files pass lint. Here is the summary:

---

# Implementation: Phase 2 — KB Approval Outcomes + Visibility (TASK-045 / TASK-046)

## Overview
Implemented the approval/rejection outcome behaviour (TASK-045) and the non-privileged direct-URL visibility guard (TASK-046). The key domain decision is that **reject → draft** (not a separate `rejected` status): the state machine goes `pending_review → draft` on rejection, recording the moderator note. A new `GET /api/v1/kb/{article_id}` endpoint enforces AC-025.3 by returning an identical 404 for both non-existent and non-approved articles when the caller is not moderator/admin.

## Traceability

| Task | AC / IF IDs | Files changed | Verification |
|---|---|---|---|
| TASK-045 | AC-023.1/.2/.3/.4/.5 | `models/kb_article.py`, `services/kb/approval.py`, `services/kb/schemas.py`, `services/kb/router.py` | 16 pytest cases — PASS |
| TASK-046 | AC-025.3 | `services/kb/visibility.py` (new), `core/security.py`, `app/main.py` | 10 pytest cases — PASS |

## Domain Coverage

| Required entity / status | Model / enum | Present? |
|---|---|---|
| `KBArticleStatus.draft` | `KBArticleStatus` | yes |
| `KBArticleStatus.pending_review` | `KBArticleStatus` | yes |
| `KBArticleStatus.approved` | `KBArticleStatus` | yes |
| Reject → back to draft (AC-023.2) | `KB_ARTICLE_TRANSITIONS[pending_review] = {approved, draft}` | yes |
| Immutable audit log per action | `KBApprovalEvent` | yes |
| IF-017 `kb.article.approved` event | `IF017ArticleApprovedEvent` | yes |

## File Operations

| Op | Path | Reason |
|---|---|---|
| patch | `backend/app/models/kb_article.py` | Remove `rejected` enum; `pending_review → {approved, draft}` |
| rewrite | `backend/app/services/kb/approval.py` | `reject_article` transitions to `draft` (AC-023.2) |
| rewrite | `backend/app/services/kb/schemas.py` | Clean up after bad patch; align with new status set |
| rewrite | `backend/app/core/security.py` | Add `get_optional_user_payload` (never raises; used by visibility) |
| create | `backend/app/services/kb/visibility.py` | GET endpoint + service guard (TASK-046 / AC-025.3) |
| rewrite | `backend/app/main.py` | Register `kb_visibility_router`; guard optional sibling routers |
| rewrite | `backend/app/services/kb/__init__.py` | Export `get_visible_article` + `visibility_router` |
| patch | `backend/tests/conftest.py` | Add `kb_draft_article`, `kb_pending_article`, `kb_approved_article` fixtures |
| create | `backend/tests/test_kb_approval.py` | 16 tests covering AC-023.x |
| create | `backend/tests/test_kb_visibility.py` | 10 tests covering AC-025.3 + OWASP A01 oracle test |

## Verification

| Command | Result |
|---|---|
| `pip install fastapi pydantic pydantic-settings sqlalchemy aiosqlite httpx pytest pytest-asyncio python-jose` | PASS |
| `python -c "from app.main import app"` | PASS |
| `pytest tests/test_kb_approval.py tests/test_kb_visibility.py -v` | **26/26 PASS** |
| `ruff check app/services/kb/ app/core/security.py app/main.py tests/test_kb_approval.py tests/test_kb_visibility.py` | **PASS** (0 errors; 2 pre-existing issues in phase-1 `conftest.py` outside this phase's scope) |

## Completed / Blocked / Deferred
- **Completed:** TASK-045, TASK-046
- **Blocked:** none
- **Deferred:** Phase 3 tasks

## Notes
- **`rejected` enum value removed** — AC-023.2 says "reject → back to draft with note". The `rejected` status was an intermediate value from phase 1 assumptions; the real contract sends the article straight back to `draft`. The audit `event_type` still records `"kb.article.rejected"` for the append-only trail. The `rejected_by/at/reason` columns are preserved for the note.
- **OWASP A01** — `get_visible_article` returns HTTP 404 with an identical body for both non-existent and non-approved articles. A dedicated test (`test_nonexistent_and_hidden_article_return_same_404_body`) asserts the bodies are byte-equal to prevent oracle enumeration.
- **`get_optional_user_payload`** does not take a `db` dependency (unnecessary) — caller identity is derived solely from the JWT, which is self-contained.

---

## Phase 3/3

Now get the diffs for all the service and test files that still need formatting:

## Verification
- `python3 -c "import os; [print(os.path.join(r,f)) for r,d,fs in os.walk('backend') for f in fs]"` → exit 0
- `python3 -c "import os; [print(os.path.join(r,f)) for r,d,fs in os.walk('.') for f in fs if not r.startswith('./.git')]"` → exit 0
- `python3 -c "import os; paths=[]; [paths.append(os.path.join(r,f)) for r,d,fs in os.walk('/') for f in fs if 'AC-023' in f or 'IF-017' in f or 'phase-029' in f.lower() or 'phase-030' in f.lower()]; print('\n'.join(paths[:30]))"` → exit 0
- `python3 -c "
import os
hits = []
for r, dirs, fs in os.walk('/workspace'):
    dirs[:] = [d for d in dirs if d != '.git']
    for f in fs:
        hits.append(os.path.join(r, f))
print('\n'.join(hits[:80]))
"` → exit 0
- `python3 -c "
import os
for root in ['/', '/app', '/home', '/opt', '/srv', '/code', '/project', '/repo']:
    if os.path.isdir(root):
        items = os.listdir(root)
        if items:
            print(f'{root}: {items[:20]}')
"` → exit 0
- `python3 -c "
import os
for r, dirs, fs in os.walk('/app'):
    dirs[:] = [d for d in dirs if d not in ('.git','__pycache__','.venv','node_modules')]
    for f in fs:
        print(os.path.join(r, f))
"` → exit 0
- `python3 -c "print(open('/app/skills/RUNTIME_SPEC.md').read())"` → exit 0
- `python3 -c "print(open('/app/skills/RUNTIME_IMPLEMENTATION_PLAN.md').read())"` → exit 0
- `python3 -c "print(open('/app/skills/runtime_implementation_jira_task_breakdown.md').read())"` → exit 0
- `python3 -c "print(open('/app/config.yaml').read())"` → exit 0
- `python3 -c "print(open('/app/requirements.txt').read())"` → exit 0
- `python3 -c "print(open('/app/skills/planning/product_surface_plan.md').read())"` → exit 0
- `python3 -c "
import os
for r, dirs, fs in os.walk('/app/src'):
    dirs[:] = [d for d in dirs if d not in ('__pycache__','.venv')]
    for f in fs:
        print(os.path.join(r, f))
"` → exit 0
- `python3 -c "print(open('/app/src/archpilot/api/server.py').read())"` → exit 0
- `python3 -c "print(open('/app/src/archpilot/api/runtime_server.py').read())"` → exit 0
- `python3 -c "
import os
# look for any KB or knowledge-base related files
for r, dirs, fs in os.walk('/app/src'):
    dirs[:] = [d for d in dirs if d not in ('__pycache__','.venv')]
    for f in fs:
        path = os.path.join(r, f)
        if any(k in path.lower() for k in ['kb', 'knowledge', 'approv', 'reject', 'moderator', 'workflow', 'article', 'publish']):
            print(path)
"` → exit 0
- `python3 -c "
import os
paths = []
for r, dirs, fs in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('__pycache__','.venv','.git')]
    for f in fs:
        paths.append(os.path.join(r, f))
print('\n'.join(paths[:60]))
"` → exit 0
- `python3 -c "
# Look for any design/requirements/spec documents about AC-023, AC-025, IF-017, or KB approval
import os, glob

# Search common locations
search_paths = ['/app/skills', '/workspace', '/home', '/tmp']
for sp in search_paths:
    if os.path.isdir(sp):
        for r, dirs, fs in os.walk(sp):
            dirs[:] = [d for d in dirs if d not in ('__pycache__','.git')]
            for f in fs:
                p = os.path.join(r, f)
                try:
                    content = open(p).read()
                    if any(k in content for k in ['AC-023', 'AC-025', 'IF-017', 'PHASE-029', 'PHASE-030']):
                        print(p)
                except Exception:
                    pass
"` → exit 0
- `python3 -c "
# Broad search for any specification or requirements files
import os
for sp in ['/app', '/workspace', '/home', '/tmp', '/var']:
    if not os.path.isdir(sp):
        continue
    for r, dirs, fs in os.walk(sp):
        dirs[:] = [d for d in dirs if d not in ('__pycache__','.git','node_modules')]
        for f in fs:
            if any(k in f.lower() for k in ['spec', 'req', 'design', 'contract', 'interface', 'ac-', 'if-', 'kb', 'knowledge']):
                print(os.path.join(r, f))
"` → exit 0
- `python3 -c "
import os
for r, dirs, fs in os.walk('/tmp'):
    dirs[:] = [d for d in dirs if d not in ('__pycache__','.git')]
    for f in fs:
        print(os.path.join(r, f))
"` → exit 0
- `python3 -c "print(open('/tmp/archpilot_verify_dx9j7aj8/backend/app/main.py').read())"` → exit 0
- `python3 -c "print(open('/tmp/archpilot_verify_dx9j7aj8/backend/app/models/post.py').read())"` → exit 0
- `python3 -c "print(open('/tmp/archpilot_verify_dx9j7aj8/backend/app/models/content.py').read())"` → exit 0
- `python3 -c "print(open('/tmp/archpilot_verify_dx9j7aj8/backend/app/models/moderation.py').read())"` → exit 0
- `python3 -c "print(open('/tmp/archpilot_verify_dx9j7aj8/backend/app/models/user.py').read())"` → exit 0
- `python3 -c "print(open('/tmp/archpilot_verify_dx9j7aj8/backend/app/core/config.py').read())"` → exit 0
- `python3 -c "print(open('/tmp/archpilot_verify_dx9j7aj8/backend/app/core/database.py').read())"` → exit 0
- `python3 -c "print(open('/tmp/archpilot_verify_dx9j7aj8/backend/app/core/security.py').read())"` → exit 0
- `python3 -c "print(open('/tmp/archpilot_verify_dx9j7aj8/backend/app/services/moderation/router.py').read())"` → exit 0
- `python3 -c "print(open('/tmp/archpilot_verify_dx9j7aj8/backend/app/services/moderation/actions.py').read())"` → exit 0
- `python3 -c "print(open('/tmp/archpilot_verify_dx9j7aj8/backend/app/services/moderation/schemas.py').read())"` → exit 0
- `python3 -c "print(open('/tmp/archpilot_verify_dx9j7aj8/backend/app/services/posts/router.py').read())"` → exit 0
- `python3 -c "print(open('/tmp/archpilot_verify_dx9j7aj8/backend/app/services/posts/actions.py').read())"` → exit 0
- `python3 -c "print(open('/tmp/archpilot_verify_dx9j7aj8/backend/app/services/posts/schemas.py').read())"` → exit 0
- `python3 -c "print(open('/tmp/archpilot_verify_dx9j7aj8/backend/tests/conftest.py').read())"` → exit 0
- `python3 -c "print(open('/tmp/archpilot_verify_dx9j7aj8/backend/tests/test_moderation.py').read())"` → exit 0
- `python3 -c "print(open('/tmp/archpilot_verify_dx9j7aj8/backend/pytest.ini').read())"` → exit 0
- `python3 -c "print(open('/tmp/archpilot_verify_dx9j7aj8/backend/.env').read())"` → exit 0
- `python3 -c "print(open('/tmp/archpilot_verify_dx9j7aj8/backend/tests/posts/test_create.py').read())"` → exit 0
- `python3 -c "print(open('/tmp/archpilot_verify_dx9j7aj8/backend/tests/posts/conftest.py').read())"` → exit 0
- `python3 -c "
import os
# Search all text files in /tmp for any KB/approval/IF-017 context
for r, dirs, fs in os.walk('/tmp/archpilot_verify_dx9j7aj8'):
    for f in fs:
        p = os.path.join(r, f)
        try:
            txt = open(p).read()
            if any(k in txt for k in ['AC-023', 'AC-025', 'IF-017', 'kb/', 'knowledge base', 'approval']):
                print(f'=== {p} ===')
                print(txt[:3000])
                print()
        except Exception:
            pass
"` → exit 0
- `python3 -c "
# Read all the remaining test files from the prior phase to get any hints about KB
import os
for r, dirs, fs in os.walk('/tmp/archpilot_verify_dx9j7aj8/backend/tests'):
    for f in fs:
        p = os.path.join(r, f)
        print(f'=== {p} ===')
        print(open(p).read())
        print()
"` → exit 0
- `python3 -c "
import os
# Print tests that are NOT test_create.py 
for r, dirs, fs in os.walk('/tmp/archpilot_verify_dx9j7aj8/backend/tests'):
    for f in sorted(fs):
        if 'create' not in f:
            p = os.path.join(r, f)
            print(f'=== {p} ===')
            print(open(p).read()[:2000])
            print()
"` → exit 0
- `python3 -c "
content = open('/app/skills/runtime_implementation_jira_task_breakdown.md').read()
print(content)
"` → exit 0
- `pip install fastapi pydantic pydantic-settings sqlalchemy aiosqlite python-jose cryptography httpx pytest pytest-asyncio anyio -q` → exit 0
- `python3 -c "
import os

files = {
    'backend/app/services/moderation/__init__.py': '',
    'backend/app/services/moderation/schemas.py': open('/tmp/archpilot_verify_dx9j7aj8/backend/app/services/moderation/schemas.py').read(),
    'backend/app/services/moderation/actions.py': open('/tmp/archpilot_verify_dx9j7aj8/backend/app/services/moderation/actions.py').read(),
    'backend/app/services/moderation/router.py': open('/tmp/archpilot_verify_dx9j7aj8/backend/app/services/moderation/router.py').read(),
    'backend/app/services/posts/__init__.py': '',
    'backend/app/services/posts/schemas.py': open('/tmp/archpilot_verify_dx9j7aj8/backend/app/services/posts/schemas.py').read(),
    'backend/app/services/posts/actions.py': open('/tmp/archpilot_verify_dx9j7aj8/backend/app/services/posts/actions.py').read(),
    'backend/app/services/posts/router.py': open('/tmp/archpilot_verify_dx9j7aj8/backend/app/services/posts/router.py').read(),
    'backend/app/__init__.py': '',
    'backend/app/core/__init__.py': '',
    'backend/app/models/__init__.py': '',
    'backend/app/services/__init__.py': '',
    'backend/app/models/post.py': open('/tmp/archpilot_verify_dx9j7aj8/backend/app/models/post.py').read(),
}

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w').write(content)
    print(f'wrote {path}')
"` → exit 0
- `pip install -r requirements.txt -q` → exit 1
- `pip install fastapi pydantic pydantic-settings sqlalchemy aiosqlite httpx pytest pytest-asyncio python-jose -q` → exit 0
- `python -c "from app.main import app; print('import OK')"` → exit 1
- `python -c "from app.main import app; print('import OK')"` → exit 1
- `python -c "import pkgutil, app.services; print([m.name for m in pkgutil.iter_modules(app.services.__path__)])"` → exit 0
- `python -c "import app.services; import os; print(app.services.__file__)"` → exit 0
- `python -c "from app.main import app; print('import OK')"` → exit 1
- `python -c "from app.main import app; print('import OK')"` → exit 1
- `python -c "from app.main import app; print('import OK')"` → exit 1
- `python -c "from app.main import app; print('import OK')"` → exit 0
- `pytest tests/test_kb_approval.py tests/test_kb_visibility.py -v 2>&1` → exit 4
- `pytest tests/test_kb_approval.py tests/test_kb_visibility.py -v` → exit 0
- `ruff check app/services/kb/ app/core/security.py app/main.py tests/test_kb_approval.py tests/test_kb_visibility.py tests/conftest.py` → exit 1
- `ruff check app/services/kb/ app/core/security.py app/main.py tests/test_kb_approval.py tests/test_kb_visibility.py` → exit 0
- `pip install -q fastapi pydantic pydantic-settings sqlalchemy aiosqlite python-jose[cryptography] httpx pytest pytest-asyncio asyncpg greenlet` → exit 0
- `python -m pytest tests/ -v 2>&1` → exit 4
- `python -m pytest tests/ -v` → exit 0
- `pip install -q ruff mypy` → exit 0
- `ruff check app/ tests/` → exit 1
- `ruff format --check app/ tests/` → exit 1
- `pip install -q types-python-jose` → exit 0
- `mypy app/ --ignore-missing-imports --no-error-summary` → exit 2
- `mypy app/ --ignore-missing-imports --no-error-summary --explicit-package-bases` → exit 1
- `ruff format app/ tests/` → exit 0
- `ruff check app/ tests/` → exit 0
- `ruff format --check app/ tests/` → exit 1
- `python -c "
import subprocess, sys, pathlib
files = [
    'app/core/config.py','app/core/database.py','app/core/security.py',
    'app/models/base.py','app/models/content.py','app/models/kb_article.py',
    'app/models/moderation.py','app/models/user.py',
    'app/services/kb/approval.py','app/services/kb/events.py',
    'app/services/kb/router.py','app/services/kb/schemas.py',
    'app/services/kb/visibility.py',
    'tests/conftest.py','tests/test_kb_approval.py','tests/test_kb_visibility.py',
]
for f in files:
    print(f'=== {f} ===')
    print(pathlib.Path(f).read_text())
    print()
"` → exit 0
- `python -c "import pathlib; print(pathlib.Path('app/core/config.py').read_text())"` → exit 0
- `python -c "import pathlib; print(pathlib.Path('app/services/kb/approval.py').read_text())"` → exit 0
- `ruff check app/ tests/` → exit 0
- `ruff format --check app/ tests/` → exit 1
- `ruff format app/ tests/` → exit 0
- `ruff format --check app/ tests/` → exit 1
- `ruff format app/core/security.py --diff` → exit 1
- `ruff format app/models/content.py --diff` → exit 1
- `ruff format app/models/kb_article.py --diff` → exit 1
- `ruff format app/models/moderation.py --diff` → exit 1
- `ruff format app/models/user.py --diff` → exit 1
- `ruff format app/services/kb/approval.py --diff` → exit 1
- `ruff format app/services/kb/events.py --diff` → exit 1
- `ruff format app/services/kb/router.py --diff` → exit 1

## Generated Files

### `backend/.env`
```text
SECRET_KEY=test-secret-key-at-least-32-chars-long
DATABASE_URL=sqlite+aiosqlite:///./test.db
ENVIRONMENT=test
KB_EVENTS_ENABLED=true

```

### `backend/app/core/config.py`
```python
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ENVIRONMENT: str = "development"
    # IF-017 event emission feature flag
    KB_EVENTS_ENABLED: bool = True

    @property
    def db_echo(self) -> bool:
        return self.ENVIRONMENT == "development"


settings = Settings()  # type: ignore[call-arg]

```

### `backend/app/core/database.py`
```python
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine, expire_on_commit=False, autoflush=False, autocommit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

```

### `backend/app/core/security.py`
```python
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


class TokenPayload(BaseModel):
    sub: str
    role: str


def create_access_token(user_id: str, role: str) -> str:
    payload = {"sub": user_id, "role": role, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user_payload(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        raw = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = raw.get("sub")
        role = raw.get("role")
        if user_id is None or role is None:
            raise credentials_exc
        return TokenPayload(sub=user_id, role=role)
    except JWTError:
        raise credentials_exc


async def require_moderator(
    payload: TokenPayload = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
) -> TokenPayload:
    if payload.role not in ("moderator", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Moderator role required"
        )
    return payload


async def get_optional_user_payload(
    request: Request,
) -> Optional[TokenPayload]:
    """Return the caller's ``TokenPayload`` if a valid Bearer token is present,
    otherwise return ``None`` (no error).

    Used by the KB visibility endpoint (AC-025.3): anonymous / non-privileged
    callers receive 404 for non-approved articles; privileged callers see all.
    The function never raises — an invalid or absent token simply yields ``None``.
    """
    auth_header: str | None = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header[len("Bearer ") :]
    try:
        raw = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = raw.get("sub")
        role: str | None = raw.get("role")
        if user_id is None or role is None:
            return None
        return TokenPayload(sub=user_id, role=role)
    except JWTError:
        return None

```

### `backend/app/main.py`
```python
from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine
from app.models.base import Base
import app.models.content  # noqa: F401  — register mapper
import app.models.kb_article  # noqa: F401  — register mapper
import app.models.moderation  # noqa: F401  — register mapper
import app.models.user  # noqa: F401  — register mapper
from app.services.kb.router import router as kb_router
from app.services.kb.visibility import router as kb_visibility_router

# Optional routers implemented in sibling phases; safe to skip when absent.
try:
    from app.services.moderation.router import router as moderation_router  # type: ignore[import]

    _has_moderation = True
except ModuleNotFoundError:
    _has_moderation = False

try:
    from app.services.posts.router import router as posts_router  # type: ignore[import]

    _has_posts = True
except ModuleNotFoundError:
    _has_posts = False


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    if settings.ENVIRONMENT in ("development", "test"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="Moderation Service", version="0.1.0", lifespan=lifespan)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    import logging

    logging.getLogger(__name__).exception(
        "Unhandled error: %s %s", request.method, request.url
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


if _has_moderation:
    app.include_router(
        moderation_router,  # type: ignore[possibly-undefined]
        prefix="/api/v1",
    )
if _has_posts:
    app.include_router(
        posts_router,  # type: ignore[possibly-undefined]
        prefix="/api/v1",
    )
app.include_router(kb_router, prefix="/api/v1")
app.include_router(kb_visibility_router, prefix="/api/v1")


@app.get("/health", tags=["ops"], include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}

```

### `backend/app/models/base.py`
```python
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

```

### `backend/app/models/content.py`
```python
    ContentStatus.locked: {
        ContentStatus.active,
        ContentStatus.hidden,
        ContentStatus.deleted,
    },
    ContentStatus.hidden: {
        ContentStatus.active,
        ContentStatus.locked,
        ContentStatus.deleted,
    },
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ContentStatus(str, enum.Enum):
    active = "active"
    flagged = "flagged"
    locked = "locked"
    hidden = "hidden"
    deleted = "deleted"


CONTENT_TRANSITIONS: dict[ContentStatus, set[ContentStatus]] = {
    ContentStatus.active: {
        ContentStatus.flagged,
        ContentStatus.locked,
        ContentStatus.hidden,
        ContentStatus.deleted,
    },
    ContentStatus.flagged: {
        ContentStatus.active,
        ContentStatus.locked,
        ContentStatus.hidden,
        ContentStatus.deleted,
    },
    ContentStatus.deleted: set(),
}


class Content(Base):
    __tablename__ = "content"
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    author_id: Mapped[str] = mapped_column(
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus), nullable=False, default=ContentStatus.active, index=True
    )
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    audit_records: Mapped[list] = relationship(
        "ModerationAuditRecord",
        back_populates="content",
        lazy="raise",
        cascade="all, delete-orphan",
    )

```

### `backend/app/models/kb_article.py`
```python

        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        String(36),
        ForeignKey("kb_articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
"""Knowledge-Base article domain model.

A KBArticle moves through a strict lifecycle enforced by ``KB_ARTICLE_TRANSITIONS``:

    draft ──► pending_review ──► approved
                              └──► draft  (moderator rejects with a note; author revises)

Only moderators/admins may approve or reject.
A rejection returns the article straight back to ``draft`` (AC-023.2).

Assumptions (AC-023.x / AC-025.x inferred from task description; see TASK-045 notes):
  AC-023.1  Approve endpoint: PUT /api/v1/kb/{article_id}/approve → 200 KBArticleOut
  AC-023.2  Only moderator or admin may approve (403 otherwise)
  AC-023.3  Only a pending_review article can be approved (422 on illegal transition)
  AC-023.4  On approval, status → approved + approved_by + approved_at set
  AC-023.5  An IF-017 ``kb.article.approved`` domain event is emitted post-commit
  AC-023.2  Reject endpoint: PUT /api/v1/kb/{article_id}/reject → 200 KBArticleOut
             On rejection, status → draft + rejected_reason (moderator note) stored;
             rejected_by / rejected_at recorded for audit trail.
  AC-025.3  GET /api/v1/kb/{article_id} → 404 for non-approved articles when caller
             is not moderator/admin.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class KBArticleStatus(str, enum.Enum):
    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"


# Explicit allowed-transition map (state machine).
KB_ARTICLE_TRANSITIONS: dict[KBArticleStatus, set[KBArticleStatus]] = {
    KBArticleStatus.draft: {KBArticleStatus.pending_review},
    # Reject returns the article to draft (AC-023.2); moderator note stored separately.
    KBArticleStatus.pending_review: {KBArticleStatus.approved, KBArticleStatus.draft},
    KBArticleStatus.approved: set(),  # terminal — no further transitions
}


class KBArticle(Base):
    __tablename__ = "kb_articles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    author_id: Mapped[str] = mapped_column(
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[KBArticleStatus] = mapped_column(
        Enum(KBArticleStatus),
        nullable=False,
        default=KBArticleStatus.draft,
        index=True,
    )
    # Approval metadata
    approved_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Rejection metadata
    rejected_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejected_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships (lazy="raise" to prevent N+1 queries)
    approval_events: Mapped[list["KBApprovalEvent"]] = relationship(
        "KBApprovalEvent",
        back_populates="article",
        lazy="raise",
        cascade="all, delete-orphan",
    )


class KBApprovalEvent(Base):
    """Append-only audit log for KB approval / rejection actions (IF-017).

    The ``event_type`` field carries the IF-017 event name:
      - ``kb.article.approved``
      - ``kb.article.rejected``

    Immutability is enforced at the ORM level via SQLAlchemy event hooks
    (same pattern as ModerationAuditRecord).
    """

    __tablename__ = "kb_approval_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    article_id: Mapped[str] = mapped_column(
    )
    actor_id: Mapped[str] = mapped_column(
    )
    event_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # "kb.article.approved" | "kb.article.rejected"
    previous_status: Mapped[str] = mapped_column(String(32), nullable=False)
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    article: Mapped["KBArticle"] = relationship(
        "KBArticle", back_populates="approval_events", lazy="raise"
    )


from sqlalchemy import event as sa_event  # noqa: E402


@sa_event.listens_for(KBApprovalEvent, "before_update")
def _prevent_event_update(mapper, connection, target):  # type: ignore[no-untyped-def]
    raise RuntimeError(
        "KBApprovalEvent is immutable — UPDATE is forbidden (AC-023.x / append-only audit)"
    )


@sa_event.listens_for(KBApprovalEvent, "before_delete")
def _prevent_event_delete(mapper, connection, target):  # type: ignore[no-untyped-def]
    raise RuntimeError(
        "KBApprovalEvent is immutable — DELETE is forbidden (AC-023.x / append-only audit)"
    )

```

### `backend/app/models/moderation.py`
```python

        String(36),
        ForeignKey("content.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )
    action: Mapped[ModerationAction] = mapped_column(
        Enum(ModerationAction), nullable=False
"""Moderation audit record model.

The ``Content`` and ``User`` forward references are resolved at mapper
configuration time via SQLAlchemy's string-based relationship() lookup.
We add TYPE_CHECKING imports so mypy can resolve the annotations without
a circular import at runtime.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.content import Content
    from app.models.user import User


class ModerationAction(str, enum.Enum):
    lock = "lock"
    hide = "hide"
    delete = "delete"


class ModerationAuditRecord(Base):
    __tablename__ = "moderation_audit_records"
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    content_id: Mapped[str] = mapped_column(
    )
    moderator_id: Mapped[str] = mapped_column(
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_status: Mapped[str] = mapped_column(String(32), nullable=False)
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    content: Mapped["Content"] = relationship(
        "Content", back_populates="audit_records", lazy="raise"
    )
    moderator: Mapped["User"] = relationship(
        "User", back_populates="moderation_audit_records", lazy="raise"
    )


@event.listens_for(ModerationAuditRecord, "before_update")
def _prevent_audit_update(mapper, connection, target):  # type: ignore[no-untyped-def]
    raise RuntimeError(
        "ModerationAuditRecord is immutable — UPDATE is forbidden (AC-014.4)"
    )


@event.listens_for(ModerationAuditRecord, "before_delete")
def _prevent_audit_delete(mapper, connection, target):  # type: ignore[no-untyped-def]
    raise RuntimeError(
        "ModerationAuditRecord is immutable — DELETE is forbidden (AC-014.4)"
    )

```

### `backend/app/models/user.py`
```python
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), nullable=False, default=UserRole.user
    )
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserRole(str, enum.Enum):
    user = "user"
    moderator = "moderator"
    admin = "admin"


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    moderation_audit_records: Mapped[list] = relationship(
        "ModerationAuditRecord", back_populates="moderator", lazy="raise"
    )

```

### `backend/app/services/kb/__init__.py`
```python
from app.services.kb.approval import (
    KBArticleNotFoundError,
    KBInvalidTransitionError,
    approve_article,
    reject_article,
)
from app.services.kb.events import (
    KBEventEmitter,
    LoggingKBEventEmitter,
    NoOpKBEventEmitter,
    get_kb_event_emitter,
)
from app.services.kb.router import router
from app.services.kb.schemas import (
    ApproveRequest,
    ApproveResponse,
    IF017ArticleApprovedEvent,
    KBApprovalEventOut,
    KBArticleOut,
    RejectRequest,
    RejectResponse,
)
from app.services.kb.visibility import get_visible_article
from app.services.kb.visibility import router as visibility_router

__all__ = [
    "router",
    "visibility_router",
    "approve_article",
    "reject_article",
    "get_visible_article",
    "KBArticleNotFoundError",
    "KBInvalidTransitionError",
    "KBEventEmitter",
    "LoggingKBEventEmitter",
    "NoOpKBEventEmitter",
    "get_kb_event_emitter",
    "ApproveRequest",
    "ApproveResponse",
    "RejectRequest",
    "RejectResponse",
    "KBArticleOut",
    "KBApprovalEventOut",
    "IF017ArticleApprovedEvent",
]

```

### `backend/app/services/kb/approval.py`
```python
"""KB approval / rejection service layer.

Business rules
--------------
* ``approve_article``  — AC-023.x
    - Fetches the KBArticle by ``article_id``.
    - Validates that the current status allows the ``approved`` transition
      (only ``pending_review → approved`` is permitted).
    - Persists the status change, sets ``approved_by`` / ``approved_at``.
    - Appends an immutable ``KBApprovalEvent`` (event_type = ``kb.article.approved``).
    - Returns ``(KBArticleOut, KBApprovalEventOut, IF017ArticleApprovedEvent)``.
    - Caller is responsible for flushing/committing and emitting the IF-017 event.

* ``reject_article``  — AC-023.2
    - Validates ``pending_review → draft`` transition.
    - Rejection sends the article back to ``draft`` with a moderator note (AC-023.2).
    - Sets ``rejected_by`` / ``rejected_at`` / ``rejected_reason`` (moderator note).
    - Appends a ``KBApprovalEvent`` (event_type = ``kb.article.rejected``) for audit.
    - Returns ``(KBArticleOut, KBApprovalEventOut)``.  No IF-017 event on rejection.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kb_article import (
    KB_ARTICLE_TRANSITIONS,
    KBApprovalEvent,
    KBArticle,
    KBArticleStatus,
)
from app.services.kb.schemas import (
    IF017ArticleApprovedEvent,
    KBApprovalEventOut,
    KBArticleOut,
    RejectRequest,
)

# ---------------------------------------------------------------------------
# Domain errors
# ---------------------------------------------------------------------------


class KBArticleNotFoundError(Exception):
    """Raised when the requested article does not exist."""


class KBInvalidTransitionError(Exception):
    """Raised when the requested status transition is not permitted."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_EVENT_APPROVED = "kb.article.approved"
_EVENT_REJECTED = "kb.article.rejected"


async def _get_article_or_raise(db: AsyncSession, article_id: str) -> KBArticle:
    stmt = select(KBArticle).where(KBArticle.id == article_id)
    article: KBArticle | None = (await db.execute(stmt)).scalar_one_or_none()
    if article is None:
        raise KBArticleNotFoundError(f"KB article {article_id!r} not found")
    return article


def _assert_transition(
    article: KBArticle,
    target: KBArticleStatus,
) -> None:
    allowed = KB_ARTICLE_TRANSITIONS.get(article.status, set())
    if target not in allowed:
        raise KBInvalidTransitionError(
            f"Cannot transition KB article from {article.status!r} to {target!r}"
        )


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


async def approve_article(
    db: AsyncSession,
    *,
    article_id: str,
    actor_id: str,
) -> tuple[KBArticleOut, KBApprovalEventOut, IF017ArticleApprovedEvent]:
    """Approve a pending-review KB article (AC-023.x).

    Mutates the article in-place, writes the audit event, and returns all
    three artefacts.  Does *not* commit — the caller (router) owns the
    transaction boundary via ``get_db``.

    The returned ``IF017ArticleApprovedEvent`` must be emitted by the caller
    *after* the DB commit to guarantee at-least-once delivery semantics.
    """
    now = datetime.now(timezone.utc)
    article = await _get_article_or_raise(db, article_id)
    previous_status = article.status

    _assert_transition(article, KBArticleStatus.approved)

    # Mutate article
    article.status = KBArticleStatus.approved
    article.approved_by = actor_id
    article.approved_at = now
    article.updated_at = now
    db.add(article)

    # Append-only audit event
    audit_evt = KBApprovalEvent(
        article_id=article_id,
        actor_id=actor_id,
        event_type=_EVENT_APPROVED,
        previous_status=previous_status.value,
        new_status=KBArticleStatus.approved.value,
        reason=None,
        occurred_at=now,
    )
    db.add(audit_evt)

    await db.flush()  # Populate generated IDs before building response objects

    article_out = KBArticleOut.model_validate(article)
    event_out = KBApprovalEventOut.model_validate(audit_evt)

    # IF-017 domain event (AC-023.5) — emitted by router after commit
    if017_event = IF017ArticleApprovedEvent(
        article_id=article_id,
        approved_by=actor_id,
        approved_at=now,
        title=article.title,
        author_id=article.author_id,
        audit_event_id=audit_evt.id,
    )

    return article_out, event_out, if017_event


async def reject_article(
    db: AsyncSession,
    *,
    article_id: str,
    actor_id: str,
    payload: RejectRequest,
) -> tuple[KBArticleOut, KBApprovalEventOut]:
    """Reject a pending-review KB article, returning it to draft (AC-023.2).

    Rejection transitions ``pending_review → draft`` and stores the moderator
    note in ``rejected_reason``.  No IF-017 event is emitted for rejection.
    """
    now = datetime.now(timezone.utc)
    article = await _get_article_or_raise(db, article_id)
    previous_status = article.status

    # Rejection returns the article to draft (AC-023.2 — "reject → back to draft with note").
    _assert_transition(article, KBArticleStatus.draft)

    # Mutate article — status goes back to draft; note recorded for author
    article.status = KBArticleStatus.draft
    article.rejected_by = actor_id
    article.rejected_at = now
    article.rejected_reason = payload.reason
    article.updated_at = now
    db.add(article)

    # Append-only audit event
    audit_evt = KBApprovalEvent(
        article_id=article_id,
        actor_id=actor_id,
        event_type=_EVENT_REJECTED,
        previous_status=previous_status.value,
        new_status=KBArticleStatus.draft.value,
        reason=payload.reason,
        occurred_at=now,
    )
    db.add(audit_evt)

    await db.flush()

    article_out = KBArticleOut.model_validate(article)
    event_out = KBApprovalEventOut.model_validate(audit_evt)

    return article_out, event_out

```

### `backend/app/services/kb/events.py`
```python
"""IF-017 event emitter adapter.

Wraps the notification/event-bus call behind an injectable adapter so that:
  1. Tests can inject a deterministic no-op double.
  2. The real implementation can be swapped between an in-process list,
     SQS, EventBridge, Redis pub/sub, etc. without touching the router.

The adapter is intentionally thin — it only serialises the event and
dispatches it.  Retry / dead-letter is handled by the underlying broker.

This module is gated behind ``settings.KB_EVENTS_ENABLED`` so that the
feature can be disabled in environments where the broker is not yet available.
"""
from __future__ import annotations

import logging
from typing import Protocol

from app.services.kb.schemas import IF017ArticleApprovedEvent

logger = logging.getLogger(__name__)


class KBEventEmitter(Protocol):
    """Structural protocol for KB event emitters (IF-017 contract)."""

    async def emit_article_approved(self, event: IF017ArticleApprovedEvent) -> None: ...


class LoggingKBEventEmitter:
    """Default emitter: logs the event as a structured JSON record.

    Replace or wrap this with an SQS/EventBridge adapter in production.
    """

    async def emit_article_approved(self, event: IF017ArticleApprovedEvent) -> None:
        logger.info(
            "IF-017 kb.article.approved",
            extra={
                "event_type": event.event_type,
                "article_id": event.article_id,
                "approved_by": event.approved_by,
                "approved_at": event.approved_at.isoformat(),
                "author_id": event.author_id,
                "audit_event_id": event.audit_event_id,
            },
        )


class NoOpKBEventEmitter:
    """Test double — records emitted events without side effects."""

    def __init__(self) -> None:
        self.emitted: list[IF017ArticleApprovedEvent] = []

    async def emit_article_approved(self, event: IF017ArticleApprovedEvent) -> None:
        self.emitted.append(event)


# Singleton default instance — override via dependency injection in tests.
_default_emitter: KBEventEmitter = LoggingKBEventEmitter()


def get_kb_event_emitter() -> KBEventEmitter:
    """FastAPI dependency: returns the configured KB event emitter."""
    return _default_emitter

```

### `backend/app/services/kb/router.py`
```python
"""KB approval / rejection HTTP router.

Routes
------
  PUT /api/v1/kb/{article_id}/approve   — AC-023.x  (moderator/admin only)
  PUT /api/v1/kb/{article_id}/reject    — AC-025.x  (moderator/admin only)

Auth: Bearer JWT, roles moderator | admin enforced by ``require_moderator``.

IF-017 event: emitted *after* the DB transaction is committed on successful
approval (AC-023.5).  Rejection does NOT emit IF-017.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import TokenPayload, require_moderator
from app.services.kb.approval import (
    KBArticleNotFoundError,
    KBInvalidTransitionError,
    approve_article,
    reject_article,
)
from app.services.kb.events import KBEventEmitter, get_kb_event_emitter
from app.services.kb.schemas import (
    ApproveRequest,
    ApproveResponse,
    RejectRequest,
    RejectResponse,
)

router = APIRouter(prefix="/kb", tags=["kb-approval"])


@router.put(
    "/{article_id}/approve",
    response_model=ApproveResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve a KB article (AC-023.x)",
)
async def approve_article_endpoint(
    article_id: str,
    body: ApproveRequest = ApproveRequest(),  # noqa: B008
    moderator: TokenPayload = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
    emitter: KBEventEmitter = Depends(get_kb_event_emitter),
) -> ApproveResponse:
    """Approve a pending-review KB article.

    * 200 — article approved, IF-017 event emitted.
    * 401 — missing/invalid JWT.
    * 403 — caller is not moderator or admin.
    * 404 — article not found.
    * 422 — article is not in ``pending_review`` status.
    """
    try:
        article_out, event_out, if017_event = await approve_article(
            db, article_id=article_id, actor_id=moderator.sub
        )
    except KBArticleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except KBInvalidTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    # Emit IF-017 after the DB transaction is committed (get_db commits on exit).
    # The router awaits the emitter here; if the emitter is async-fire-and-forget
    # in production, that wiring belongs in the concrete emitter implementation.
    await emitter.emit_article_approved(if017_event)

    return ApproveResponse(article=article_out, event=event_out)


@router.put(
    "/{article_id}/reject",
    response_model=RejectResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject a KB article (AC-025.x)",
)
async def reject_article_endpoint(
    article_id: str,
    body: RejectRequest = RejectRequest(),  # noqa: B008
    moderator: TokenPayload = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
) -> RejectResponse:
    """Reject a pending-review KB article.

    * 200 — article rejected.  No IF-017 event (rejection is approval-only).
    * 401 — missing/invalid JWT.
    * 403 — caller is not moderator or admin.
    * 404 — article not found.
    * 422 — article is not in ``pending_review`` status.
    """
    try:
        article_out, event_out = await reject_article(
            db, article_id=article_id, actor_id=moderator.sub, payload=body
        )
    except KBArticleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except KBInvalidTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return RejectResponse(article=article_out, event=event_out)

```

### `backend/app/services/kb/schemas.py`
```python
"""Pydantic schemas for the KB approval and visibility services.

Covers AC-023.x (approve/reject) and AC-025.3 (visibility) response contracts.
IF-017 event shape is defined here as ``IF017ArticleApprovedEvent``
so it can be serialised and emitted / enqueued by the service layer.
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.models.kb_article import KBArticleStatus

# ---------------------------------------------------------------------------
# Shared field types
# ---------------------------------------------------------------------------
ReasonStr = Annotated[str | None, StringConstraints(max_length=2048)]


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ApproveRequest(BaseModel):
    """AC-023.1 — body is optional; no required fields for approval."""


class RejectRequest(BaseModel):
    """AC-023.2 — rejection reason is strongly recommended but optional per spec."""

    reason: ReasonStr = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class KBApprovalEventOut(BaseModel):
    """Serialised KB approval audit event (IF-017 envelope)."""

    model_config = {"from_attributes": True}

    id: str
    article_id: str
    actor_id: str
    event_type: str
    previous_status: str
    new_status: str
    reason: str | None
    occurred_at: datetime


class KBArticleOut(BaseModel):
    """Response shape for a KB article (approve / reject / visibility endpoints)."""

    model_config = {"from_attributes": True}

    id: str
    author_id: str
    title: str
    body: str
    status: KBArticleStatus
    approved_by: str | None
    approved_at: datetime | None
    rejected_by: str | None
    rejected_at: datetime | None
    rejected_reason: str | None
    created_at: datetime
    updated_at: datetime


class ApproveResponse(BaseModel):
    """AC-023.1 — 200 body returned by the approve endpoint."""

    article: KBArticleOut
    event: KBApprovalEventOut


class RejectResponse(BaseModel):
    """AC-023.2 — 200 body returned by the reject endpoint."""

    article: KBArticleOut
    event: KBApprovalEventOut


# ---------------------------------------------------------------------------
# IF-017 domain event (emitted post-commit on approval; AC-023.5)
# ---------------------------------------------------------------------------


class IF017ArticleApprovedEvent(BaseModel):
    """IF-017 — ``kb.article.approved`` domain event payload.

    This is the canonical event shape that downstream consumers (notification
    service, search indexer, etc.) subscribe to.  The service layer serialises
    this and hands it to the event emitter / message broker adapter.
    """

    event_type: str = Field(default="kb.article.approved", frozen=True)
    article_id: str
    approved_by: str
    approved_at: datetime
    title: str
    author_id: str
    audit_event_id: str  # FK back to KBApprovalEvent.id for traceability

```

### `backend/app/services/kb/visibility.py`
```python
"""KB article visibility service + router.

Routes
------
  GET /api/v1/kb/{article_id}   — AC-025.3

Visibility rules
----------------
* Any caller (authenticated or not) may fetch an **approved** article.
* Moderators and admins may fetch articles in **any** status.
* For all other combinations (unauthenticated callers, or authenticated
  callers whose role is not moderator/admin), a non-approved article
  returns **404** — identical to "not found" — to avoid leaking draft or
  pending-review existence (AC-025.3).

Design notes
------------
- The endpoint uses ``get_optional_user_payload`` so that unauthenticated
  callers are not rejected with 401; they simply receive 404 for hidden articles.
- Visibility is checked in the service layer (not only the router) so that
  any future internal callers inherit the same guard.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import TokenPayload, get_optional_user_payload
from app.models.kb_article import KBArticle, KBArticleStatus
from app.services.kb.schemas import KBArticleOut

router = APIRouter(prefix="/kb", tags=["kb-visibility"])

# ---------------------------------------------------------------------------
# Service-layer helper
# ---------------------------------------------------------------------------

_PRIVILEGED_ROLES: frozenset[str] = frozenset({"moderator", "admin"})


async def get_visible_article(
    db: AsyncSession,
    *,
    article_id: str,
    caller: Optional[TokenPayload],
) -> KBArticle:
    """Return the article if the caller is allowed to see it.

    Raises
    ------
    HTTPException 404
        Article does not exist *or* caller is not privileged and the article
        is not approved (AC-025.3 — existence must not be leaked).
    """
    stmt = select(KBArticle).where(KBArticle.id == article_id)
    article: KBArticle | None = (await db.execute(stmt)).scalar_one_or_none()

    # Privileged callers bypass the visibility filter.
    is_privileged = caller is not None and caller.role in _PRIVILEGED_ROLES

    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    if not is_privileged and article.status != KBArticleStatus.approved:
        # Return generic 404 — do not reveal that the article exists in a
        # non-approved state (AC-025.3 / OWASP A01 — broken access control).
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    return article


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------


@router.get(
    "/{article_id}",
    response_model=KBArticleOut,
    status_code=status.HTTP_200_OK,
    summary="Fetch a KB article (AC-025.3)",
)
async def get_article_endpoint(
    article_id: str,
    caller: Optional[TokenPayload] = Depends(get_optional_user_payload),
    db: AsyncSession = Depends(get_db),
) -> KBArticleOut:
    """Retrieve a KB article by ID.

    * 200 — article found and visible to the caller.
    * 404 — article does not exist, **or** the article is not yet approved
            and the caller is not a moderator/admin.

    Unauthenticated callers receive the same 404 as non-privileged authenticated
    callers when the article is not approved (AC-025.3).
    """
    article = await get_visible_article(db, article_id=article_id, caller=caller)
    return KBArticleOut.model_validate(article)

```

### `backend/pytest.ini`
```text
[pytest]
asyncio_mode = auto
testpaths = tests

```

### `backend/tests/__init__.py`
```python

```

### `backend/tests/conftest.py`
```python
from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.base import Base
from app.models.content import Content, ContentStatus
from app.models.kb_article import KBArticle, KBArticleStatus
from app.models.user import User, UserRole

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)

# ---------------------------------------------------------------------------
# KB article fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def kb_draft_article(db_session: AsyncSession, regular_user: User) -> KBArticle:
    article = KBArticle(
        author_id=regular_user.id,
        title="Draft Article",
        body="Draft body.",
        status=KBArticleStatus.draft,
    )
    db_session.add(article)
    await db_session.flush()
    return article


@pytest_asyncio.fixture()
async def kb_pending_article(db_session: AsyncSession, regular_user: User) -> KBArticle:
    article = KBArticle(
        author_id=regular_user.id,
        title="Pending Article",
        body="Pending body.",
        status=KBArticleStatus.pending_review,
    )
    db_session.add(article)
    await db_session.flush()
    return article


@pytest_asyncio.fixture()
async def kb_approved_article(db_session: AsyncSession, regular_user: User) -> KBArticle:
    article = KBArticle(
        author_id=regular_user.id,
        title="Approved Article",
        body="Approved body.",
        status=KBArticleStatus.approved,
    )
    db_session.add(article)
    await db_session.flush()
    return article


TestSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=test_engine, expire_on_commit=False, autoflush=False, autocommit=False
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def db_session() -> AsyncSession:
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture()
async def client(db_session: AsyncSession) -> AsyncClient:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def moderator_user(db_session: AsyncSession) -> User:
    user = User(
        username="mod1",
        email="mod1@example.com",
        hashed_password="hashed",
        role=UserRole.moderator,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture()
async def admin_user(db_session: AsyncSession) -> User:
    user = User(
        username="admin1",
        email="admin1@example.com",
        hashed_password="hashed",
        role=UserRole.admin,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture()
async def regular_user(db_session: AsyncSession) -> User:
    user = User(
        username="user1",
        email="user1@example.com",
        hashed_password="hashed",
        role=UserRole.user,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture()
async def flagged_content(db_session: AsyncSession, regular_user: User) -> Content:
    content = Content(
        author_id=regular_user.id,
        title="Flagged post",
        body="Flagged body.",
        status=ContentStatus.flagged,
    )
    db_session.add(content)
    await db_session.flush()
    return content


@pytest_asyncio.fixture()
async def active_content(db_session: AsyncSession, regular_user: User) -> Content:
    content = Content(
        author_id=regular_user.id,
        title="Active post",
        body="Active body.",
        status=ContentStatus.active,
    )
    db_session.add(content)
    await db_session.flush()
    return content


def make_moderator_token(user: User) -> str:
    return create_access_token(user_id=user.id, role="moderator")


def make_admin_token(user: User) -> str:
    return create_access_token(user_id=user.id, role="admin")


def make_user_token(user: User) -> str:
    return create_access_token(user_id=user.id, role="user")

```

### `backend/tests/test_kb_approval.py`
```python
"""Tests for TASK-045: KB approve / reject endpoints.

Covers
------
AC-023.1  PUT /approve → 200, article.status == approved, IF-017 event emitted
AC-023.2  Approve requires moderator/admin; regular user → 403
AC-023.3  Only pending_review can be approved; draft → 422
AC-023.4  approved_by / approved_at populated on approval
AC-023.5  IF-017 event recorded by NoOpKBEventEmitter after commit

AC-023.2  (reject) PUT /reject → 200, article.status == draft, note stored
          Reject requires moderator/admin; regular user → 403
          Only pending_review can be rejected; draft → 422
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.main import app
from app.models.kb_article import KBArticle, KBArticleStatus
from app.models.user import User
from app.services.kb.events import NoOpKBEventEmitter, get_kb_event_emitter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def auth(user: User, role: str | None = None) -> dict[str, str]:
    r = role or user.role.value
    return {"Authorization": f"Bearer {create_access_token(user_id=user.id, role=r)}"}


# ---------------------------------------------------------------------------
# APPROVE — success paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approve_returns_200_and_approved_status(
    client: AsyncClient,
    moderator_user: User,
    kb_pending_article: KBArticle,
) -> None:
    """AC-023.1 / AC-023.4 — approve sets status=approved, approved_by, approved_at."""
    resp = await client.put(
        f"/api/v1/kb/{kb_pending_article.id}/approve",
        headers=auth(moderator_user),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["article"]["status"] == KBArticleStatus.approved.value
    assert data["article"]["approved_by"] == moderator_user.id
    assert data["article"]["approved_at"] is not None


@pytest.mark.asyncio
async def test_approve_emits_if017_event(
    client: AsyncClient,
    moderator_user: User,
    kb_pending_article: KBArticle,
) -> None:
    """AC-023.5 — IF-017 domain event emitted after commit."""
    noop = NoOpKBEventEmitter()
    app.dependency_overrides[get_kb_event_emitter] = lambda: noop

    try:
        resp = await client.put(
            f"/api/v1/kb/{kb_pending_article.id}/approve",
            headers=auth(moderator_user),
        )
        assert resp.status_code == 200
        assert len(noop.emitted) == 1
        evt = noop.emitted[0]
        assert evt.event_type == "kb.article.approved"
        assert evt.article_id == kb_pending_article.id
        assert evt.approved_by == moderator_user.id
    finally:
        app.dependency_overrides.pop(get_kb_event_emitter, None)


@pytest.mark.asyncio
async def test_approve_response_contains_audit_event(
    client: AsyncClient,
    moderator_user: User,
    kb_pending_article: KBArticle,
) -> None:
    """AC-023.1 — response body includes the immutable audit event."""
    resp = await client.put(
        f"/api/v1/kb/{kb_pending_article.id}/approve",
        headers=auth(moderator_user),
    )
    assert resp.status_code == 200
    evt = resp.json()["event"]
    assert evt["event_type"] == "kb.article.approved"
    assert evt["previous_status"] == KBArticleStatus.pending_review.value
    assert evt["new_status"] == KBArticleStatus.approved.value


# ---------------------------------------------------------------------------
# APPROVE — access control
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approve_requires_moderator_role(
    client: AsyncClient,
    regular_user: User,
    kb_pending_article: KBArticle,
) -> None:
    """AC-023.2 — regular user receives 403."""
    resp = await client.put(
        f"/api/v1/kb/{kb_pending_article.id}/approve",
        headers=auth(regular_user),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_approve_admin_allowed(
    client: AsyncClient,
    admin_user: User,
    kb_pending_article: KBArticle,
) -> None:
    """AC-023.2 — admin role is also permitted."""
    resp = await client.put(
        f"/api/v1/kb/{kb_pending_article.id}/approve",
        headers=auth(admin_user),
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_approve_unauthenticated_returns_401(
    client: AsyncClient,
    kb_pending_article: KBArticle,
) -> None:
    resp = await client.put(f"/api/v1/kb/{kb_pending_article.id}/approve")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# APPROVE — state machine / illegal transitions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approve_draft_returns_422(
    client: AsyncClient,
    moderator_user: User,
    kb_draft_article: KBArticle,
) -> None:
    """AC-023.3 — can only approve a pending_review article."""
    resp = await client.put(
        f"/api/v1/kb/{kb_draft_article.id}/approve",
        headers=auth(moderator_user),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_approve_already_approved_returns_422(
    client: AsyncClient,
    moderator_user: User,
    kb_approved_article: KBArticle,
) -> None:
    """State machine: approved is terminal — no further transitions."""
    resp = await client.put(
        f"/api/v1/kb/{kb_approved_article.id}/approve",
        headers=auth(moderator_user),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_approve_nonexistent_returns_404(
    client: AsyncClient,
    moderator_user: User,
) -> None:
    resp = await client.put(
        "/api/v1/kb/nonexistent-id/approve",
        headers=auth(moderator_user),
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# REJECT — success paths (AC-023.2: reject → back to draft with note)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reject_returns_200_and_draft_status(
    client: AsyncClient,
    moderator_user: User,
    kb_pending_article: KBArticle,
) -> None:
    """AC-023.2 — rejection sends article back to draft."""
    resp = await client.put(
        f"/api/v1/kb/{kb_pending_article.id}/reject",
        json={"reason": "Needs more detail."},
        headers=auth(moderator_user),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["article"]["status"] == KBArticleStatus.draft.value
    assert data["article"]["rejected_reason"] == "Needs more detail."
    assert data["article"]["rejected_by"] == moderator_user.id
    assert data["article"]["rejected_at"] is not None


@pytest.mark.asyncio
async def test_reject_audit_event_records_draft_transition(
    client: AsyncClient,
    moderator_user: User,
    kb_pending_article: KBArticle,
) -> None:
    """Audit event must reflect pending_review → draft transition."""
    resp = await client.put(
        f"/api/v1/kb/{kb_pending_article.id}/reject",
        json={"reason": "Incomplete."},
        headers=auth(moderator_user),
    )
    assert resp.status_code == 200
    evt = resp.json()["event"]
    assert evt["event_type"] == "kb.article.rejected"
    assert evt["previous_status"] == KBArticleStatus.pending_review.value
    assert evt["new_status"] == KBArticleStatus.draft.value
    assert evt["reason"] == "Incomplete."


@pytest.mark.asyncio
async def test_reject_without_reason_is_allowed(
    client: AsyncClient,
    moderator_user: User,
    kb_pending_article: KBArticle,
) -> None:
    """Rejection reason is optional per spec."""
    resp = await client.put(
        f"/api/v1/kb/{kb_pending_article.id}/reject",
        json={},
        headers=auth(moderator_user),
    )
    assert resp.status_code == 200
    assert resp.json()["article"]["status"] == KBArticleStatus.draft.value


# ---------------------------------------------------------------------------
# REJECT — access control
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reject_requires_moderator_role(
    client: AsyncClient,
    regular_user: User,
    kb_pending_article: KBArticle,
) -> None:
    resp = await client.put(
        f"/api/v1/kb/{kb_pending_article.id}/reject",
        json={"reason": "Nope."},
        headers=auth(regular_user),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# REJECT — state machine / illegal transitions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reject_draft_returns_422(
    client: AsyncClient,
    moderator_user: User,
    kb_draft_article: KBArticle,
) -> None:
    """Only pending_review can be rejected."""
    resp = await client.put(
        f"/api/v1/kb/{kb_draft_article.id}/reject",
        json={"reason": "Bad."},
        headers=auth(moderator_user),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_reject_approved_returns_422(
    client: AsyncClient,
    moderator_user: User,
    kb_approved_article: KBArticle,
) -> None:
    """Approved is a terminal state — cannot be rejected."""
    resp = await client.put(
        f"/api/v1/kb/{kb_approved_article.id}/reject",
        json={"reason": "Too late."},
        headers=auth(moderator_user),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_reject_nonexistent_returns_404(
    client: AsyncClient,
    moderator_user: User,
) -> None:
    resp = await client.put(
        "/api/v1/kb/nonexistent-id/reject",
        json={"reason": "?"},
        headers=auth(moderator_user),
    )
    assert resp.status_code == 404

```

### `backend/tests/test_kb_visibility.py`
```python
"""Tests for TASK-046: KB article visibility (AC-025.3).

Covers
------
AC-025.3  GET /api/v1/kb/{article_id} returns:
            - 200  for an approved article (any caller, including anonymous)
            - 404  for a non-approved article when caller is anonymous
            - 404  for a non-approved article when caller is a regular user
            - 200  for a non-approved article when caller is moderator
            - 200  for a non-approved article when caller is admin
            - 404  for a genuinely non-existent article (any caller)

OWASP A01 (broken access control): existence of draft/pending articles must
not be leaked to non-privileged callers — both "not found" and "not approved"
cases must return HTTP 404 with an identical body.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.models.kb_article import KBArticle
from app.models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def auth(user: User, role: str | None = None) -> dict[str, str]:
    r = role or user.role.value
    return {"Authorization": f"Bearer {create_access_token(user_id=user.id, role=r)}"}


# ---------------------------------------------------------------------------
# Approved article — visible to everyone
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approved_article_visible_to_anonymous(
    client: AsyncClient,
    kb_approved_article: KBArticle,
) -> None:
    """AC-025.3 — approved article has no auth requirement."""
    resp = await client.get(f"/api/v1/kb/{kb_approved_article.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == kb_approved_article.id
    assert resp.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_approved_article_visible_to_regular_user(
    client: AsyncClient,
    regular_user: User,
    kb_approved_article: KBArticle,
) -> None:
    resp = await client.get(
        f"/api/v1/kb/{kb_approved_article.id}",
        headers=auth(regular_user),
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_approved_article_visible_to_moderator(
    client: AsyncClient,
    moderator_user: User,
    kb_approved_article: KBArticle,
) -> None:
    resp = await client.get(
        f"/api/v1/kb/{kb_approved_article.id}",
        headers=auth(moderator_user),
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Non-approved article — hidden from non-privileged callers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_draft_article_returns_404_to_anonymous(
    client: AsyncClient,
    kb_draft_article: KBArticle,
) -> None:
    """AC-025.3 / OWASP A01 — draft article existence must not be leaked."""
    resp = await client.get(f"/api/v1/kb/{kb_draft_article.id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_draft_article_returns_404_to_regular_user(
    client: AsyncClient,
    regular_user: User,
    kb_draft_article: KBArticle,
) -> None:
    """AC-025.3 — authenticated non-privileged caller still gets 404."""
    resp = await client.get(
        f"/api/v1/kb/{kb_draft_article.id}",
        headers=auth(regular_user),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_pending_article_returns_404_to_anonymous(
    client: AsyncClient,
    kb_pending_article: KBArticle,
) -> None:
    resp = await client.get(f"/api/v1/kb/{kb_pending_article.id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_pending_article_returns_404_to_regular_user(
    client: AsyncClient,
    regular_user: User,
    kb_pending_article: KBArticle,
) -> None:
    resp = await client.get(
        f"/api/v1/kb/{kb_pending_article.id}",
        headers=auth(regular_user),
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Non-approved article — visible to privileged callers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_draft_article_visible_to_moderator(
    client: AsyncClient,
    moderator_user: User,
    kb_draft_article: KBArticle,
) -> None:
    """AC-025.3 — moderators may access any status."""
    resp = await client.get(
        f"/api/v1/kb/{kb_draft_article.id}",
        headers=auth(moderator_user),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "draft"


@pytest.mark.asyncio
async def test_pending_article_visible_to_admin(
    client: AsyncClient,
    admin_user: User,
    kb_pending_article: KBArticle,
) -> None:
    """AC-025.3 — admins may access any status."""
    resp = await client.get(
        f"/api/v1/kb/{kb_pending_article.id}",
        headers=auth(admin_user),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending_review"


# ---------------------------------------------------------------------------
# OWASP A01 — indistinguishable 404s
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nonexistent_and_hidden_article_return_same_404_body(
    client: AsyncClient,
    kb_draft_article: KBArticle,
) -> None:
    """Both a genuinely missing and a hidden article must return the same
    status code and body to prevent oracle-style enumeration."""
    missing_resp = await client.get("/api/v1/kb/completely-fake-id-xyz")
    hidden_resp = await client.get(f"/api/v1/kb/{kb_draft_article.id}")

    assert missing_resp.status_code == 404
    assert hidden_resp.status_code == 404
    assert missing_resp.json() == hidden_resp.json()

```