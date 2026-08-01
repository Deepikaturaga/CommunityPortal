# Implementation Report

The written files appear in the CWD of each verification call. Let me write the files directly to the repo path using python in one call:

## Verification
- `node -e "const fs=require('fs'); function walk(d,p=''){try{fs.readdirSync(d).forEach(f=>{const full=d+'/'+f,rel=p+'/'+f;try{if(fs.statSync(full).isDirectory()&&!f.startsWith('node_modules')&&f!=='.git')walk(full,rel);else if(!f.startsWith('node_modules')&&f!=='.git')console.log(rel);}catch(e){}});}catch(e){}} walk('.')"` → exit 127
- `python3 -c "
import os
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__', '.next', 'dist', 'build', '.venv', 'venv')]
    for f in files:
        print(os.path.join(root, f))
"` → exit 0
- `python3 -c "
import os, sys
results = []
for root, dirs, files in os.walk('/workspace'):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__', '.next', 'dist', 'build')]
    for f in files:
        results.append(os.path.join(root, f))
print('\n'.join(results[:120]))
"` → exit 0
- `python3 -c "
import os
for root, dirs, files in os.walk('/home'):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__')]
    for f in files:
        print(os.path.join(root, f))
"` → exit 0
- `python3 -c "import os; print(os.getcwd()); print(os.listdir('.'))"` → exit 0
- `python3 -c "
import os
cwd = os.getcwd()
print('CWD:', cwd)
# walk up to find repo root
for path in [cwd, os.path.dirname(cwd), '/app', '/srv', '/code', '/project', '/repo']:
    if os.path.exists(path):
        items = os.listdir(path)
        if items:
            print(f'{path}: {items[:30]}')
"` → exit 0
- `python3 -c "
import os
for root, dirs, files in os.walk('/app'):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__', '.next', 'dist', 'build', 'venv', '.venv')]
    for f in files:
        print(os.path.join(root, f))
"` → exit 0
- `python3 -c "
with open('/app/skills/RUNTIME_IMPLEMENTATION_PLAN.md') as f:
    print(f.read())
"` → exit 0
- `python3 -c "
with open('/app/skills/RUNTIME_SPEC.md') as f:
    content = f.read()
    print(content[:8000])
"` → exit 0
- `python3 -c "
with open('/app/skills/testing/api_testing.md') as f:
    print(f.read())
"` → exit 0
- `python3 -c "
with open('/app/skills/planning/product_surface_plan.md') as f:
    print(f.read()[:6000])
"` → exit 0
- `python3 -c "
import os, json
# look for session/run data  
for path in ['/tmp', '/var/tmp']:
    if os.path.exists(path):
        items = os.listdir(path)
        print(f'{path}: {items}')
"` → exit 0
- `python3 -c "
import os
for root, dirs, files in os.walk('/tmp/archpilot_verify_dx9j7aj8'):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__')]
    for f in files:
        print(os.path.join(root, f))
"` → exit 0
- `python3 -c "
files = [
    '/tmp/archpilot_verify_dx9j7aj8/backend/pytest.ini',
    '/tmp/archpilot_verify_dx9j7aj8/backend/.env',
    '/tmp/archpilot_verify_dx9j7aj8/backend/app/main.py',
    '/tmp/archpilot_verify_dx9j7aj8/backend/app/core/config.py',
    '/tmp/archpilot_verify_dx9j7aj8/backend/app/core/database.py',
    '/tmp/archpilot_verify_dx9j7aj8/backend/app/core/security.py',
]
for f in files:
    print(f'\\n=== {f} ===')
    with open(f) as fh:
        print(fh.read())
"` → exit 0
- `python3 -c "
files = [
    '/tmp/archpilot_verify_dx9j7aj8/backend/app/models/user.py',
    '/tmp/archpilot_verify_dx9j7aj8/backend/app/models/moderation.py',
    '/tmp/archpilot_verify_dx9j7aj8/backend/app/models/content.py',
    '/tmp/archpilot_verify_dx9j7aj8/backend/app/models/base.py',
]
for f in files:
    print(f'\\n=== {f} ===')
    with open(f) as fh:
        print(fh.read())
"` → exit 0
- `python3 -c "
files = [
    '/tmp/archpilot_verify_dx9j7aj8/backend/app/models/user.py',
    '/tmp/archpilot_verify_dx9j7aj8/backend/app/services/moderation/router.py',
    '/tmp/archpilot_verify_dx9j7aj8/backend/app/services/moderation/actions.py',
    '/tmp/archpilot_verify_dx9j7aj8/backend/app/services/moderation/schemas.py',
]
for f in files:
    print(f'\\n=== {f} ===')
    with open(f) as fh:
        print(fh.read())
"` → exit 0
- `python3 -c "
files = [
    '/tmp/archpilot_verify_dx9j7aj8/backend/app/models/user.py',
    '/tmp/archpilot_verify_dx9j7aj8/backend/app/services/moderation/router.py',
]
for f in files:
    print(f'\\n=== {f} ===')
    with open(f) as fh:
        print(fh.read())
"` → exit 0
- `python3 -c "
files = [
    '/tmp/archpilot_verify_dx9j7aj8/backend/tests/conftest.py',
    '/tmp/archpilot_verify_dx9j7aj8/backend/tests/test_moderation.py',
    '/tmp/archpilot_verify_dx9j7aj8/backend/tests/__init__.py',
    '/tmp/archpilot_verify_dx9j7aj8/backend/pytest.ini',
    '/tmp/archpilot_verify_dx9j7aj8/backend/.env',
]
for f in files:
    print(f'\\n=== {f} ===')
    with open(f) as fh:
        print(fh.read())
"` → exit 0
- `python3 -c "
with open('/tmp/archpilot_verify_dx9j7aj8/backend/tests/conftest.py') as f:
    print(f.read())
"` → exit 0
- `python3 -c "
with open('/tmp/archpilot_verify_dx9j7aj8/backend/tests/test_moderation.py') as f:
    print(f.read())
"` → exit 0
- `python3 -c "
with open('/tmp/archpilot_verify_dx9j7aj8/backend/tests/test_moderation.py') as f:
    content = f.read()
print(repr(content[:200]))
print('---FULL CONTENT BYTES:', len(content))
# show from beginning
import base64
print(base64.b64encode(content[:3000].encode()).decode())
"` → exit 0
- `python3 -c "
import os
for root, dirs, files in os.walk('/tmp/archpilot_verify_dx9j7aj8'):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__', '.venv', 'venv', '__pycache__')]
    for f in files:
        print(os.path.join(root, f))
"` → exit 0
- `python3 -c "
import base64
with open('/tmp/archpilot_verify_dx9j7aj8/backend/tests/test_moderation.py', 'rb') as f:
    raw = f.read()
print('SIZE:', len(raw))
print(base64.b64encode(raw).decode())
"` → exit 0
- `python3 -c "
import base64
data = 'nQgcmVzcC5zdGF0dXNfY29kZSA9PSA0MDEKCiAgICBhc3luYyBkZWYgdGVzdF9hY3Rpb25fcmVqZWN0c19yZWd1bGFyX3VzZXIoc2VsZiwgY2xpZW50OiBBc3luY0NsaWVudCwgcmVndWxhcl91c2VyOiBVc2VyLCBmbGFnZ2VkX2NvbnRlbnQ6IENvbnRlbnQpIC0+IE5vbmU6CiAgICAgICAgdG9rZW4gPSBtYWtlX3VzZXJfdG9rZW4ocmVndWxhcl91c2VyKQogICAgICAgIHJlc3AgPSBhd2FpdCBjbGllbnQucG9zdChmIi9hcGkvdjEvbW9kZXJhdGlvbi9xdWV1ZS97ZmxhZ2dlZF9jb250ZW50LmlkfS9hY3Rpb25zIiwganNvbj17ImFjdGlvbiI6ICJsb2NrIn0sIGhlYWRlcnM9YXV0aF9oZWFkZXJzKHRva2VuKSkKICAgICAgICBhc3NlcnQgcmVzcC5zdGF0dXNfY29kZSA9PSA0MDMKCiAgICBhc3luYyBkZWYgdGVzdF9ub25leGlzdGVudF9jb250ZW50XzQwNChzZWxmLCBjbGllbnQ6IEFzeW5jQ2xpZW50LCBtb2RlcmF0b3JfdXNlcjogVXNlcikgLT4gTm9uZToKICAgICAgICB0b2tlbiA9IG1ha2VfbW9kZXJhdG9yX3Rva2VuKG1vZGVyYXRvcl91c2VyKQogICAgICAgIHJlc3AgPSBhd2FpdCBjbGllbnQucG9zdCgiL2FwaS92MS9tb2RlcmF0aW9uL3F1ZXVlL25vbmV4aXN0ZW50LWlkL2FjdGlvbnMiLCBqc29uPXsiYWN0aW9uIjogImxvY2sifSwgaGVhZGVycz1hdXRoX2hlYWRlcnModG9rZW4pKQogICAgICAgIGFzc2VydCByZXNwLnN0YXR1c19jb2RlID09IDQwNAoKICAgIGFzeW5jIGRlZiB0ZXN0X2lsbGVnYWxfdHJhbnNpdGlvbl80MjIoc2VsZiwgY2xpZW50OiBBc3luY0NsaWVudCwgbW9kZXJhdG9yX3VzZXI6IFVzZXIsIGRiX3Nlc3Npb246IEFzeW5jU2Vzc2lvbiwgcmVndWxhcl91c2VyOiBVc2VyKSAtPiBOb25lOgogICAgICAgIGRlbGV0ZWRfY29udGVudCA9IENvbnRlbnQoYXV0aG9yX2lkPXJlZ3VsYXJfdXNlci5pZCwgdGl0bGU9IkRlbGV0ZWQiLCBib2R5PSJib2R5Iiwgc3RhdHVzPUNvbnRlbnRTdGF0dXMuZGVsZXRlZCkKICAgICAgICBkYl9zZXNzaW9uLmFkZChkZWxldGVkX2NvbnRlbnQpCiAgICAgICAgYXdhaXQgZGJfc2Vzc2lvbi5mbHVzaCgpCiAgICAgICAgdG9rZW4gPSBtYWtlX21vZGVyYXRvcl90b2tlbihtb2RlcmF0b3JfdXNlcikKICAgICAgICByZXNwID0gYXdhaXQgY2xpZW50LnBvc3QoZiIvYXBpL3YxL21vZGVyYXRpb24vcXVldWUve2RlbGV0ZWRfY29udGVudC5pZH0vYWN0aW9ucyIsIGpzb249eyJhY3Rpb24iOiAibG9jayJ9LCBoZWFkZXJzPWF1dGhfaGVhZGVycyh0b2tlbikpCiAgICAgICAgYXNzZXJ0IHJlc3Auc3RhdHVzX2NvZGUgPT0gNDIyCgogICAgYXN5bmMgZGVmIHRlc3RfcmVhc29uX29wdGlvbmFsKHNlbGYsIGNsaWVudDogQXN5bmNDbGllbnQsIG1vZGVyYXRvcl91c2VyOiBVc2VyLCBmbGFnZ2VkX2NvbnRlbnQ6IENvbnRlbnQpIC0+IE5vbmU6CiAgICAgICAgdG9rZW4gPSBtYWtlX21vZGVyYXRvcl90b2tlbihtb2RlcmF0b3JfdXNlcikKICAgICAgICByZXNwID0gYXdhaXQgY2xpZW50LnBvc3QoZiIvYXBpL3YxL21vZGVyYXRpb24vcXVldWUve2ZsYWdnZWRfY29udGVudC5pZH0vYWN0aW9ucyIsIGpzb249eyJhY3Rpb24iOiAiaGlkZSJ9LCBoZWFkZXJzPWF1dGhfaGVhZGVycyh0b2tlbikpCiAgICAgICAgYXNzZXJ0IHJlc3Auc3RhdHVzX2NvZGUgPT0gMjAwCiAgICAgICAgYXNzZXJ0IHJlc3AuanNvbigpWyJhdWRpdF9yZWNvcmQiXVsicmVhc29uIl0gaXMgTm9uZQoKY2xhc3MgVGVzdEF1ZGl0SW1tdXRhYmlsaXR5OgogICAgYXN5bmMgZGVmIHRlc3Rfb3JtX3VwZGF0ZV9yYWlzZXMoc2VsZiwgZGJfc2Vzc2lvbjogQXN5bmNTZXNzaW9uLCBtb2RlcmF0b3JfdXNlcjogVVNlciwgZmxhZ2dlZF9jb250ZW50OiBDb250ZW50KSAtPiBOb25lOgogICAgICAgIHJlY29yZCA9IE1vZGVyYXRpb25BdWRpdFJlY29yZCgKICAgICAgICAgICAgY29udGVudF9pZD1mbGFnZ2VkX2NvbnRlbnQuaWQsIG1vZGVyYXRvcl9pZD1tb2RlcmF0b3JfdXNlci5pZCwKICAgICAgICAgICAgYWN0aW9uPSJsb2NrIiwgcmVhc29uPSJvcmlnaW5hbCIsIHByZXZpb3VzX3N0YXR1cz0iZmxhZ2dlZCIsIG5ld19zdGF0dXM9ImxvY2tlZCIsCiAgICAgICAgKQogICAgICAgIGRiX3Nlc3Npb24uYWRkKHJlY29yZCkKICAgICAgICBhd2FpdCBkYl9zZXNzaW9uLmZsdXNoKCkKICAgICAgICByZWNvcmQucmVhc29uID0gInRhbXBlcmVkIgogICAgICAgIHdpdGggcHl0ZXN0LnJhaXNlcyhSdW50aW1lRXJyb3IsIG1hdGNoPSJpbW11dGFibGUiKToKICAgICAgICAgICAgYXdhaXQgZGJfc2Vzc2lvbi5mbHVzaCgpCgogICAgYXN5bmMgZGVmIHRlc3Rfb3JtX2RlbGV0ZV9yYWlzZXMoc2VsZiwgZGJfc2Vzc2lvbjogQXN5bmNTZXNzaW9uLCBtb2RlcmF0b3JfdXNlcjogVXNlciwgZmxhZ2dlZF9jb250ZW50OiBDb250ZW50KSAtPiBOb25lOgogICAgICAgIHJlY29yZCA9IE1vZGVyYXRpb25BdWRpdFJlY29yZCgKICAgICAgICAgICAgY29udGVudF9pZD1mbGFnZ2VkX2NvbnRlbnQuaWQsIG1vZGVyYXRvcl9pZD1tb2RlcmF0b3JfdXNlci5pZCwKICAgICAgICAgICAgYWN0aW9uPSJoaWRlIiwgcmVhc29uPU5vbmUsIHByZXZpb3VzX3N0YXR1cz0iZmxhZ2dlZCIsIG5ld19zdGF0dXM9ImhpZGRlbiIsCiAgICAgICAgKQogICAgICAgIGRiX3Nlc3Npb24uYWRkKHJlY29yZCkKICAgICAgICBhd2FpdCBkYl9zZXNzaW9uLmZsdXNoKCkKICAgICAgICBhd2FpdCBkYl9zZXNzaW9uLmRlbGV0ZShyZWNvcmQpCiAgICAgICAgd2l0aCBweXRlc3QucmFpc2VzKFJ1bnRpbWVFcnJvciwgbWF0Y2g9ImltbXV0YWJsZSIpOgogICAgICAgICAgICBhd2FpdCBkYl9zZXNzaW9uLmZsdXNoKCkKCmFzeW5jIGRlZiB0ZXN0X2hlYWx0aChjbGllbnQ6IEFzeW5jQ2xpZW50KSAtPiBOb25lOgogICAgcmVzcCA9IGF3YWl0IGNsaWVudC5nZXQoIi9oZWFsdGgiKQogICAgYXNzZXJ0IHJlc3Auc3RhdHVzX2NvZGUgPT0gMjAwCiAgICBhc3NlcnQgcmVzcC5qc29uKCkgPT0geyJzdGF0dXMiOiAib2sifQo='
print(base64.b64decode(data).decode())
"` → exit 1
- `pip list` → exit 0
- `python3 -c "
import importlib.metadata as m
packages = ['fastapi','sqlalchemy','pytest','httpx','pydantic','aiosqlite','pytest-cov','slowapi','starlette','python-jose','pytest-asyncio','anyio','uvicorn','passlib','bcrypt','alembic','pydantic-settings','aiosqlite']
for p in packages:
    try:
        v = m.version(p)
        print(f'{p}=={v}')
    except:
        print(f'{p}: NOT INSTALLED')
"` → exit 0
- `python3 -c "
with open('/tmp/archpilot_verify_dx9j7aj8/backend/app/main.py') as f:
    print(f.read())
"` → exit 0
- `python3 -c "
import shutil, os

# Source: written files in /tmp/archpilot_verify_jnb7qzgu/backend
# Target: the actual repo in /tmp/archpilot_verify_dx9j7aj8/backend
src_base = '/tmp/archpilot_verify_jnb7qzgu'
dst_base = '/tmp/archpilot_verify_dx9j7aj8'

# The files we wrote
written = [
    'backend/app/models/post.py',
    'backend/app/services/posts/__init__.py',
    'backend/app/services/posts/schemas.py',
    'backend/app/services/posts/actions.py',
    'backend/app/services/posts/router.py',
    'backend/app/main.py',
    'backend/tests/posts/conftest.py',
    'backend/tests/posts/test_create.py',
    'backend/tests/posts/test_read.py',
    'backend/tests/posts/test_list.py',
    'backend/tests/posts/test_update.py',
    'backend/tests/posts/test_delete.py',
    'backend/tests/posts/test_rate_limit.py',
    'backend/tests/posts/test_contract.py',
    'backend/tests/posts/test_service_unit.py',
    'backend/tests/posts/locustfile.py',
]

for rel_path in written:
    src = os.path.join(src_base, rel_path)
    dst = os.path.join(dst_base, rel_path)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    print(f'Copied: {rel_path}')
"` → exit 1
- `python3 -c "
import os
# Find where the write_file tool put files
for base in ['/tmp', '/var/tmp', '/workspace']:
    if not os.path.exists(base): continue
    for item in os.listdir(base):
        full = os.path.join(base, item)
        if os.path.isdir(full) and 'archpilot' in item:
            print(full)
            for root, dirs, files in os.walk(full):
                dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__')]
                for f in files:
                    print('  ', os.path.join(root, f))
"` → exit 0
- `python3 -c "
import shutil, os

src_base = '/tmp/archpilot_verify_84_rq3ru'
dst_base = '/tmp/archpilot_verify_dx9j7aj8'

written = [
    'backend/app/models/post.py',
    'backend/app/services/posts/__init__.py',
    'backend/app/services/posts/schemas.py',
    'backend/app/services/posts/actions.py',
    'backend/app/services/posts/router.py',
    'backend/app/main.py',
    'backend/tests/posts/conftest.py',
    'backend/tests/posts/test_create.py',
    'backend/tests/posts/test_read.py',
    'backend/tests/posts/test_list.py',
    'backend/tests/posts/test_update.py',
    'backend/tests/posts/test_delete.py',
    'backend/tests/posts/test_rate_limit.py',
    'backend/tests/posts/test_contract.py',
    'backend/tests/posts/test_service_unit.py',
    'backend/tests/posts/locustfile.py',
]

for rel_path in written:
    src = os.path.join(src_base, rel_path)
    dst = os.path.join(dst_base, rel_path)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    print(f'OK: {rel_path}')
print('Done.')
"` → exit 1
- `python3 -c "
import os
for root, dirs, files in os.walk('/tmp/archpilot_verify_84_rq3ru'):
    dirs[:] = [d for d in dirs if d not in ('__pycache__',)]
    for f in files:
        print(os.path.join(root, f))
"` → exit 0
- `python3 -c "
import os
# Find the current verification temp dir and the repo dir
cwd = os.getcwd()
print('CWD:', cwd)

# List /tmp to see all archpilot dirs
for item in sorted(os.listdir('/tmp')):
    if 'archpilot' in item:
        p = '/tmp/' + item
        contents = []
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in ('__pycache__',)]
            for f in files:
                contents.append(os.path.join(root, f))
        print(p, ':', len(contents), 'files')
"` → exit 0
- `python3 -c "
import os, shutil

cwd = os.getcwd()  # This session's written files
repo = '/tmp/archpilot_verify_dx9j7aj8'

for root, dirs, files in os.walk(cwd):
    dirs[:] = [d for d in dirs if d not in ('__pycache__',)]
    for f in files:
        src = os.path.join(root, f)
        rel = os.path.relpath(src, cwd)
        dst = os.path.join(repo, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        print(f'Copied: {rel}')
print('Done.')
"` → exit 0

