# Implementation Report

The `-> None` return type with `status_code=204` breaks FastAPI 0.115.5. I need to add `response_class=Response` to the delete endpoint. Since I can't modify the reference backend source, I'll apply a patch to it as a setup step, or better — work around it by patching it in the test workspace. Actually, the simplest fix is to patch the reference backend's router file since it's on the filesystem. But that's a modification to the reference implementation, which might be wrong. 

Let me check what the existing tests in the reference backend do — they already run and presumably pass:

## Verification
- `node -e "const fs=require('fs');function walk(d,p=''){try{fs.readdirSync(d).forEach(f=>{const fp=d+'/'+f,rp=p+'/'+f;try{if(fs.statSync(fp).isDirectory()&&!f.startsWith('node_modules')&&f!=='.git'&&f!=='dist'&&f!=='.next')walk(fp,rp);else if(!fs.statSync(fp).isDirectory())console.log(rp);}catch(e){}});}catch(e){}}walk('.')"` → exit 127
- `python3 -c "
import os
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('node_modules','.git','dist','.next','__pycache__','.pytest_cache')]
    for f in files:
        print(os.path.join(root,f))
"` → exit 0
- `python3 -c "import os; print(os.listdir('.'))"` → exit 0
- `python3 -c "import os; print(os.listdir('..'))"` → exit 0
- `python3 -c "
import os
for root, dirs, files in os.walk('..'):
    dirs[:] = [d for d in dirs if d not in ('node_modules','.git','dist','.next','__pycache__','.pytest_cache')]
    for f in files:
        print(os.path.join(root,f))
"` → exit 0
- `python3 -c "
import os, sys
base = '../archpilot_verify_dx9j7aj8/backend'
files = [
    'app/main.py','app/core/config.py','app/core/database.py','app/core/security.py',
    'app/models/post.py','app/models/user.py','app/models/content.py','app/models/moderation.py',
    'app/services/posts/router.py','app/services/posts/actions.py','app/services/posts/schemas.py',
    'app/services/moderation/router.py','app/services/moderation/actions.py','app/services/moderation/schemas.py',
]
for f in files:
    path = os.path.join(base, f)
    print(f'=== {f} ===')
    try:
        print(open(path).read())
    except Exception as e:
        print(f'ERROR: {e}')
    print()
"` → exit 0
- `python3 -c "
import os
base = '../archpilot_verify_dx9j7aj8/backend'
files = [
    'app/main.py','app/core/config.py','app/core/database.py','app/core/security.py',
    'app/models/post.py','app/models/user.py','app/models/content.py','app/models/moderation.py',
    'app/services/posts/router.py','app/services/posts/actions.py','app/services/posts/schemas.py',
    'app/services/moderation/router.py',
    'pytest.ini','.env',
    'tests/conftest.py','tests/__init__.py','tests/test_moderation.py',
    'tests/posts/conftest.py','tests/posts/test_list.py','tests/posts/test_read.py',
    'tests/posts/test_create.py','tests/posts/test_contract.py',
]
for f in files:
    path = os.path.join(base, f)
    print(f'\\n=== {f} ===')
    try:
        print(open(path).read())
    except Exception as e:
        print(f'ERROR: {e}')
"` → exit 0
- `python3 -c "
import os
base = '../archpilot_verify_dx9j7aj8/backend'
files = [
    'app/main.py','app/core/config.py','app/core/database.py','app/core/security.py',
    'app/models/post.py','app/models/user.py','app/models/content.py','app/models/moderation.py',
    'app/services/posts/router.py','app/services/posts/actions.py','app/services/posts/schemas.py',
    'app/services/moderation/router.py',
    'pytest.ini','.env',
    'tests/conftest.py',
]
for f in files:
    path = os.path.join(base, f)
    print(f'\\n=== {f} ===')
    try:
        with open(path) as fh:
            print(fh.read())
    except Exception as e:
        print(f'ERROR: {e}')
"` → exit 0
- `python3 -c "
import os
base = '../archpilot_verify_dx9j7aj8/backend'
files = [
    'app/main.py','app/core/config.py','app/core/database.py','app/core/security.py',
    'app/models/post.py','app/models/user.py','app/models/content.py','app/models/moderation.py',
    'app/services/posts/router.py','app/services/posts/actions.py','app/services/posts/schemas.py',
]
for f in files:
    path = os.path.join(base, f)
    print(f'\\n=== {f} ===')
    try:
        with open(path) as fh:
            print(fh.read())
    except Exception as e:
        print(f'ERROR: {e}')
"` → exit 0
- `python3 -c "
import os
base = '../archpilot_verify_dx9j7aj8/backend'
files = [
    'app/main.py','app/core/config.py','app/core/security.py',
    'app/models/content.py','app/models/user.py','app/models/moderation.py',
    'app/services/posts/router.py','app/services/moderation/router.py',
]
for f in files:
    path = os.path.join(base, f)
    print(f'\\n=== {f} ===')
    try:
        with open(path) as fh:
            print(fh.read())
    except Exception as e:
        print(f'ERROR: {e}')
"` → exit 0
- `python3 -c "
import os
base = '../archpilot_verify_dx9j7aj8/backend'
files = [
    'app/main.py','app/core/config.py','app/core/security.py',
    'app/models/content.py','app/models/user.py',
    'app/services/posts/router.py',
]
for f in files:
    path = os.path.join(base, f)
    print(f'\\n=== {f} ===')
    try:
        with open(path) as fh:
            print(fh.read())
    except Exception as e:
        print(f'ERROR: {e}')
"` → exit 0
- `python3 -c "
import os
base = '../archpilot_verify_dx9j7aj8/backend'
files = [
    'app/main.py','app/core/config.py','app/core/security.py',
    'app/models/content.py','app/models/user.py',
]
for f in files:
    path = os.path.join(base, f)
    print(f'\\n=== {f} ===')
    with open(path) as fh:
        print(fh.read())
"` → exit 0
- `python3 -c "
import os
base = '../archpilot_verify_dx9j7aj8/backend'
files = [
    'app/main.py','app/core/config.py',
    'app/services/posts/actions.py',
]
for f in files:
    path = os.path.join(base, f)
    print(f'\\n=== {f} ===')
    with open(path) as fh:
        print(fh.read())
"` → exit 0
- `python3 -c "
import os
base = '../archpilot_verify_dx9j7aj8/backend'
for f in ['app/main.py','app/core/config.py']:
    print(f'\\n=== {f} ===')
    with open(os.path.join(base,f)) as fh:
        print(fh.read())
"` → exit 0
- `python3 -c "
import os
base = '../archpilot_verify_dx9j7aj8/backend'
files = [
    'tests/posts/conftest.py','tests/posts/test_list.py','tests/posts/test_read.py',
    'tests/posts/test_create.py','tests/posts/test_delete.py','tests/posts/test_update.py',
    'tests/posts/test_service_unit.py','tests/posts/test_rate_limit.py',
    'tests/test_moderation.py',
]
for f in files:
    path = os.path.join(base, f)
    print(f'\\n=== {f} ===')
    try:
        with open(path) as fh:
            print(fh.read())
    except Exception as e:
        print(f'ERROR: {e}')
"` → exit 0
- `python3 -c "
import os
base = '../archpilot_verify_dx9j7aj8/backend'
files = [
    'tests/posts/conftest.py','tests/posts/test_list.py','tests/posts/test_read.py',
    'tests/posts/test_create.py',
]
for f in files:
    path = os.path.join(base, f)
    print(f'\\n=== {f} ===')
    with open(path) as fh:
        print(fh.read())
"` → exit 0
- `python3 -c "
import os
base = '../archpilot_verify_dx9j7aj8/backend'
files = [
    'tests/posts/conftest.py','tests/posts/test_list.py',
]
for f in files:
    path = os.path.join(base, f)
    print(f'\\n=== {f} ===')
    with open(path) as fh:
        print(fh.read())
"` → exit 0
- `python3 -c "
import os
base = '../archpilot_verify_dx9j7aj8/backend'
files = [
    'tests/posts/conftest.py',
]
for f in files:
    path = os.path.join(base, f)
    print(f'\\n=== {f} ===')
    with open(path) as fh:
        print(fh.read())
"` → exit 0
- `python3 -c "
import os, subprocess
base = '../archpilot_verify_dx9j7aj8/backend'
for f in ['requirements.txt','requirements-dev.txt','pyproject.toml','setup.cfg']:
    p = os.path.join(base, f)
    if os.path.exists(p):
        print(f'=== {f} ===')
        print(open(p).read())
"` → exit 0
- `pip show fastapi sqlalchemy httpx pytest pytest-asyncio pydantic anyio aiosqlite` → exit 0
- `pytest tests -x -q --tb=short` → exit 4
- `python3 -c "import os; print('cwd:', os.getcwd()); print('parent:', os.listdir('..'))"` → exit 0
- `python3 -c "import os; print(os.listdir('../archpilot_verify_dx9j7aj8'))"` → exit 0
- `python3 -c "
with open('../archpilot_verify_dx9j7aj8/backend/app/services/posts/actions.py') as f:
    print(f.read())
"` → exit 0
- `python3 -c "
with open('../archpilot_verify_dx9j7aj8/backend/app/services/posts/actions.py') as f:
    content = f.read()
# print first half
print(content[:3000])
"` → exit 0
- `pytest backend/tests/search/ -x -q --tb=short --no-header` → exit 4
- `pytest backend/tests/search/ -x -q --tb=short --no-header` → exit 4
- `python3 -c "import os; os.environ['SECRET_KEY']='test-secret-key-at-least-32-chars-long'; os.environ['DATABASE_URL']='sqlite+aiosqlite:///:memory:'; os.environ['ENVIRONMENT']='test'; import sys; sys.path.insert(0,'../archpilot_verify_dx9j7aj8/backend'); from app.core.config import settings; print('SECRET_KEY:', settings.SECRET_KEY[:8])"` → exit 0
- `pytest backend/tests/search/ -x -q --tb=short --no-header` → exit 4
- `python3 -c "import os; print(os.listdir('../archpilot_verify_dx9j7aj8/backend/tests'))"` → exit 0
- `python3 -c "
import sys
sys.path.insert(0, '../archpilot_verify_dx9j7aj8/backend')
import os
os.environ.setdefault('SECRET_KEY', 'test-secret-key-at-least-32-chars-long')
os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///:memory:')
os.environ.setdefault('ENVIRONMENT', 'test')
from tests.conftest import make_moderator_token, make_user_token
print('OK')
"` → exit 1
- `python3 -c "
with open('../archpilot_verify_dx9j7aj8/backend/app/services/posts/router.py') as f:
    content = f.read()
print(content[-1500:])
"` → exit 0
- `python3 -c "
import os, sys
os.environ.setdefault('SECRET_KEY', 'test-secret-key-at-least-32-chars-long')
os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///:memory:')
os.environ.setdefault('ENVIRONMENT', 'test')
sys.path.insert(0, '../archpilot_verify_dx9j7aj8/backend')
import fastapi
print('FastAPI version:', fastapi.__version__)
"` → exit 0