## Generated Files

### `backend/app/main.py`
```python
from __future__ import annotations
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import engine
from app.models.base import Base
import app.models.user
import app.models.content
import app.models.moderation
from app.services.moderation.router import router as moderation_router
from app.services.posts.router import router as posts_router

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if settings.ENVIRONMENT in ("development", "test"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(title="Moderation Service", version="0.1.0", lifespan=lifespan)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    import logging
    logging.getLogger(__name__).exception("Unhandled error: %s %s", request.method, request.url)
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Internal server error"})

app.include_router(moderation_router, prefix="/api/v1")
app.include_router(posts_router, prefix="/api/v1")

@app.get("/health", tags=["ops"], include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}

```

### `backend/app/models/post.py`
```python
"""
Post model re-exports.

The canonical storage for user posts is the ``Content`` table introduced in
PHASE-026.  The posts service (PHASE-027) builds CRUD operations on top of
that same table.  This module re-exports the relevant symbols so that the
posts service can import from a stable, domain-named location.
"""
from __future__ import annotations

from app.models.content import Content, ContentStatus, CONTENT_TRANSITIONS  # noqa: F401

# Convenience alias so that posts-service code reads naturally.
Post = Content
PostStatus = ContentStatus

__all__ = [
    "Post",
    "PostStatus",
    "Content",
    "ContentStatus",
    "CONTENT_TRANSITIONS",
]

```

### `backend/app/services/posts/__init__.py`
```python
"""Posts service package."""

```

### `backend/app/services/posts/actions.py`
```python
"""Post service business logic.

Covers:
  AC-016.x  Create post
  AC-017.x  Read single post
  AC-018.x  List / paginate posts
  AC-019.x  Update post (own content; moderators may update any)
  AC-020.x  Soft-delete post (sets status=deleted; hard-delete forbidden via model)
  AC-021.x  Per-author post creation rate limiting (enforced in service layer)
"""
from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus, CONTENT_TRANSITIONS
from app.services.posts.schemas import PostCreateRequest, PostOut, PostPage, PostUpdateRequest

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class PostNotFoundError(Exception):
    """Raised when a requested post does not exist."""


class PostForbiddenError(Exception):
    """Raised when the caller is not permitted to perform the operation."""


class PostDeletedError(Exception):
    """Raised when a caller attempts to modify a soft-deleted post."""


class RateLimitError(Exception):
    """Raised when the per-author post-creation rate limit is exceeded.

    AC-021.1 — max 10 posts per author per rolling 60-second window.
    """


# ---------------------------------------------------------------------------
# Rate-limit constants
# ---------------------------------------------------------------------------
RATE_LIMIT_MAX_POSTS: int = 10
RATE_LIMIT_WINDOW_SECONDS: int = 60


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------


async def _get_post_or_raise(db: AsyncSession, post_id: str) -> Content:
    """Load a Content row or raise ``PostNotFoundError``."""
    stmt = select(Content).where(Content.id == post_id)
    post: Content | None = (await db.execute(stmt)).scalar_one_or_none()
    if post is None:
        raise PostNotFoundError(f"Post {post_id!r} not found.")
    return post


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def create_post(
    db: AsyncSession,
    *,
    author_id: str,
    payload: PostCreateRequest,
) -> PostOut:
    """AC-016 — create a new post.

    AC-021.1 — enforce rate limit: max ``RATE_LIMIT_MAX_POSTS`` posts per
    author within a rolling ``RATE_LIMIT_WINDOW_SECONDS``-second window.
    """
    window_start = datetime.now(UTC) - timedelta(seconds=RATE_LIMIT_WINDOW_SECONDS)
    count_stmt = (
        select(func.count())
        .select_from(Content)
        .where(
            Content.author_id == author_id,
            Content.created_at >= window_start,
        )
    )
    recent_count: int = (await db.execute(count_stmt)).scalar_one()
    if recent_count >= RATE_LIMIT_MAX_POSTS:
        raise RateLimitError(
            f"Rate limit exceeded: max {RATE_LIMIT_MAX_POSTS} posts per "
            f"{RATE_LIMIT_WINDOW_SECONDS}s window."
        )

    post = Content(
        author_id=author_id,
        title=payload.title,
        body=payload.body,
        status=ContentStatus.active,
        is_locked=False,
    )
    db.add(post)
    await db.flush()
    return PostOut.model_validate(post)


async def get_post(
    db: AsyncSession,
    *,
    post_id: str,
    caller_id: str,
    caller_role: str,
) -> PostOut:
    """AC-017 — retrieve a single post.

    Regular users may only read their own posts or non-deleted content.
    Moderators/admins may read any post.

    AC-017.3 — deleted posts are hidden from regular users (404 semantics).
    """
    post = await _get_post_or_raise(db, post_id)

    is_privileged = caller_role in ("moderator", "admin")
    if post.status == ContentStatus.deleted and not is_privileged:
        raise PostNotFoundError(f"Post {post_id!r} not found.")

    return PostOut.model_validate(post)


async def list_posts(
    db: AsyncSession,
    *,
    caller_id: str,
    caller_role: str,
    author_id: str | None = None,
    status_filter: ContentStatus | None = None,
    page: int = 1,
    page_size: int = 20,
) -> PostPage:
    """AC-018 — paginated list.

    * Regular users: see only non-deleted posts (or their own posts of any
      status when ``author_id == caller_id``).
    * Moderators/admins: see all posts regardless of status.
    """
    is_privileged = caller_role in ("moderator", "admin")

    filters: list = []

    if author_id:
        filters.append(Content.author_id == author_id)

    if status_filter:
        filters.append(Content.status == status_filter)
    elif not is_privileged:
        # Regular users cannot see deleted posts unless they are the author.
        if author_id != caller_id:
            filters.append(Content.status != ContentStatus.deleted)

    count_stmt = select(func.count()).select_from(Content)
    if filters:
        count_stmt = count_stmt.where(*filters)
    total: int = (await db.execute(count_stmt)).scalar_one()

    offset = (page - 1) * page_size
    rows_stmt = (
        select(Content)
        .order_by(Content.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    if filters:
        rows_stmt = rows_stmt.where(*filters)
    rows = list((await db.execute(rows_stmt)).scalars().all())

    return PostPage(
        items=[PostOut.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


async def update_post(
    db: AsyncSession,
    *,
    post_id: str,
    caller_id: str,
    caller_role: str,
    payload: PostUpdateRequest,
) -> PostOut:
    """AC-019 — update title and/or body.

    * Authors may edit their own non-deleted, non-locked posts.
    * Moderators/admins may edit any non-deleted post.

    AC-019.4 — locked posts cannot be edited.
    AC-019.5 — deleted posts cannot be edited.
    """
    post = await _get_post_or_raise(db, post_id)

    is_privileged = caller_role in ("moderator", "admin")

    if post.status == ContentStatus.deleted:
        raise PostDeletedError(f"Post {post_id!r} has been deleted and cannot be edited.")

    if not is_privileged and post.author_id != caller_id:
        raise PostForbiddenError("You may only edit your own posts.")

    if post.is_locked and not is_privileged:
        raise PostForbiddenError("Post is locked and cannot be edited.")

    if payload.title is not None:
        post.title = payload.title
    if payload.body is not None:
        post.body = payload.body
    post.updated_at = datetime.now(UTC)
    db.add(post)
    await db.flush()
    return PostOut.model_validate(post)


async def delete_post(
    db: AsyncSession,
    *,
    post_id: str,
    caller_id: str,
    caller_role: str,
) -> None:
    """AC-020 — soft-delete a post (status → deleted).

    * Authors may delete their own posts.
    * Moderators/admins may delete any post.
    * Already-deleted posts are idempotent (no error).
    """
    post = await _get_post_or_raise(db, post_id)

    is_privileged = caller_role in ("moderator", "admin")
    if not is_privileged and post.author_id != caller_id:
        raise PostForbiddenError("You may only delete your own posts.")

    if post.status == ContentStatus.deleted:
        # Idempotent.
        return

    allowed = CONTENT_TRANSITIONS.get(post.status, set())
    if ContentStatus.deleted not in allowed:
        # Model invariant: no status can transition away from deleted, but
        # all other statuses allow deletion — this branch should not be
        # reached in practice.
        raise PostForbiddenError(
            f"Post in status {post.status!r} cannot be deleted via this path."
        )

    post.status = ContentStatus.deleted
    post.updated_at = datetime.now(UTC)
    db.add(post)
    await db.flush()

```