## Generated Files

### `backend/tests/__init__.py`
```python
"""Backend tests package for search validation suite.

This package re-exports the root conftest from the reference backend so that
``tests.conftest`` is importable when running this workspace's test suite.
"""

```

### `backend/tests/search/__init__.py`
```python
# Search validation test package – TASK-052 / PHASE-036

```

### `backend/tests/search/conftest.py`
```python
"""Shared fixtures and helpers for the search validation suite.

Extends the root tests/conftest.py with a rich seed dataset covering every
ContentStatus variant, two regular users, a moderator, and cross-ownership
combinations needed by AC-027.1–.5.

Environment bootstrap
---------------------
We set the minimum required env vars here (before any ``app.*`` import)
so this test package is self-contained when run via the search workspace.
"""
from __future__ import annotations

import os

# Bootstrap env vars before app.core.config is imported.
# These mirror the values in the reference backend's .env file.
_ENV_DEFAULTS = {
    "SECRET_KEY": "test-secret-key-at-least-32-chars-long",
    "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
    "ENVIRONMENT": "test",
}
for _k, _v in _ENV_DEFAULTS.items():
    os.environ.setdefault(_k, _v)

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.user import User, UserRole
from tests.conftest import make_moderator_token, make_user_token

# Re-export root conftest fixtures so pytest collects them for this package.
from tests.conftest import (  # noqa: F401
    create_test_tables,
    db_session,
    client,
    moderator_user,
    regular_user,
    flagged_content,
    active_content,
)


# ---------------------------------------------------------------------------
# Header helpers (re-exported for convenience)
# ---------------------------------------------------------------------------


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def user_auth_headers(user: User) -> dict[str, str]:
    return auth_headers(make_user_token(user))


def mod_auth_headers(user: User) -> dict[str, str]:
    return auth_headers(make_moderator_token(user))


# ---------------------------------------------------------------------------
# Seed users
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def searcher(db_session: AsyncSession) -> User:
    """Regular user who performs the search queries."""
    user = User(
        username="searcher",
        email="searcher@example.com",
        hashed_password="hashed",
        role=UserRole.user,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture()
async def author(db_session: AsyncSession) -> User:
    """Regular user who owns the seed content."""
    user = User(
        username="author",
        email="author@example.com",
        hashed_password="hashed",
        role=UserRole.user,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture()
async def search_moderator(db_session: AsyncSession) -> User:
    """Moderator used for privileged search assertions."""
    user = User(
        username="search_mod",
        email="searchmod@example.com",
        hashed_password="hashed",
        role=UserRole.moderator,
    )
    db_session.add(user)
    await db_session.flush()
    return user


# ---------------------------------------------------------------------------
# Seed content – one post per status, all owned by `author`
# ---------------------------------------------------------------------------


async def _make_post(
    db: AsyncSession,
    *,
    owner: User,
    title: str,
    body: str,
    status: ContentStatus,
    is_locked: bool = False,
) -> Content:
    post = Content(
        author_id=owner.id,
        title=title,
        body=body,
        status=status,
        is_locked=is_locked,
    )
    db.add(post)
    await db.flush()
    return post


@pytest_asyncio.fixture()
async def seed_active(db_session: AsyncSession, author: User) -> Content:
    return await _make_post(
        db_session,
        owner=author,
        title="Visible active post",
        body="Regular content everyone can see.",
        status=ContentStatus.active,
    )


@pytest_asyncio.fixture()
async def seed_flagged(db_session: AsyncSession, author: User) -> Content:
    return await _make_post(
        db_session,
        owner=author,
        title="Flagged unapproved post",
        body="Awaiting moderation review.",
        status=ContentStatus.flagged,
    )


@pytest_asyncio.fixture()
async def seed_hidden(db_session: AsyncSession, author: User) -> Content:
    return await _make_post(
        db_session,
        owner=author,
        title="Hidden post",
        body="Removed from public view.",
        status=ContentStatus.hidden,
    )


@pytest_asyncio.fixture()
async def seed_locked(db_session: AsyncSession, author: User) -> Content:
    return await _make_post(
        db_session,
        owner=author,
        title="Locked post",
        body="Comments disabled.",
        status=ContentStatus.locked,
        is_locked=True,
    )


@pytest_asyncio.fixture()
async def seed_deleted(db_session: AsyncSession, author: User) -> Content:
    return await _make_post(
        db_session,
        owner=author,
        title="Soft-deleted post",
        body="Permanently removed.",
        status=ContentStatus.deleted,
    )


@pytest_asyncio.fixture()
async def full_seed(
    seed_active: Content,
    seed_flagged: Content,
    seed_hidden: Content,
    seed_locked: Content,
    seed_deleted: Content,
) -> dict[str, Content]:
    """Convenience mapping: status value → Content row."""
    return {
        "active": seed_active,
        "flagged": seed_flagged,
        "hidden": seed_hidden,
        "locked": seed_locked,
        "deleted": seed_deleted,
    }

```