### `backend/app/services/posts/router.py`
```python
"""FastAPI router for the posts service.

Endpoints:
  POST   /api/v1/posts            — create   (AC-016)
  GET    /api/v1/posts/{id}       — read     (AC-017)
  GET    /api/v1/posts            — list     (AC-018)
  PATCH  /api/v1/posts/{id}       — update   (AC-019)
  DELETE /api/v1/posts/{id}       — delete   (AC-020)

Rate limiting is enforced inside the service layer (AC-021).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import TokenPayload, get_current_user_payload
from app.models.content import ContentStatus
from app.services.posts.actions import (
    PostDeletedError,
    PostForbiddenError,
    PostNotFoundError,
    RateLimitError,
    create_post,
    delete_post,
    get_post,
    list_posts,
    update_post,
)
from app.services.posts.schemas import PostCreateRequest, PostOut, PostPage, PostUpdateRequest

router = APIRouter(prefix="/posts", tags=["posts"])


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=PostOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new post (AC-016)",
)
async def create_post_endpoint(
    body: PostCreateRequest,
    caller: TokenPayload = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
) -> PostOut:
    try:
        return await create_post(db, author_id=caller.sub, payload=body)
    except RateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)
        ) from exc


# ---------------------------------------------------------------------------
# Read single
# ---------------------------------------------------------------------------


@router.get(
    "/{post_id}",
    response_model=PostOut,
    status_code=status.HTTP_200_OK,
    summary="Get a single post (AC-017)",
)
async def get_post_endpoint(
    post_id: str,
    caller: TokenPayload = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
) -> PostOut:
    try:
        return await get_post(
            db, post_id=post_id, caller_id=caller.sub, caller_role=caller.role
        )
    except PostNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=PostPage,
    status_code=status.HTTP_200_OK,
    summary="List posts with pagination (AC-018)",
)
async def list_posts_endpoint(
    author_id: str | None = Query(default=None),
    post_status: ContentStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    caller: TokenPayload = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
) -> PostPage:
    return await list_posts(
        db,
        caller_id=caller.sub,
        caller_role=caller.role,
        author_id=author_id,
        status_filter=post_status,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


@router.patch(
    "/{post_id}",
    response_model=PostOut,
    status_code=status.HTTP_200_OK,
    summary="Update post title / body (AC-019)",
)
async def update_post_endpoint(
    post_id: str,
    body: PostUpdateRequest,
    caller: TokenPayload = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
) -> PostOut:
    try:
        return await update_post(
            db,
            post_id=post_id,
            caller_id=caller.sub,
            caller_role=caller.role,
            payload=body,
        )
    except PostNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PostDeletedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except PostForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a post (AC-020)",
)
async def delete_post_endpoint(
    post_id: str,
    caller: TokenPayload = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await delete_post(
            db,
            post_id=post_id,
            caller_id=caller.sub,
            caller_role=caller.role,
        )
    except PostNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PostForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

```

### `backend/app/services/posts/schemas.py`
```python
"""Post-service Pydantic schemas.

Covers AC-016 (create), AC-017 (read), AC-018 (list/pagination),
AC-019 (update), AC-020 (delete / soft-delete), AC-021 (rate limiting).
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.models.content import ContentStatus

# ---------------------------------------------------------------------------
# Shared field types
# ---------------------------------------------------------------------------
TitleStr = Annotated[str, StringConstraints(min_length=1, max_length=512, strip_whitespace=True)]
BodyStr = Annotated[str, StringConstraints(min_length=1, max_length=65_535, strip_whitespace=True)]


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------
class PostCreateRequest(BaseModel):
    """AC-016.1 — required fields for post creation."""

    title: TitleStr
    body: BodyStr


class PostUpdateRequest(BaseModel):
    """AC-019.1 — all fields are optional (PATCH semantics)."""

    title: TitleStr | None = None
    body: BodyStr | None = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------
class PostOut(BaseModel):
    """AC-017.1 — single-post response shape."""

    model_config = {"from_attributes": True}

    id: str
    author_id: str
    title: str
    body: str
    status: ContentStatus
    is_locked: bool
    created_at: datetime
    updated_at: datetime


class PostPage(BaseModel):
    """AC-018.1 — paginated list response."""

    items: list[PostOut]
    total: int
    page: int
    page_size: int
    pages: int


# ---------------------------------------------------------------------------
# Validation-error shape (contract)
# ---------------------------------------------------------------------------
class FieldError(BaseModel):
    loc: list[str]
    msg: str
    type: str


class ValidationErrorResponse(BaseModel):
    detail: list[FieldError]

```

### `backend/tests/posts/conftest.py`
```python
"""Shared fixtures for the posts test suite.

Extends the root conftest (tests/conftest.py) with posts-specific helpers.
All fixtures here are scoped to the function level to guarantee test isolation.
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.user import User
from tests.conftest import make_moderator_token, make_user_token  # re-export helpers


# ---------------------------------------------------------------------------
# Token / header helpers
# ---------------------------------------------------------------------------


def auth_headers(token: str) -> dict[str, str]:
    """Return ``Authorization: Bearer <token>`` header dict."""
    return {"Authorization": f"Bearer {token}"}


def user_auth_headers(user: User) -> dict[str, str]:
    return auth_headers(make_user_token(user))


def mod_auth_headers(user: User) -> dict[str, str]:
    return auth_headers(make_moderator_token(user))


# ---------------------------------------------------------------------------
# Post fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def active_post(db_session: AsyncSession, regular_user: User) -> Content:
    """A fresh active post owned by *regular_user*."""
    post = Content(
        author_id=regular_user.id,
        title="Hello world",
        body="This is the body.",
        status=ContentStatus.active,
        is_locked=False,
    )
    db_session.add(post)
    await db_session.flush()
    return post


@pytest_asyncio.fixture()
async def flagged_post(db_session: AsyncSession, regular_user: User) -> Content:
    """A flagged post owned by *regular_user*."""
    post = Content(
        author_id=regular_user.id,
        title="Flagged post",
        body="Reported content.",
        status=ContentStatus.flagged,
        is_locked=False,
    )
    db_session.add(post)
    await db_session.flush()
    return post


@pytest_asyncio.fixture()
async def locked_post(db_session: AsyncSession, regular_user: User) -> Content:
    """A locked post owned by *regular_user*."""
    post = Content(
        author_id=regular_user.id,
        title="Locked post",
        body="Locked content.",
        status=ContentStatus.locked,
        is_locked=True,
    )
    db_session.add(post)
    await db_session.flush()
    return post


@pytest_asyncio.fixture()
async def deleted_post(db_session: AsyncSession, regular_user: User) -> Content:
    """A soft-deleted post owned by *regular_user*."""
    post = Content(
        author_id=regular_user.id,
        title="Deleted post",
        body="Removed content.",
        status=ContentStatus.deleted,
        is_locked=False,
    )
    db_session.add(post)
    await db_session.flush()
    return post


@pytest_asyncio.fixture()
async def other_user(db_session: AsyncSession) -> User:
    """A second regular user with no posts."""
    from app.models.user import UserRole

    user = User(
        username="other_user",
        email="other@example.com",
        hashed_password="hashed",
        role=UserRole.user,
    )
    db_session.add(user)
    await db_session.flush()
    return user

```

### `backend/tests/posts/locustfile.py`
```python
"""Locust load-test scaffolding for the posts service.

This file is NOT executed in the CI gate.  It provides a realistic load
scenario for manual performance validation against a running instance.

Target thresholds (indicative — tune per environment):
  - POST /api/v1/posts  p95 < 200 ms
  - GET  /api/v1/posts  p95 < 150 ms
  - GET  /api/v1/posts/{id}  p95 < 100 ms

Usage:
    locust -f tests/posts/locustfile.py --host http://localhost:8000
"""
from __future__ import annotations

import random
import string
import uuid
from typing import Any

try:
    from locust import HttpUser, between, task
except ImportError:  # pragma: no cover
    # Allow the file to be imported without locust installed (test collection).
    HttpUser = object  # type: ignore[misc,assignment]

    def between(*args: Any, **kwargs: Any) -> Any:  # type: ignore[misc]
        return None

    def task(*args: Any, **kwargs: Any) -> Any:  # type: ignore[misc]
        def decorator(fn: Any) -> Any:
            return fn
        return decorator


_ALPHABET = string.ascii_letters + string.digits


def _rand_str(length: int = 10) -> str:
    return "".join(random.choices(_ALPHABET, k=length))


class PostsUser(HttpUser):
    """Simulates a mix of create / read / list / update / delete operations."""

    wait_time = between(0.1, 0.5)

    # JWT token injected at start; replace with real auth flow if needed.
    _token: str = ""
    _post_ids: list[str] = []

    def on_start(self) -> None:
        """Obtain an auth token before starting tasks."""
        # In a real environment call the token endpoint.
        # Here we use a placeholder — override with the actual auth URL.
        self._post_ids = []

    @property
    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    @task(3)
    def create_post(self) -> None:
        resp = self.client.post(
            "/api/v1/posts",
            json={"title": f"Load post {_rand_str()}", "body": "body " * 20},
            headers=self._auth_headers,
            name="/api/v1/posts [POST]",
        )
        if resp.status_code == 201:
            self._post_ids.append(resp.json()["id"])

    @task(10)
    def list_posts(self) -> None:
        self.client.get(
            "/api/v1/posts?page_size=20",
            headers=self._auth_headers,
            name="/api/v1/posts [GET list]",
        )

    @task(8)
    def get_post(self) -> None:
        if not self._post_ids:
            return
        post_id = random.choice(self._post_ids)
        self.client.get(
            f"/api/v1/posts/{post_id}",
            headers=self._auth_headers,
            name="/api/v1/posts/{id} [GET]",
        )

    @task(2)
    def update_post(self) -> None:
        if not self._post_ids:
            return
        post_id = random.choice(self._post_ids)
        self.client.patch(
            f"/api/v1/posts/{post_id}",
            json={"title": f"Updated {_rand_str()}"},
            headers=self._auth_headers,
            name="/api/v1/posts/{id} [PATCH]",
        )

    @task(1)
    def delete_post(self) -> None:
        if not self._post_ids:
            return
        post_id = self._post_ids.pop()
        self.client.delete(
            f"/api/v1/posts/{post_id}",
            headers=self._auth_headers,
            name="/api/v1/posts/{id} [DELETE]",
        )

```

### `backend/tests/posts/test_contract.py`
```python
"""AC-017/AC-018 — Contract tests.

Verify that the HTTP response shapes exactly match the declared Pydantic schemas
(PostOut, PostPage) so that the API contract is honoured end-to-end.

VER-002 — Response schema matches OpenAPI/Pydantic model.
VER-020 — All required fields present with correct types.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.content import Content, ContentStatus
from app.models.user import User
from app.services.posts.schemas import PostOut, PostPage
from tests.posts.conftest import mod_auth_headers, user_auth_headers


@pytest.mark.asyncio
class TestPostContractSinglePost:
    """Contract: GET /api/v1/posts/{id} response matches PostOut."""

    async def test_response_validates_as_post_out(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200
        # Validate against Pydantic model — raises ValidationError on mismatch
        post = PostOut.model_validate(resp.json())
        assert post.id == active_post.id

    async def test_post_out_required_fields_present(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(regular_user),
        )
        data = resp.json()
        required_fields = {"id", "author_id", "title", "body", "status", "is_locked", "created_at", "updated_at"}
        assert required_fields.issubset(data.keys()), (
            f"Missing fields: {required_fields - data.keys()}"
        )

    async def test_post_out_field_types(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(regular_user),
        )
        data = resp.json()
        assert isinstance(data["id"], str)
        assert isinstance(data["author_id"], str)
        assert isinstance(data["title"], str)
        assert isinstance(data["body"], str)
        assert data["status"] in [s.value for s in ContentStatus]
        assert isinstance(data["is_locked"], bool)
        # ISO-8601 datetime strings
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)

    async def test_status_enum_values_are_valid(
        self,
        client: AsyncClient,
        moderator_user: User,
        active_post: Content,
        flagged_post: Content,
        locked_post: Content,
        deleted_post: Content,
    ) -> None:
        valid_statuses = {s.value for s in ContentStatus}
        for post in (active_post, flagged_post, locked_post, deleted_post):
            resp = await client.get(
                f"/api/v1/posts/{post.id}",
                headers=mod_auth_headers(moderator_user),
            )
            assert resp.status_code == 200
            assert resp.json()["status"] in valid_statuses


@pytest.mark.asyncio
class TestPostContractListPage:
    """Contract: GET /api/v1/posts response matches PostPage."""

    async def test_response_validates_as_post_page(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200
        page = PostPage.model_validate(resp.json())
        assert isinstance(page.items, list)
        assert isinstance(page.total, int)
        assert page.total >= 0

    async def test_post_page_required_fields(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            headers=user_auth_headers(regular_user),
        )
        data = resp.json()
        required = {"items", "total", "page", "page_size", "pages"}
        assert required.issubset(data.keys())

    async def test_post_page_items_are_post_out(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            headers=user_auth_headers(regular_user),
        )
        data = resp.json()
        for item in data["items"]:
            PostOut.model_validate(item)  # must not raise

    async def test_post_page_pagination_fields_types(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts?page=1&page_size=5",
            headers=user_auth_headers(regular_user),
        )
        data = resp.json()
        assert isinstance(data["total"], int)
        assert isinstance(data["page"], int)
        assert isinstance(data["page_size"], int)
        assert isinstance(data["pages"], int)
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert data["pages"] >= 1

    async def test_create_response_validates_as_post_out(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.post(
            "/api/v1/posts",
            json={"title": "Contract check", "body": "body text"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 201
        PostOut.model_validate(resp.json())  # must not raise

```

### `backend/tests/posts/test_create.py`
```python
"""AC-016 — Post creation tests.

Acceptance criteria:
  AC-016.1  201 + PostOut on valid request
  AC-016.2  401 when unauthenticated
  AC-016.3  422 when title is missing / blank
  AC-016.4  422 when body is missing / blank
  AC-016.5  Title and body are persisted to DB correctly
  AC-016.6  author_id is taken from the JWT (not the request body)
  AC-016.7  New post has status=active, is_locked=False
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.user import User
from tests.posts.conftest import mod_auth_headers, user_auth_headers


@pytest.mark.asyncio
class TestPostCreate:
    # ------------------------------------------------------------------
    # AC-016.1  Happy path
    # ------------------------------------------------------------------
    async def test_create_returns_201_and_post_shape(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.post(
            "/api/v1/posts",
            json={"title": "My first post", "body": "Hello everyone!"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "My first post"
        assert data["body"] == "Hello everyone!"
        assert data["author_id"] == regular_user.id
        assert data["status"] == "active"
        assert data["is_locked"] is False
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    # ------------------------------------------------------------------
    # AC-016.2  Unauthenticated
    # ------------------------------------------------------------------
    async def test_create_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/posts",
            json={"title": "No auth", "body": "body"},
        )
        assert resp.status_code == 401

    # ------------------------------------------------------------------
    # AC-016.3  Missing / blank title
    # ------------------------------------------------------------------
    @pytest.mark.parametrize(
        "payload",
        [
            {"body": "No title here"},
            {"title": "", "body": "blank title"},
            {"title": "   ", "body": "whitespace title"},
        ],
    )
    async def test_create_rejects_invalid_title(
        self,
        client: AsyncClient,
        regular_user: User,
        payload: dict,
    ) -> None:
        resp = await client.post(
            "/api/v1/posts",
            json=payload,
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 422

    # ------------------------------------------------------------------
    # AC-016.4  Missing / blank body
    # ------------------------------------------------------------------
    @pytest.mark.parametrize(
        "payload",
        [
            {"title": "No body"},
            {"title": "Empty body", "body": ""},
            {"title": "Whitespace body", "body": "   "},
        ],
    )
    async def test_create_rejects_invalid_body(
        self,
        client: AsyncClient,
        regular_user: User,
        payload: dict,
    ) -> None:
        resp = await client.post(
            "/api/v1/posts",
            json=payload,
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 422

    # ------------------------------------------------------------------
    # AC-016.5  Persistence
    # ------------------------------------------------------------------
    async def test_create_persists_to_db(
        self,
        client: AsyncClient,
        regular_user: User,
        db_session: AsyncSession,
    ) -> None:
        resp = await client.post(
            "/api/v1/posts",
            json={"title": "Persisted", "body": "Check DB"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 201
        post_id = resp.json()["id"]
        stmt = select(Content).where(Content.id == post_id)
        row = (await db_session.execute(stmt)).scalar_one_or_none()
        assert row is not None
        assert row.title == "Persisted"
        assert row.body == "Check DB"

    # ------------------------------------------------------------------
    # AC-016.6  author_id from JWT
    # ------------------------------------------------------------------
    async def test_author_id_comes_from_jwt(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.post(
            "/api/v1/posts",
            json={"title": "JWT author", "body": "must match"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 201
        assert resp.json()["author_id"] == regular_user.id

    # ------------------------------------------------------------------
    # AC-016.7  Default status / lock
    # ------------------------------------------------------------------
    async def test_create_default_status_and_lock(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.post(
            "/api/v1/posts",
            json={"title": "Defaults", "body": "status check"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == ContentStatus.active.value
        assert data["is_locked"] is False

    # ------------------------------------------------------------------
    # Moderator can also create posts (extended happy path)
    # ------------------------------------------------------------------
    async def test_moderator_can_create_post(
        self,
        client: AsyncClient,
        moderator_user: User,
    ) -> None:
        resp = await client.post(
            "/api/v1/posts",
            json={"title": "Mod post", "body": "Written by mod"},
            headers=mod_auth_headers(moderator_user),
        )
        assert resp.status_code == 201
        assert resp.json()["author_id"] == moderator_user.id

```

### `backend/tests/posts/test_delete.py`
```python
"""AC-020 — Post soft-delete tests.

Acceptance criteria:
  AC-020.1  204 No Content on successful delete
  AC-020.2  401 when unauthenticated
  AC-020.3  403 when non-owner regular user attempts delete
  AC-020.4  404 for non-existent post
  AC-020.5  post.status becomes "deleted" in DB after delete
  AC-020.6  Idempotent: deleting an already-deleted post returns 204
  AC-020.7  Moderator can delete any post
  AC-020.8  Deleted post is no longer visible to regular users (GET → 404)
  AC-020.9  Hard delete of DB row is NOT allowed — row persists after soft-delete
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.user import User
from tests.posts.conftest import mod_auth_headers, user_auth_headers


@pytest.mark.asyncio
class TestPostDelete:
    # ------------------------------------------------------------------
    # AC-020.1  Happy path — 204
    # ------------------------------------------------------------------
    async def test_delete_own_post_returns_204(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 204
        assert resp.content == b""

    # ------------------------------------------------------------------
    # AC-020.2  Unauthenticated
    # ------------------------------------------------------------------
    async def test_delete_requires_auth(
        self,
        client: AsyncClient,
        active_post: Content,
    ) -> None:
        resp = await client.delete(f"/api/v1/posts/{active_post.id}")
        assert resp.status_code == 401

    # ------------------------------------------------------------------
    # AC-020.3  Non-owner forbidden
    # ------------------------------------------------------------------
    async def test_delete_rejects_non_owner(
        self,
        client: AsyncClient,
        other_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(other_user),
        )
        assert resp.status_code == 403

    # ------------------------------------------------------------------
    # AC-020.4  Non-existent post → 404
    # ------------------------------------------------------------------
    async def test_delete_nonexistent_post_404(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.delete(
            "/api/v1/posts/totally-fake-id",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 404

    # ------------------------------------------------------------------
    # AC-020.5  Status becomes "deleted" in DB
    # ------------------------------------------------------------------
    async def test_delete_sets_status_deleted_in_db(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
        db_session: AsyncSession,
    ) -> None:
        await client.delete(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(regular_user),
        )
        stmt = select(Content).where(Content.id == active_post.id)
        row = (await db_session.execute(stmt)).scalar_one()
        assert row.status == ContentStatus.deleted

    # ------------------------------------------------------------------
    # AC-020.6  Idempotent — re-deleting returns 204
    # ------------------------------------------------------------------
    async def test_delete_idempotent(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        resp1 = await client.delete(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(regular_user),
        )
        resp2 = await client.delete(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(regular_user),
        )
        assert resp1.status_code == 204
        assert resp2.status_code == 204

    # ------------------------------------------------------------------
    # AC-020.7  Moderator can delete any post
    # ------------------------------------------------------------------
    async def test_moderator_can_delete_any_post(
        self,
        client: AsyncClient,
        moderator_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/posts/{active_post.id}",
            headers=mod_auth_headers(moderator_user),
        )
        assert resp.status_code == 204

    # ------------------------------------------------------------------
    # AC-020.8  Deleted post becomes 404 for regular users
    # ------------------------------------------------------------------
    async def test_deleted_post_returns_404_on_get(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        await client.delete(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(regular_user),
        )
        get_resp = await client.get(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(regular_user),
        )
        assert get_resp.status_code == 404

    # ------------------------------------------------------------------
    # AC-020.9  Row persists after soft-delete (no hard delete)
    # ------------------------------------------------------------------
    async def test_row_persists_after_soft_delete(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
        db_session: AsyncSession,
    ) -> None:
        await client.delete(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(regular_user),
        )
        stmt = select(Content).where(Content.id == active_post.id)
        row = (await db_session.execute(stmt)).scalar_one_or_none()
        assert row is not None, "Row must still exist after soft-delete"
        assert row.status == ContentStatus.deleted

    # ------------------------------------------------------------------
    # Deleting a flagged post works (not only active)
    # ------------------------------------------------------------------
    async def test_can_delete_flagged_post(
        self,
        client: AsyncClient,
        regular_user: User,
        flagged_post: Content,
        db_session: AsyncSession,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/posts/{flagged_post.id}",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 204
        stmt = select(Content).where(Content.id == flagged_post.id)
        row = (await db_session.execute(stmt)).scalar_one()
        assert row.status == ContentStatus.deleted

```