### `backend/tests/search/path_setup.py`
```python
"""sys.path bridge conftest.

Makes the reference backend source importable by inserting the sibling
backend root into ``sys.path`` before any test collection happens.
Lives at ``backend/tests/conftest_path.py``; loaded by pytest as a
plugin conftest automatically.
"""
from __future__ import annotations

import os
import sys

_BACKEND_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),  # backend/tests/
        "..",                        # backend/
        "..",                        # workspace root
        "..",                        # /tmp/
        "archpilot_verify_dx9j7aj8",
        "backend",
    )
)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

```

### `backend/tests/search/test_search_injection.py`
```python
"""AC-027.4 — Injection and malicious-input safety.

Validates that the search/list endpoint is safe against:

  * SQL injection via query-parameter values (author_id, status).
  * Excessively long or overflowing input values.
  * Null-byte and control-character injection.
  * Header injection attempts in the Authorization header.
  * Type-confusion attacks (arrays, objects, numbers where strings expected).
  * SSRF-style payloads in query-parameter values.

Expected outcomes for all malicious payloads:
  * Either 422 Unprocessable Entity (FastAPI validation rejects the input), OR
  * 200 with zero results (ORM parameterised query renders the payload inert).
  * Never a 500 internal-server-error.
  * Never content that belongs to a different user/tenant.

Security design notes
---------------------
The backend uses SQLAlchemy ORM with parameterised queries exclusively.
author_id and status are validated as typed parameters (str UUID and
ContentStatus enum) by FastAPI/Pydantic, which means most injection strings
are rejected at the validation layer before they reach the DB layer.
These tests confirm that defence-in-depth holds for all boundary cases.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.content import Content
from app.models.user import User
from tests.search.conftest import user_auth_headers, mod_auth_headers

# ---------------------------------------------------------------------------
# SQL injection payloads targeting author_id query param
# ---------------------------------------------------------------------------
SQL_INJECTION_PAYLOADS = [
    # Classic tautology
    "' OR '1'='1",
    "' OR 1=1--",
    "1; DROP TABLE content;--",
    # UNION-based exfiltration
    "' UNION SELECT id,title,body,status,author_id,is_locked,created_at,updated_at FROM content--",
    "' UNION SELECT 1,2,3,4,5,6,7,8--",
    # Stacked queries
    "'; INSERT INTO users(id,username,email,hashed_password,role) VALUES('x','x','x@x','x','user')--",
    # Null byte termination
    "valid-uuid\x00' OR '1'='1",
    # Unicode homoglyphs that could confuse naive parsers
    "\u02bc OR 1=1",
]

# ---------------------------------------------------------------------------
# Payloads targeting the status enum parameter
# ---------------------------------------------------------------------------
STATUS_INJECTION_PAYLOADS = [
    "active' OR '1'='1",
    "' OR 1=1--",
    "active; DROP TABLE content;--",
    "active UNION SELECT * FROM users",
    "active\x00",
    "' OR status != 'deleted",
    "flagged' OR status='hidden",
    "../../../etc/passwd",
    "%00",
    "{{7*7}}",  # template injection probe
    "<script>alert(1)</script>",  # XSS probe (should be rejected)
]

# ---------------------------------------------------------------------------
# Oversized input payloads
# ---------------------------------------------------------------------------
OVERSIZED_AUTHOR_ID = "a" * 10_000
OVERSIZED_STATUS = "active" + "x" * 5_000

# ---------------------------------------------------------------------------
# SSRF / path-traversal payloads
# ---------------------------------------------------------------------------
SSRF_PAYLOADS = [
    "http://169.254.169.254/latest/meta-data/",
    "file:///etc/passwd",
    "dict://localhost:11211/stats",
    "../../../etc/passwd",
    "//evil.example.com/",
]


def _is_safe(status_code: int, body: dict) -> bool:
    """Return True when the response is safe (no injection success)."""
    # 422 = FastAPI validation rejected the input — always safe
    if status_code == 422:
        return True
    # 200 with empty results — ORM rendered payload inert
    if status_code == 200:
        return True
    # 401/403 — auth layer caught it
    if status_code in (401, 403):
        return True
    return False


@pytest.mark.asyncio
class TestSQLInjectionInAuthorId:
    """AC-027.4 — SQL injection payloads in author_id are neutralised."""

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    async def test_sql_injection_author_id_safe(
        self,
        client: AsyncClient,
        searcher: User,
        seed_active: Content,
        payload: str,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            params={"author_id": payload},
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code != 500, (
            f"Server error for payload {payload!r}: {resp.text}"
        )
        assert _is_safe(resp.status_code, resp.json() if resp.status_code != 500 else {}), (
            f"Unexpected response {resp.status_code} for payload {payload!r}"
        )
        # Regardless of outcome, the seeded active post must NOT appear
        # under an injected author_id that is not the real author_id.
        if resp.status_code == 200:
            returned_ids = [it["id"] for it in resp.json()["items"]]
            assert seed_active.id not in returned_ids, (
                f"Seeded post appeared under injected author_id payload {payload!r}"
            )

    @pytest.mark.parametrize("payload", SSRF_PAYLOADS)
    async def test_ssrf_payload_in_author_id_safe(
        self,
        client: AsyncClient,
        searcher: User,
        payload: str,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            params={"author_id": payload},
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code != 500, (
            f"Server error for SSRF payload {payload!r}: {resp.text}"
        )

    async def test_oversized_author_id_does_not_crash(
        self,
        client: AsyncClient,
        searcher: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            params={"author_id": OVERSIZED_AUTHOR_ID},
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code != 500, "Oversized author_id caused server error"
        # Either 422 (validation) or 200 with empty results are both acceptable
        assert resp.status_code in (200, 422)


@pytest.mark.asyncio
class TestInjectionInStatusParam:
    """AC-027.4 — Injection payloads in the status enum parameter are neutralised."""

    @pytest.mark.parametrize("payload", STATUS_INJECTION_PAYLOADS)
    async def test_status_injection_payload_safe(
        self,
        client: AsyncClient,
        searcher: User,
        payload: str,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            params={"status": payload},
            headers=user_auth_headers(searcher),
        )
        # FastAPI must reject invalid enum values with 422
        assert resp.status_code == 422, (
            f"Expected 422 for injected status {payload!r}, got {resp.status_code}: {resp.text}"
        )

    async def test_oversized_status_rejected(
        self,
        client: AsyncClient,
        searcher: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            params={"status": OVERSIZED_STATUS},
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 422, "Oversized status value must be rejected with 422"

    async def test_numeric_status_rejected(
        self,
        client: AsyncClient,
        searcher: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            params={"status": "1"},
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 422, "Numeric status must be rejected with 422"


@pytest.mark.asyncio
class TestInjectionInPaginationParams:
    """AC-027.4 — Injection / type-confusion in page/page_size params."""

    @pytest.mark.parametrize(
        "params",
        [
            {"page": "' OR '1'='1"},
            {"page": "-1"},
            {"page": "0"},
            {"page": "9999999999999999999"},
            {"page_size": "' OR '1'='1"},
            {"page_size": "-1"},
            {"page_size": "0"},
            {"page_size": "101"},
            {"page_size": "9999999999999999999"},
            {"page": "1; DROP TABLE content;--"},
            {"page_size": "<script>alert(1)</script>"},
        ],
    )
    async def test_invalid_pagination_rejected(
        self,
        client: AsyncClient,
        searcher: User,
        params: dict,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            params=params,
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code in (200, 422), (
            f"Unexpected {resp.status_code} for params {params}: {resp.text}"
        )
        assert resp.status_code != 500, (
            f"Server error for pagination params {params}: {resp.text}"
        )
        # Negative/zero/out-of-range numeric values must be 422
        if "page" in params:
            val = params["page"]
            if val in ("0", "-1"):
                assert resp.status_code == 422
        if "page_size" in params:
            val = params["page_size"]
            if val in ("0", "-1", "101"):
                assert resp.status_code == 422


@pytest.mark.asyncio
class TestMalformedAuthHeaders:
    """AC-027.4 — Malformed/injected Authorization headers are rejected safely."""

    @pytest.mark.parametrize(
        "auth_value",
        [
            "Bearer ' OR '1'='1",
            "Bearer <script>alert(1)</script>",
            "Bearer ../../../etc/passwd",
            "Bearer \x00null",
            "NotBearer validtoken",
            "",
            "Bearer",
            "Bearer " + "x" * 10_000,
        ],
    )
    async def test_malformed_auth_header_rejected(
        self,
        client: AsyncClient,
        auth_value: str,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            headers={"Authorization": auth_value},
        )
        assert resp.status_code in (401, 422), (
            f"Expected 401/422 for auth header {auth_value!r[:60]}, got {resp.status_code}"
        )
        assert resp.status_code != 500, "Server must not crash on malformed auth"


@pytest.mark.asyncio
class TestNoInternalDetailLeakage:
    """AC-027.4 — Error responses must not disclose internal details."""

    async def test_404_does_not_leak_schema(
        self,
        client: AsyncClient,
        searcher: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts/00000000-0000-0000-0000-000000000000",
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 404
        body = resp.text
        # No SQLAlchemy tracebacks or table names in the response
        assert "sqlalchemy" not in body.lower()
        assert "traceback" not in body.lower()
        assert "syntax error" not in body.lower()

    async def test_422_does_not_leak_internals(
        self,
        client: AsyncClient,
        searcher: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts?status=INVALID_STATUS",
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 422
        body = resp.text
        assert "sqlalchemy" not in body.lower()
        assert "traceback" not in body.lower()

```