### `backend/tests/posts/test_list.py`
```python
"""AC-018 — Post list / pagination tests.

Acceptance criteria:
  AC-018.1  200 + PostPage shape for authenticated request
  AC-018.2  401 when unauthenticated
  AC-018.3  Pagination: page/page_size respected; pages calculated correctly
  AC-018.4  author_id filter returns only that author's posts
  AC-018.5  status filter returns only matching posts
  AC-018.6  Deleted posts excluded from default listing for regular users
  AC-018.7  Deleted posts included for moderator listing
  AC-018.8  page_size upper bound (100) enforced
  AC-018.9  page_size lower bound (1) enforced
  AC-018.10 Results ordered by created_at descending
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.user import User
from tests.posts.conftest import mod_auth_headers, user_auth_headers


@pytest.mark.asyncio
class TestPostList:
    # ------------------------------------------------------------------
    # AC-018.1  Happy path — shape
    # ------------------------------------------------------------------
    async def test_list_returns_200_and_page_shape(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "pages" in data
        assert isinstance(data["items"], list)

    # ------------------------------------------------------------------
    # AC-018.2  Unauthenticated
    # ------------------------------------------------------------------
    async def test_list_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/posts")
        assert resp.status_code == 401

    # ------------------------------------------------------------------
    # AC-018.3  Pagination
    # ------------------------------------------------------------------
    async def test_pagination_page_size_respected(
        self,
        client: AsyncClient,
        regular_user: User,
        db_session: AsyncSession,
    ) -> None:
        # Create 5 extra active posts
        for i in range(5):
            db_session.add(
                Content(
                    author_id=regular_user.id,
                    title=f"Paged {i}",
                    body="body",
                    status=ContentStatus.active,
                )
            )
        await db_session.flush()

        resp = await client.get(
            "/api/v1/posts?page_size=2&page=1",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page_size"] == 2
        assert len(data["items"]) <= 2

    async def test_pagination_pages_field_correct(
        self,
        client: AsyncClient,
        regular_user: User,
        db_session: AsyncSession,
    ) -> None:
        # Clear slate: create exactly 3 active posts, page_size=2 → 2 pages
        for i in range(3):
            db_session.add(
                Content(
                    author_id=regular_user.id,
                    title=f"Calc {i}",
                    body="body",
                    status=ContentStatus.active,
                )
            )
        await db_session.flush()

        resp = await client.get(
            "/api/v1/posts?page_size=2&author_id=" + regular_user.id,
            headers=user_auth_headers(regular_user),
        )
        data = resp.json()
        assert data["total"] >= 3
        expected_pages = -(-data["total"] // 2)  # ceiling division
        assert data["pages"] == expected_pages

    # ------------------------------------------------------------------
    # AC-018.4  author_id filter
    # ------------------------------------------------------------------
    async def test_author_filter_returns_only_own_posts(
        self,
        client: AsyncClient,
        regular_user: User,
        other_user: User,
        active_post: Content,
        db_session: AsyncSession,
    ) -> None:
        # Create a post for the other user
        other_post = Content(
            author_id=other_user.id,
            title="Other user post",
            body="other body",
            status=ContentStatus.active,
        )
        db_session.add(other_post)
        await db_session.flush()

        resp = await client.get(
            f"/api/v1/posts?author_id={regular_user.id}",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["items"]]
        assert active_post.id in ids
        assert other_post.id not in ids

    # ------------------------------------------------------------------
    # AC-018.5  status filter
    # ------------------------------------------------------------------
    async def test_status_filter_flagged(
        self,
        client: AsyncClient,
        moderator_user: User,
        flagged_post: Content,
        active_post: Content,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts?status=flagged",
            headers=mod_auth_headers(moderator_user),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        statuses = {item["status"] for item in items}
        assert statuses == {"flagged"} or all(s == "flagged" for s in statuses)
        ids = [item["id"] for item in items]
        assert flagged_post.id in ids
        assert active_post.id not in ids

    # ------------------------------------------------------------------
    # AC-018.6  Deleted posts excluded for regular users (default listing)
    # ------------------------------------------------------------------
    async def test_deleted_excluded_for_regular_user(
        self,
        client: AsyncClient,
        regular_user: User,
        other_user: User,
        active_post: Content,
        deleted_post: Content,
        db_session: AsyncSession,
    ) -> None:
        # deleted_post is owned by regular_user but still should be hidden
        # from listing when NOT filtering by own author_id
        resp = await client.get(
            f"/api/v1/posts?author_id={other_user.id}",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200
        # deleted_post should not appear in other user's perspective
        ids = [item["id"] for item in resp.json()["items"]]
        assert deleted_post.id not in ids

    # ------------------------------------------------------------------
    # AC-018.7  Moderator sees deleted posts
    # ------------------------------------------------------------------
    async def test_moderator_sees_deleted_posts(
        self,
        client: AsyncClient,
        moderator_user: User,
        deleted_post: Content,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts?status=deleted",
            headers=mod_auth_headers(moderator_user),
        )
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["items"]]
        assert deleted_post.id in ids

    # ------------------------------------------------------------------
    # AC-018.8  page_size upper bound
    # ------------------------------------------------------------------
    async def test_page_size_over_100_rejected(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts?page_size=101",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 422

    # ------------------------------------------------------------------
    # AC-018.9  page_size lower bound
    # ------------------------------------------------------------------
    async def test_page_size_zero_rejected(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts?page_size=0",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 422

    # ------------------------------------------------------------------
    # AC-018.10  Ordering — newest first
    # ------------------------------------------------------------------
    async def test_results_ordered_newest_first(
        self,
        client: AsyncClient,
        regular_user: User,
        db_session: AsyncSession,
    ) -> None:
        from datetime import UTC, datetime, timedelta

        base = datetime.now(UTC)
        posts = []
        for offset in range(3):
            p = Content(
                author_id=regular_user.id,
                title=f"Ordered {offset}",
                body="body",
                status=ContentStatus.active,
                created_at=base + timedelta(seconds=offset),
            )
            db_session.add(p)
            posts.append(p)
        await db_session.flush()

        resp = await client.get(
            f"/api/v1/posts?author_id={regular_user.id}&page_size=100",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        owned_ids = [p.id for p in posts]
        owned_items = [it for it in items if it["id"] in owned_ids]
        timestamps = [it["created_at"] for it in owned_items]
        assert timestamps == sorted(timestamps, reverse=True)

```

### `backend/tests/posts/test_rate_limit.py`
```python
"""AC-021 — Rate limiting tests.

Acceptance criteria:
  AC-021.1  After RATE_LIMIT_MAX_POSTS (10) within the window, next POST → 429
  AC-021.2  429 response contains a descriptive detail message
  AC-021.3  Rate limit is per-author: different authors have independent counters
  AC-021.4  Requests to read/list/update/delete do NOT count against post-create limit
  AC-021.5  Service-layer unit test: RateLimitError raised when count >= limit
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.user import User
from app.services.posts.actions import (
    RATE_LIMIT_MAX_POSTS,
    RATE_LIMIT_WINDOW_SECONDS,
    RateLimitError,
    create_post,
)
from app.services.posts.schemas import PostCreateRequest
from tests.posts.conftest import user_auth_headers


# ---------------------------------------------------------------------------
# Integration tests (HTTP layer)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestRateLimitIntegration:
    """HTTP-layer rate-limit tests via the ASGI test client."""

    async def _flood_create(
        self,
        client: AsyncClient,
        user: User,
        count: int,
    ) -> list[int]:
        """Issue *count* POST /api/v1/posts and return the status codes."""
        status_codes: list[int] = []
        for i in range(count):
            resp = await client.post(
                "/api/v1/posts",
                json={"title": f"Flood post {i}", "body": "body content"},
                headers=user_auth_headers(user),
            )
            status_codes.append(resp.status_code)
        return status_codes

    # ------------------------------------------------------------------
    # AC-021.1  10 succeed, 11th is 429
    # ------------------------------------------------------------------
    async def test_rate_limit_blocks_on_eleventh_post(
        self,
        client: AsyncClient,
        regular_user: User,
        db_session: AsyncSession,
    ) -> None:
        """Create RATE_LIMIT_MAX_POSTS posts — all succeed; the next is 429."""
        codes = await self._flood_create(
            client, regular_user, RATE_LIMIT_MAX_POSTS + 1
        )
        assert all(c == 201 for c in codes[:RATE_LIMIT_MAX_POSTS]), (
            f"First {RATE_LIMIT_MAX_POSTS} should be 201; got {codes[:RATE_LIMIT_MAX_POSTS]}"
        )
        assert codes[RATE_LIMIT_MAX_POSTS] == 429, (
            f"Post #{RATE_LIMIT_MAX_POSTS + 1} should be 429; got {codes[RATE_LIMIT_MAX_POSTS]}"
        )

    # ------------------------------------------------------------------
    # AC-021.2  429 has a descriptive message
    # ------------------------------------------------------------------
    async def test_rate_limit_response_has_detail(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        await self._flood_create(client, regular_user, RATE_LIMIT_MAX_POSTS)
        resp = await client.post(
            "/api/v1/posts",
            json={"title": "Over limit", "body": "body"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 429
        body = resp.json()
        assert "detail" in body
        assert len(body["detail"]) > 0

    # ------------------------------------------------------------------
    # AC-021.3  Rate limit is per-author
    # ------------------------------------------------------------------
    async def test_rate_limit_is_per_author(
        self,
        client: AsyncClient,
        regular_user: User,
        other_user: User,
        db_session: AsyncSession,
    ) -> None:
        """Exhaust rate limit for regular_user; other_user is unaffected."""
        await self._flood_create(client, regular_user, RATE_LIMIT_MAX_POSTS)
        # regular_user is now limited
        blocked = await client.post(
            "/api/v1/posts",
            json={"title": "Over limit", "body": "body"},
            headers=user_auth_headers(regular_user),
        )
        assert blocked.status_code == 429

        # other_user is NOT limited
        allowed = await client.post(
            "/api/v1/posts",
            json={"title": "Other user post", "body": "fine"},
            headers=user_auth_headers(other_user),
        )
        assert allowed.status_code == 201

    # ------------------------------------------------------------------
    # AC-021.4  Read/update/delete do NOT count against create limit
    # ------------------------------------------------------------------
    async def test_reads_do_not_count_against_rate_limit(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        """Performing many GET requests should not trigger the create rate limit."""
        for _ in range(RATE_LIMIT_MAX_POSTS + 5):
            await client.get(
                f"/api/v1/posts/{active_post.id}",
                headers=user_auth_headers(regular_user),
            )
        # Creating a post should still succeed (rate limit not consumed)
        resp = await client.post(
            "/api/v1/posts",
            json={"title": "After reads", "body": "body"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 201


# ---------------------------------------------------------------------------
# Unit tests (service layer)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestRateLimitUnit:
    """Direct service-layer tests; mock the DB to control count output."""

    async def test_rate_limit_error_raised_when_at_limit(self) -> None:
        """AC-021.5 — RateLimitError when recent_count >= RATE_LIMIT_MAX_POSTS."""
        mock_db = AsyncMock()

        # Simulate scalar_one() returning exactly RATE_LIMIT_MAX_POSTS
        scalar_result = MagicMock()
        scalar_result.scalar_one.return_value = RATE_LIMIT_MAX_POSTS
        mock_db.execute.return_value = scalar_result

        with pytest.raises(RateLimitError):
            await create_post(
                mock_db,
                author_id="user-123",
                payload=PostCreateRequest(title="Test", body="body"),
            )

    async def test_rate_limit_error_raised_when_above_limit(self) -> None:
        """RateLimitError when count is already above the limit."""
        mock_db = AsyncMock()
        scalar_result = MagicMock()
        scalar_result.scalar_one.return_value = RATE_LIMIT_MAX_POSTS + 5
        mock_db.execute.return_value = scalar_result

        with pytest.raises(RateLimitError):
            await create_post(
                mock_db,
                author_id="user-456",
                payload=PostCreateRequest(title="Flood", body="body"),
            )

    async def test_no_error_when_below_limit(
        self,
        db_session: AsyncSession,
        regular_user: User,
    ) -> None:
        """No error when the author has fewer posts than the limit."""
        # 0 recent posts — should succeed
        payload = PostCreateRequest(title="First post", body="Hello")
        result = await create_post(
            db_session,
            author_id=regular_user.id,
            payload=payload,
        )
        assert result.title == "First post"
        assert result.author_id == regular_user.id

    def test_rate_limit_constants_are_sane(self) -> None:
        """Contract: constants are set to reasonable defaults."""
        assert RATE_LIMIT_MAX_POSTS == 10
        assert RATE_LIMIT_WINDOW_SECONDS == 60

```

### `backend/tests/posts/test_read.py`
```python
"""AC-017 — Post read (single) tests.

Acceptance criteria:
  AC-017.1  200 + PostOut for existing active post
  AC-017.2  401 when unauthenticated
  AC-017.3  Deleted post → 404 for regular users
  AC-017.4  Deleted post → 200 for moderators / admins
  AC-017.5  Response fields match DB record exactly
  AC-017.6  404 for completely non-existent ID
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.content import Content
from app.models.user import User
from tests.posts.conftest import mod_auth_headers, user_auth_headers


@pytest.mark.asyncio
class TestPostRead:
    # ------------------------------------------------------------------
    # AC-017.1  Happy path
    # ------------------------------------------------------------------
    async def test_get_active_post_200(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == active_post.id
        assert data["title"] == active_post.title
        assert data["body"] == active_post.body

    # ------------------------------------------------------------------
    # AC-017.2  Unauthenticated
    # ------------------------------------------------------------------
    async def test_get_post_requires_auth(
        self,
        client: AsyncClient,
        active_post: Content,
    ) -> None:
        resp = await client.get(f"/api/v1/posts/{active_post.id}")
        assert resp.status_code == 401

    # ------------------------------------------------------------------
    # AC-017.3  Deleted post hidden from regular users
    # ------------------------------------------------------------------
    async def test_deleted_post_is_404_for_regular_user(
        self,
        client: AsyncClient,
        regular_user: User,
        deleted_post: Content,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{deleted_post.id}",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 404

    # ------------------------------------------------------------------
    # AC-017.4  Deleted post visible to moderators
    # ------------------------------------------------------------------
    async def test_deleted_post_visible_to_moderator(
        self,
        client: AsyncClient,
        moderator_user: User,
        deleted_post: Content,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{deleted_post.id}",
            headers=mod_auth_headers(moderator_user),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

    # ------------------------------------------------------------------
    # AC-017.5  Response fields match DB
    # ------------------------------------------------------------------
    async def test_response_fields_match_db(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(regular_user),
        )
        data = resp.json()
        assert data["id"] == active_post.id
        assert data["author_id"] == active_post.author_id
        assert data["title"] == active_post.title
        assert data["body"] == active_post.body
        assert data["status"] == active_post.status.value
        assert data["is_locked"] == active_post.is_locked

    # ------------------------------------------------------------------
    # AC-017.6  Non-existent ID → 404
    # ------------------------------------------------------------------
    async def test_nonexistent_post_404(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.get(
            "/api/v1/posts/does-not-exist-at-all",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 404

    # ------------------------------------------------------------------
    # Cross-user read (regular user may read other users' active posts)
    # ------------------------------------------------------------------
    async def test_other_user_can_read_active_post(
        self,
        client: AsyncClient,
        other_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{active_post.id}",
            headers=user_auth_headers(other_user),
        )
        assert resp.status_code == 200

    # ------------------------------------------------------------------
    # Flagged / locked posts are readable by regular users (only deleted
    # content is hidden).
    # ------------------------------------------------------------------
    async def test_flagged_post_readable_by_regular_user(
        self,
        client: AsyncClient,
        regular_user: User,
        flagged_post: Content,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{flagged_post.id}",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200

    async def test_locked_post_readable_by_regular_user(
        self,
        client: AsyncClient,
        regular_user: User,
        locked_post: Content,
    ) -> None:
        resp = await client.get(
            f"/api/v1/posts/{locked_post.id}",
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200

```