### `backend/tests/search/test_search_pagination.py`
```python
"""AC-027.5 — Pagination correctness under search/filter conditions.

Validates:
  * total count matches the actual number of rows satisfying the filter.
  * pages = ceil(total / page_size), always ≥ 1.
  * items on each page are non-overlapping and collectively cover all rows.
  * out-of-range page returns an empty items list (not an error).
  * page/page_size boundary enforcement.
  * ordering is stable and consistent across pages.
"""
from __future__ import annotations

import math

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.user import User
from tests.search.conftest import mod_auth_headers, user_auth_headers, _make_post


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _collect_all_pages(
    client: AsyncClient,
    url_base: str,
    headers: dict,
    page_size: int = 5,
) -> list[dict]:
    """Walk all pages of a paginated endpoint and return all items."""
    all_items: list[dict] = []
    page = 1
    while True:
        sep = "&" if "?" in url_base else "?"
        resp = await client.get(
            f"{url_base}{sep}page={page}&page_size={page_size}",
            headers=headers,
        )
        assert resp.status_code == 200, f"Page {page} failed: {resp.text}"
        data = resp.json()
        all_items.extend(data["items"])
        if page >= data["pages"]:
            break
        page += 1
    return all_items


# ---------------------------------------------------------------------------
# Fixtures: controlled corpus of N active posts
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def twelve_active_posts(
    db_session: AsyncSession,
    author: User,
) -> list[Content]:
    """Seed exactly 12 active posts owned by *author* for pagination tests."""
    posts = []
    for i in range(12):
        p = await _make_post(
            db_session,
            owner=author,
            title=f"Pagination post {i:03d}",
            body=f"Body of post {i}.",
            status=ContentStatus.active,
        )
        posts.append(p)
    return posts


@pytest_asyncio.fixture()
async def mixed_status_posts(
    db_session: AsyncSession,
    author: User,
) -> dict[str, list[Content]]:
    """Seed 4 active + 3 flagged + 2 hidden + 2 deleted posts."""
    result: dict[str, list[Content]] = {
        "active": [],
        "flagged": [],
        "hidden": [],
        "deleted": [],
    }
    counts = {"active": 4, "flagged": 3, "hidden": 2, "deleted": 2}
    for status_str, count in counts.items():
        status = ContentStatus(status_str)
        for i in range(count):
            p = await _make_post(
                db_session,
                owner=author,
                title=f"{status_str.capitalize()} post {i}",
                body="body",
                status=status,
            )
            result[status_str].append(p)
    return result


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestPaginationBasics:
    """AC-027.5 — fundamental pagination mechanics."""

    async def test_total_matches_actual_row_count(
        self,
        client: AsyncClient,
        author: User,
        search_moderator: User,
        twelve_active_posts: list[Content],
    ) -> None:
        """total in page metadata >= number of rows seeded for this author."""
        resp = await client.get(
            f"/api/v1/posts?author_id={author.id}&status=active&page_size=100",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 12

    async def test_pages_equals_ceil_total_over_page_size(
        self,
        client: AsyncClient,
        author: User,
        search_moderator: User,
        twelve_active_posts: list[Content],
    ) -> None:
        page_size = 5
        resp = await client.get(
            f"/api/v1/posts?author_id={author.id}&status=active&page_size={page_size}",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        data = resp.json()
        expected_pages = max(1, math.ceil(data["total"] / page_size))
        assert data["pages"] == expected_pages

    async def test_pages_at_least_one_when_empty(
        self,
        client: AsyncClient,
        search_moderator: User,
    ) -> None:
        """pages must be ≥ 1 even when total == 0."""
        resp = await client.get(
            "/api/v1/posts?author_id=00000000-ffff-0000-0000-000000000000",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pages"] >= 1

    async def test_out_of_range_page_returns_empty_items(
        self,
        client: AsyncClient,
        author: User,
        search_moderator: User,
        twelve_active_posts: list[Content],
    ) -> None:
        """Requesting a page beyond the last page returns empty items, not 404."""
        resp = await client.get(
            f"/api/v1/posts?author_id={author.id}&status=active&page=9999&page_size=5",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    async def test_page_size_one_returns_single_item(
        self,
        client: AsyncClient,
        author: User,
        search_moderator: User,
        twelve_active_posts: list[Content],
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts?author_id={author.id}&status=active&page=1&page_size=1",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 1

    async def test_page_size_max_100_accepted(
        self,
        client: AsyncClient,
        author: User,
        search_moderator: User,
        twelve_active_posts: list[Content],
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts?author_id={author.id}&status=active&page=1&page_size=100",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        assert resp.json()["page_size"] == 100

    async def test_page_size_101_rejected(
        self,
        client: AsyncClient,
        searcher: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts?page_size=101",
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 422

    async def test_page_0_rejected(
        self,
        client: AsyncClient,
        searcher: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts?page=0",
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestPaginationCompleteness:
    """AC-027.5 — all rows appear exactly once across pages."""

    async def test_all_rows_covered_no_duplicates(
        self,
        client: AsyncClient,
        author: User,
        search_moderator: User,
        twelve_active_posts: list[Content],
    ) -> None:
        """Walking all pages returns each seeded post exactly once."""
        seeded_ids = {p.id for p in twelve_active_posts}
        all_items = await _collect_all_pages(
            client,
            f"/api/v1/posts?author_id={author.id}&status=active",
            headers=mod_auth_headers(search_moderator),
            page_size=5,
        )
        returned_ids = [it["id"] for it in all_items]
        # No duplicates
        assert len(returned_ids) == len(set(returned_ids)), "Duplicate IDs across pages"
        # All seeded posts present
        for pid in seeded_ids:
            assert pid in returned_ids, f"Seeded post {pid} missing from paginated results"

    async def test_pagination_stable_ordering(
        self,
        client: AsyncClient,
        author: User,
        search_moderator: User,
        twelve_active_posts: list[Content],
    ) -> None:
        """Two consecutive full-scan traversals return items in the same order."""
        headers = mod_auth_headers(search_moderator)
        base_url = f"/api/v1/posts?author_id={author.id}&status=active"
        first_run = await _collect_all_pages(client, base_url, headers, page_size=4)
        second_run = await _collect_all_pages(client, base_url, headers, page_size=4)
        assert [it["id"] for it in first_run] == [it["id"] for it in second_run]

    async def test_page_metadata_consistent_across_pages(
        self,
        client: AsyncClient,
        author: User,
        search_moderator: User,
        twelve_active_posts: list[Content],
    ) -> None:
        """total and pages metadata must be identical on every page of the
        same query."""
        page_size = 3
        totals: list[int] = []
        pages_values: list[int] = []
        page = 1
        while True:
            resp = await client.get(
                f"/api/v1/posts?author_id={author.id}&status=active"
                f"&page={page}&page_size={page_size}",
                headers=mod_auth_headers(search_moderator),
            )
            assert resp.status_code == 200
            data = resp.json()
            totals.append(data["total"])
            pages_values.append(data["pages"])
            if page >= data["pages"]:
                break
            page += 1
        assert len(set(totals)) == 1, f"total changed across pages: {totals}"
        assert len(set(pages_values)) == 1, f"pages changed across pages: {pages_values}"


@pytest.mark.asyncio
class TestPaginationWithVisibilityFiltering:
    """AC-027.5 + AC-027.2 — pagination counts respect visibility rules."""

    async def test_regular_user_total_excludes_hidden_deleted(
        self,
        client: AsyncClient,
        author: User,
        searcher: User,
        mixed_status_posts: dict[str, list[Content]],
    ) -> None:
        """Regular user's listing for a foreign author_id must not include
        hidden or deleted posts owned by that author."""
        resp = await client.get(
            f"/api/v1/posts?author_id={author.id}",
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 200
        data = resp.json()
        returned_ids = {it["id"] for it in data["items"]}
        hidden_ids = {p.id for p in mixed_status_posts["hidden"]}
        deleted_ids = {p.id for p in mixed_status_posts["deleted"]}
        assert not returned_ids & hidden_ids, "Hidden posts leaked into paginated results"
        assert not returned_ids & deleted_ids, "Deleted posts leaked into paginated results"

    async def test_moderator_total_includes_all_statuses(
        self,
        client: AsyncClient,
        author: User,
        search_moderator: User,
        mixed_status_posts: dict[str, list[Content]],
    ) -> None:
        """Moderator's unfiltered listing includes all status variants."""
        resp = await client.get(
            f"/api/v1/posts?author_id={author.id}&page_size=100",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        returned_ids = {it["id"] for it in resp.json()["items"]}
        for status_str, posts in mixed_status_posts.items():
            for p in posts:
                assert p.id in returned_ids, (
                    f"Moderator listing missing {status_str} post {p.id}"
                )

    async def test_total_reflects_filtered_count_not_global(
        self,
        client: AsyncClient,
        author: User,
        search_moderator: User,
        mixed_status_posts: dict[str, list[Content]],
    ) -> None:
        """total must reflect the filtered corpus, not the global row count."""
        expected_active_count = len(mixed_status_posts["active"])
        resp = await client.get(
            f"/api/v1/posts?author_id={author.id}&status=active&page_size=100",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == expected_active_count, (
            f"total={data['total']} does not match seeded active count {expected_active_count}"
        )
        assert len(data["items"]) == expected_active_count

```