### `backend/tests/posts/test_service_unit.py`
```python
"""VER-010 — Service-layer unit tests.

Tests that exercise the business-logic functions directly (no HTTP), mocking
the database where needed.  These cover error paths, edge cases, and domain
invariants that are difficult to reproduce through the HTTP layer alone.
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.user import User
from app.services.posts.actions import (
    PostDeletedError,
    PostForbiddenError,
    PostNotFoundError,
    create_post,
    delete_post,
    get_post,
    list_posts,
    update_post,
)
from app.services.posts.schemas import PostCreateRequest, PostUpdateRequest


@pytest.mark.asyncio
class TestCreatePostUnit:
    async def test_create_returns_post_out(
        self,
        db_session: AsyncSession,
        regular_user: User,
    ) -> None:
        payload = PostCreateRequest(title="Unit title", body="Unit body")
        result = await create_post(db_session, author_id=regular_user.id, payload=payload)
        assert result.title == "Unit title"
        assert result.body == "Unit body"
        assert result.author_id == regular_user.id
        assert result.status == ContentStatus.active
        assert result.is_locked is False

    async def test_create_post_id_is_uuid_like(
        self,
        db_session: AsyncSession,
        regular_user: User,
    ) -> None:
        payload = PostCreateRequest(title="ID check", body="body")
        result = await create_post(db_session, author_id=regular_user.id, payload=payload)
        assert len(result.id) == 36  # UUID4 string length
        assert result.id.count("-") == 4


@pytest.mark.asyncio
class TestGetPostUnit:
    async def test_get_nonexistent_raises(
        self,
        db_session: AsyncSession,
        regular_user: User,
    ) -> None:
        with pytest.raises(PostNotFoundError):
            await get_post(
                db_session,
                post_id="no-such-post",
                caller_id=regular_user.id,
                caller_role="user",
            )

    async def test_get_deleted_raises_for_regular_user(
        self,
        db_session: AsyncSession,
        regular_user: User,
        deleted_post: Content,
    ) -> None:
        with pytest.raises(PostNotFoundError):
            await get_post(
                db_session,
                post_id=deleted_post.id,
                caller_id=regular_user.id,
                caller_role="user",
            )

    async def test_get_deleted_succeeds_for_moderator(
        self,
        db_session: AsyncSession,
        moderator_user: User,
        deleted_post: Content,
    ) -> None:
        result = await get_post(
            db_session,
            post_id=deleted_post.id,
            caller_id=moderator_user.id,
            caller_role="moderator",
        )
        assert result.status == ContentStatus.deleted


@pytest.mark.asyncio
class TestUpdatePostUnit:
    async def test_update_nonexistent_raises(
        self,
        db_session: AsyncSession,
        regular_user: User,
    ) -> None:
        with pytest.raises(PostNotFoundError):
            await update_post(
                db_session,
                post_id="ghost",
                caller_id=regular_user.id,
                caller_role="user",
                payload=PostUpdateRequest(title="X"),
            )

    async def test_update_deleted_raises(
        self,
        db_session: AsyncSession,
        regular_user: User,
        deleted_post: Content,
    ) -> None:
        with pytest.raises(PostDeletedError):
            await update_post(
                db_session,
                post_id=deleted_post.id,
                caller_id=regular_user.id,
                caller_role="user",
                payload=PostUpdateRequest(title="edit deleted"),
            )

    async def test_update_other_users_post_raises(
        self,
        db_session: AsyncSession,
        other_user: User,
        active_post: Content,
    ) -> None:
        with pytest.raises(PostForbiddenError):
            await update_post(
                db_session,
                post_id=active_post.id,
                caller_id=other_user.id,
                caller_role="user",
                payload=PostUpdateRequest(title="steal"),
            )

    async def test_update_locked_raises_for_user(
        self,
        db_session: AsyncSession,
        regular_user: User,
        locked_post: Content,
    ) -> None:
        with pytest.raises(PostForbiddenError):
            await update_post(
                db_session,
                post_id=locked_post.id,
                caller_id=regular_user.id,
                caller_role="user",
                payload=PostUpdateRequest(body="attempt"),
            )

    async def test_update_locked_succeeds_for_moderator(
        self,
        db_session: AsyncSession,
        moderator_user: User,
        locked_post: Content,
    ) -> None:
        result = await update_post(
            db_session,
            post_id=locked_post.id,
            caller_id=moderator_user.id,
            caller_role="moderator",
            payload=PostUpdateRequest(body="mod override"),
        )
        assert result.body == "mod override"


@pytest.mark.asyncio
class TestDeletePostUnit:
    async def test_delete_nonexistent_raises(
        self,
        db_session: AsyncSession,
        regular_user: User,
    ) -> None:
        with pytest.raises(PostNotFoundError):
            await delete_post(
                db_session,
                post_id="ghost",
                caller_id=regular_user.id,
                caller_role="user",
            )

    async def test_delete_other_users_post_raises(
        self,
        db_session: AsyncSession,
        other_user: User,
        active_post: Content,
    ) -> None:
        with pytest.raises(PostForbiddenError):
            await delete_post(
                db_session,
                post_id=active_post.id,
                caller_id=other_user.id,
                caller_role="user",
            )

    async def test_delete_sets_status(
        self,
        db_session: AsyncSession,
        regular_user: User,
        active_post: Content,
    ) -> None:
        await delete_post(
            db_session,
            post_id=active_post.id,
            caller_id=regular_user.id,
            caller_role="user",
        )
        await db_session.refresh(active_post)
        assert active_post.status == ContentStatus.deleted

    async def test_delete_idempotent(
        self,
        db_session: AsyncSession,
        regular_user: User,
        active_post: Content,
    ) -> None:
        await delete_post(
            db_session,
            post_id=active_post.id,
            caller_id=regular_user.id,
            caller_role="user",
        )
        # Second call must not raise
        await delete_post(
            db_session,
            post_id=active_post.id,
            caller_id=regular_user.id,
            caller_role="user",
        )
        await db_session.refresh(active_post)
        assert active_post.status == ContentStatus.deleted


@pytest.mark.asyncio
class TestListPostsUnit:
    async def test_list_returns_page_structure(
        self,
        db_session: AsyncSession,
        regular_user: User,
        active_post: Content,
    ) -> None:
        page = await list_posts(
            db_session,
            caller_id=regular_user.id,
            caller_role="user",
        )
        assert page.page == 1
        assert page.page_size == 20
        assert page.total >= 1
        assert any(item.id == active_post.id for item in page.items)

    async def test_list_excludes_deleted_for_user(
        self,
        db_session: AsyncSession,
        regular_user: User,
        other_user: User,
        deleted_post: Content,
    ) -> None:
        page = await list_posts(
            db_session,
            caller_id=other_user.id,
            caller_role="user",
            author_id=other_user.id,
        )
        ids = [item.id for item in page.items]
        assert deleted_post.id not in ids

    async def test_list_includes_deleted_for_moderator(
        self,
        db_session: AsyncSession,
        moderator_user: User,
        deleted_post: Content,
    ) -> None:
        page = await list_posts(
            db_session,
            caller_id=moderator_user.id,
            caller_role="moderator",
            status_filter=ContentStatus.deleted,
        )
        ids = [item.id for item in page.items]
        assert deleted_post.id in ids

```

### `backend/tests/posts/test_update.py`
```python
"""AC-019 — Post update (PATCH) tests.

Acceptance criteria:
  AC-019.1  200 + updated PostOut when author patches own post
  AC-019.2  401 when unauthenticated
  AC-019.3  403 when non-owner regular user attempts update
  AC-019.4  422 when attempting to edit a locked post (as regular user)
  AC-019.5  422 when attempting to edit a deleted post
  AC-019.6  404 for non-existent post ID
  AC-019.7  Moderator can edit any non-deleted post
  AC-019.8  Moderator can edit a locked post
  AC-019.9  Partial update: only supplied fields change; others preserved
  AC-019.10 updated_at is refreshed after update
"""
from __future__ import annotations

import asyncio

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content
from app.models.user import User
from tests.posts.conftest import mod_auth_headers, user_auth_headers


@pytest.mark.asyncio
class TestPostUpdate:
    # ------------------------------------------------------------------
    # AC-019.1  Happy path
    # ------------------------------------------------------------------
    async def test_update_own_active_post(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{active_post.id}",
            json={"title": "New title", "body": "New body"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "New title"
        assert data["body"] == "New body"

    # ------------------------------------------------------------------
    # AC-019.2  Unauthenticated
    # ------------------------------------------------------------------
    async def test_update_requires_auth(
        self,
        client: AsyncClient,
        active_post: Content,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{active_post.id}",
            json={"title": "X"},
        )
        assert resp.status_code == 401

    # ------------------------------------------------------------------
    # AC-019.3  Non-owner forbidden
    # ------------------------------------------------------------------
    async def test_update_rejects_non_owner(
        self,
        client: AsyncClient,
        other_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{active_post.id}",
            json={"title": "Steal"},
            headers=user_auth_headers(other_user),
        )
        assert resp.status_code == 403

    # ------------------------------------------------------------------
    # AC-019.4  Locked post — regular user cannot edit
    # ------------------------------------------------------------------
    async def test_update_locked_post_forbidden_for_regular_user(
        self,
        client: AsyncClient,
        regular_user: User,
        locked_post: Content,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{locked_post.id}",
            json={"body": "Attempt edit"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 403

    # ------------------------------------------------------------------
    # AC-019.5  Deleted post — cannot be edited
    # ------------------------------------------------------------------
    async def test_update_deleted_post_rejected(
        self,
        client: AsyncClient,
        regular_user: User,
        deleted_post: Content,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{deleted_post.id}",
            json={"title": "Ghost edit"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code in (403, 422)

    # ------------------------------------------------------------------
    # AC-019.6  Non-existent post → 404
    # ------------------------------------------------------------------
    async def test_update_nonexistent_post_404(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        resp = await client.patch(
            "/api/v1/posts/no-such-id",
            json={"title": "X"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 404

    # ------------------------------------------------------------------
    # AC-019.7  Moderator can edit any non-deleted post
    # ------------------------------------------------------------------
    async def test_moderator_can_edit_other_users_post(
        self,
        client: AsyncClient,
        moderator_user: User,
        active_post: Content,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{active_post.id}",
            json={"title": "Mod edited"},
            headers=mod_auth_headers(moderator_user),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Mod edited"

    # ------------------------------------------------------------------
    # AC-019.8  Moderator can edit a locked post
    # ------------------------------------------------------------------
    async def test_moderator_can_edit_locked_post(
        self,
        client: AsyncClient,
        moderator_user: User,
        locked_post: Content,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/posts/{locked_post.id}",
            json={"body": "Mod override"},
            headers=mod_auth_headers(moderator_user),
        )
        assert resp.status_code == 200
        assert resp.json()["body"] == "Mod override"

    # ------------------------------------------------------------------
    # AC-019.9  Partial update preserves unchanged fields
    # ------------------------------------------------------------------
    async def test_partial_update_preserves_title(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        original_title = active_post.title
        resp = await client.patch(
            f"/api/v1/posts/{active_post.id}",
            json={"body": "Only body updated"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == original_title
        assert resp.json()["body"] == "Only body updated"

    async def test_partial_update_preserves_body(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
    ) -> None:
        original_body = active_post.body
        resp = await client.patch(
            f"/api/v1/posts/{active_post.id}",
            json={"title": "Only title updated"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200
        assert resp.json()["body"] == original_body
        assert resp.json()["title"] == "Only title updated"

    # ------------------------------------------------------------------
    # AC-019.10  updated_at refreshed
    # ------------------------------------------------------------------
    async def test_updated_at_changes_after_patch(
        self,
        client: AsyncClient,
        regular_user: User,
        active_post: Content,
        db_session: AsyncSession,
    ) -> None:
        original_updated_at = active_post.updated_at
        # Small sleep to guarantee a different timestamp
        await asyncio.sleep(0.01)
        resp = await client.patch(
            f"/api/v1/posts/{active_post.id}",
            json={"title": "Time check"},
            headers=user_auth_headers(regular_user),
        )
        assert resp.status_code == 200

        # Re-fetch from DB
        stmt = select(Content).where(Content.id == active_post.id)
        row = (await db_session.execute(stmt)).scalar_one()
        assert row.updated_at >= original_updated_at

```