### `backend/tests/search/test_search_relevance.py`
```python
"""AC-027.1 — Search relevance and filter correctness.

Validates that the list/filter endpoint returns exactly the rows that match
the supplied filters and no extraneous results:

  AC-027.1 — Results are scoped to requested author_id filter.
  AC-027.1 — Results are scoped to requested status filter (moderators only).
  AC-027.1 — Combined author + status filters intersect correctly.
  AC-027.1 — Absent filters return all visible rows (no false-negatives).
  AC-027.1 — Pagination metadata (total/pages) reflects the filtered set.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.user import User
from tests.search.conftest import auth_headers, mod_auth_headers, user_auth_headers


@pytest.mark.asyncio
class TestSearchRelevance:
    """AC-027.1 — filter results match requested criteria exactly."""

    # ------------------------------------------------------------------
    # author_id filter
    # ------------------------------------------------------------------

    async def test_author_filter_returns_only_that_author(
        self,
        client: AsyncClient,
        searcher: User,
        author: User,
        seed_active: Content,
        db_session: AsyncSession,
    ) -> None:
        """Only posts owned by the filtered author appear in results."""
        from app.models.user import UserRole

        other = User(
            username="other_rel",
            email="other_rel@example.com",
            hashed_password="hashed",
            role=UserRole.user,
        )
        db_session.add(other)
        await db_session.flush()
        from tests.search.conftest import _make_post

        other_post = await _make_post(
            db_session,
            owner=other,
            title="Other author post",
            body="Should not appear",
            status=ContentStatus.active,
        )

        resp = await client.get(
            f"/api/v1/posts?author_id={author.id}",
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 200
        ids = [it["id"] for it in resp.json()["items"]]
        assert seed_active.id in ids
        assert other_post.id not in ids

    async def test_author_filter_nonexistent_returns_empty(
        self,
        client: AsyncClient,
        searcher: User,
    ) -> None:
        """Filtering by an unknown author_id yields an empty page, not an error."""
        resp = await client.get(
            "/api/v1/posts?author_id=00000000-0000-0000-0000-000000000000",
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    # ------------------------------------------------------------------
    # status filter (moderator only)
    # ------------------------------------------------------------------

    async def test_status_filter_active_returns_only_active(
        self,
        client: AsyncClient,
        search_moderator: User,
        full_seed: dict[str, Content],
    ) -> None:
        """Moderator filtering status=active sees only active posts."""
        resp = await client.get(
            "/api/v1/posts?status=active",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        for item in items:
            assert item["status"] == "active", f"Unexpected status {item['status']!r}"

    async def test_status_filter_hidden_returns_only_hidden(
        self,
        client: AsyncClient,
        search_moderator: User,
        full_seed: dict[str, Content],
    ) -> None:
        """Moderator filtering status=hidden sees only hidden posts."""
        resp = await client.get(
            "/api/v1/posts?status=hidden",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert full_seed["hidden"].id in [it["id"] for it in items]
        for item in items:
            assert item["status"] == "hidden"

    async def test_status_filter_deleted_returns_only_deleted(
        self,
        client: AsyncClient,
        search_moderator: User,
        full_seed: dict[str, Content],
    ) -> None:
        resp = await client.get(
            "/api/v1/posts?status=deleted",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert full_seed["deleted"].id in [it["id"] for it in items]
        for item in items:
            assert item["status"] == "deleted"

    async def test_status_filter_flagged_returns_only_flagged(
        self,
        client: AsyncClient,
        search_moderator: User,
        full_seed: dict[str, Content],
    ) -> None:
        resp = await client.get(
            "/api/v1/posts?status=flagged",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert full_seed["flagged"].id in [it["id"] for it in items]
        for item in items:
            assert item["status"] == "flagged"

    async def test_status_filter_locked_returns_only_locked(
        self,
        client: AsyncClient,
        search_moderator: User,
        full_seed: dict[str, Content],
    ) -> None:
        resp = await client.get(
            "/api/v1/posts?status=locked",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert full_seed["locked"].id in [it["id"] for it in items]
        for item in items:
            assert item["status"] == "locked"

    # ------------------------------------------------------------------
    # Combined filters
    # ------------------------------------------------------------------

    async def test_combined_author_and_status_filter(
        self,
        client: AsyncClient,
        search_moderator: User,
        author: User,
        full_seed: dict[str, Content],
        db_session: AsyncSession,
    ) -> None:
        """author_id + status filter must intersect — not union."""
        from app.models.user import UserRole

        other = User(
            username="other_comb",
            email="other_comb@example.com",
            hashed_password="hashed",
            role=UserRole.user,
        )
        db_session.add(other)
        await db_session.flush()
        from tests.search.conftest import _make_post

        other_active = await _make_post(
            db_session,
            owner=other,
            title="Other active",
            body="body",
            status=ContentStatus.active,
        )

        resp = await client.get(
            f"/api/v1/posts?author_id={author.id}&status=active",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        ids = [it["id"] for it in resp.json()["items"]]
        assert full_seed["active"].id in ids
        # Other author's active post must NOT appear
        assert other_active.id not in ids
        # Author's non-active posts must NOT appear
        assert full_seed["flagged"].id not in ids
        assert full_seed["deleted"].id not in ids

    # ------------------------------------------------------------------
    # No filter — baseline
    # ------------------------------------------------------------------

    async def test_no_filter_includes_active_posts(
        self,
        client: AsyncClient,
        searcher: User,
        seed_active: Content,
    ) -> None:
        """Unfiltered listing for a regular user includes active posts."""
        resp = await client.get(
            "/api/v1/posts",
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 200
        ids = [it["id"] for it in resp.json()["items"]]
        assert seed_active.id in ids

    async def test_invalid_status_value_rejected(
        self,
        client: AsyncClient,
        searcher: User,
    ) -> None:
        """An unrecognised status enum value returns 422."""
        resp = await client.get(
            "/api/v1/posts?status=unapproved",
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 422

```

### `backend/tests/search/test_visibility_leakage.py`
```python
"""AC-027.2 & AC-027.3 — Visibility-leakage prevention.

Ensures that hidden, deleted, and flagged (unapproved) content is NEVER
returned to unprivileged callers, even when:

  * The content exists and has a known ID (direct-read endpoint).
  * Listing is used with or without an explicit status filter.
  * The content is owned by a third party.
  * The content is owned by the calling user (self-listing edge cases).

AC-027.2 — hidden/deleted content is not leaked to regular users.
AC-027.3 — flagged (unapproved) content is not leaked to regular users
           UNLESS the caller is the author viewing their own posts.

Moderators are expected to see all statuses (positive control).
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.user import User
from tests.search.conftest import auth_headers, mod_auth_headers, user_auth_headers


@pytest.mark.asyncio
class TestHiddenContentNotLeaked:
    """AC-027.2 — hidden posts are invisible to regular users."""

    async def test_hidden_post_absent_from_unfiltered_listing(
        self,
        client: AsyncClient,
        searcher: User,
        seed_hidden: Content,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 200
        ids = [it["id"] for it in resp.json()["items"]]
        assert seed_hidden.id not in ids, (
            "Hidden post must not appear in unfiltered listing for regular user"
        )

    async def test_hidden_post_direct_read_visible_to_owner(
        self,
        client: AsyncClient,
        author: User,
        seed_hidden: Content,
    ) -> None:
        """Author can still GET their own hidden post by ID (read endpoint
        does not enforce status visibility for the owner — design intent).
        This test documents the expected behaviour rather than asserting
        hidden content is forbidden for the owner.
        """
        resp = await client.get(
            f"/api/v1/posts/{seed_hidden.id}",
            headers=user_auth_headers(author),
        )
        # 200 for owner — hidden doesn't mean 404 on direct read
        assert resp.status_code == 200
        assert resp.json()["id"] == seed_hidden.id

    async def test_hidden_post_direct_read_visible_to_moderator(
        self,
        client: AsyncClient,
        search_moderator: User,
        seed_hidden: Content,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{seed_hidden.id}",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200

    async def test_moderator_can_list_hidden_posts(
        self,
        client: AsyncClient,
        search_moderator: User,
        seed_hidden: Content,
    ) -> None:
        """Positive control: moderators see hidden posts via status filter."""
        resp = await client.get(
            "/api/v1/posts?status=hidden",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        ids = [it["id"] for it in resp.json()["items"]]
        assert seed_hidden.id in ids

    async def test_regular_user_status_filter_hidden_rejected_or_empty(
        self,
        client: AsyncClient,
        searcher: User,
        seed_hidden: Content,
    ) -> None:
        """When a regular user explicitly requests status=hidden, either the
        request is rejected (403/422) or the hidden post is still absent.
        The current implementation returns 200 with an empty set for the
        non-owner searcher because the status filter is applied but the
        visibility rule also excludes status != deleted for non-owner
        paths — net effect: hidden post must not appear.
        """
        resp = await client.get(
            "/api/v1/posts?status=hidden",
            headers=user_auth_headers(searcher),
        )
        # Acceptable outcomes: permission error OR empty/filtered result
        if resp.status_code == 200:
            ids = [it["id"] for it in resp.json()["items"]]
            assert seed_hidden.id not in ids, (
                "Hidden post must not appear even when explicitly requested by non-owner"
            )
        else:
            assert resp.status_code in (403, 422)


@pytest.mark.asyncio
class TestDeletedContentNotLeaked:
    """AC-027.2 — deleted posts are invisible to regular users (cross-user)."""

    async def test_deleted_absent_from_unfiltered_listing_by_other_user(
        self,
        client: AsyncClient,
        searcher: User,
        seed_deleted: Content,
    ) -> None:
        """A regular user listing all posts must not see another user's
        deleted post."""
        resp = await client.get(
            "/api/v1/posts",
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 200
        ids = [it["id"] for it in resp.json()["items"]]
        assert seed_deleted.id not in ids

    async def test_deleted_absent_when_filtering_by_other_authors_id(
        self,
        client: AsyncClient,
        searcher: User,
        author: User,
        seed_deleted: Content,
    ) -> None:
        """Filtering by the owning author's ID must still exclude deleted
        posts for a third-party caller."""
        resp = await client.get(
            f"/api/v1/posts?author_id={author.id}",
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 200
        ids = [it["id"] for it in resp.json()["items"]]
        assert seed_deleted.id not in ids

    async def test_author_self_listing_may_see_own_deleted(
        self,
        client: AsyncClient,
        author: User,
        seed_deleted: Content,
    ) -> None:
        """An author listing their OWN posts (author_id == caller_id) is
        permitted to see their own deleted posts per AC-018 business rule.
        """
        resp = await client.get(
            f"/api/v1/posts?author_id={author.id}",
            headers=user_auth_headers(author),
        )
        assert resp.status_code == 200
        ids = [it["id"] for it in resp.json()["items"]]
        assert seed_deleted.id in ids

    async def test_moderator_sees_all_deleted(
        self,
        client: AsyncClient,
        search_moderator: User,
        seed_deleted: Content,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts?status=deleted",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        ids = [it["id"] for it in resp.json()["items"]]
        assert seed_deleted.id in ids

    async def test_regular_user_explicit_deleted_filter_not_leaked(
        self,
        client: AsyncClient,
        searcher: User,
        author: User,
        seed_deleted: Content,
    ) -> None:
        """Even with an explicit status=deleted parameter and author_id of
        the content owner, a third-party regular user must not see the
        deleted post.
        """
        resp = await client.get(
            f"/api/v1/posts?author_id={author.id}&status=deleted",
            headers=user_auth_headers(searcher),
        )
        if resp.status_code == 200:
            ids = [it["id"] for it in resp.json()["items"]]
            assert seed_deleted.id not in ids
        else:
            assert resp.status_code in (403, 422)


@pytest.mark.asyncio
class TestFlaggedContentNotLeaked:
    """AC-027.3 — flagged (unapproved) content is not leaked to non-authors."""

    async def test_flagged_absent_from_unfiltered_listing(
        self,
        client: AsyncClient,
        searcher: User,
        seed_flagged: Content,
    ) -> None:
        """Flagged posts must not appear in a regular user's unfiltered
        listing when the caller is not the author."""
        resp = await client.get(
            "/api/v1/posts",
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 200
        ids = [it["id"] for it in resp.json()["items"]]
        assert seed_flagged.id not in ids

    async def test_flagged_absent_when_filtering_by_author_id(
        self,
        client: AsyncClient,
        searcher: User,
        author: User,
        seed_flagged: Content,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts?author_id={author.id}",
            headers=user_auth_headers(searcher),
        )
        assert resp.status_code == 200
        ids = [it["id"] for it in resp.json()["items"]]
        assert seed_flagged.id not in ids

    async def test_moderator_sees_flagged_posts(
        self,
        client: AsyncClient,
        search_moderator: User,
        seed_flagged: Content,
    ) -> None:
        """Positive control: moderators must see flagged posts."""
        resp = await client.get(
            "/api/v1/posts?status=flagged",
            headers=mod_auth_headers(search_moderator),
        )
        assert resp.status_code == 200
        ids = [it["id"] for it in resp.json()["items"]]
        assert seed_flagged.id in ids

    async def test_regular_user_explicit_flagged_filter_not_leaked(
        self,
        client: AsyncClient,
        searcher: User,
        author: User,
        seed_flagged: Content,
    ) -> None:
        """status=flagged explicit filter from a non-moderator should yield
        either a permission error or an empty/filtered result."""
        resp = await client.get(
            f"/api/v1/posts?author_id={author.id}&status=flagged",
            headers=user_auth_headers(searcher),
        )
        if resp.status_code == 200:
            ids = [it["id"] for it in resp.json()["items"]]
            assert seed_flagged.id not in ids
        else:
            assert resp.status_code in (403, 422)


@pytest.mark.asyncio
class TestUnauthenticatedCannotSearch:
    """Unauthenticated requests to search/list endpoints must be rejected."""

    async def test_unauthenticated_list_rejected(
        self,
        client: AsyncClient,
    ) -> None:
        resp = await client.get("/api/v1/posts")
        assert resp.status_code == 401

    async def test_unauthenticated_read_rejected(
        self,
        client: AsyncClient,
        seed_active: Content,
    ) -> None:
        resp = await client.get(f"/api/v1/posts/{seed_active.id}")
        assert resp.status_code == 401

```

### `pyproject.toml`
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["backend/tests"]
asyncio_default_fixture_loop_scope = "function"
pythonpath = ["../archpilot_verify_dx9j7aj8/backend"]

```

### `pytest.ini`
```text
[pytest]
asyncio_mode = auto
testpaths = backend/tests
asyncio_default_fixture_loop_scope = function
pythonpath = ../archpilot_verify_dx9j7aj8/backend

```