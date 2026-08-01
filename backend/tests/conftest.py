"""Shared pytest fixtures for the notification preference API tests."""
from __future__ import annotations
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt

from app.core.config import settings
from app.main import app


# ── JWT helpers ────────────────────────────────────────────────────────────────

def make_token(user_id: str, secret: str | None = None) -> str:
    import time

    secret = secret or settings.secret_key
    now = int(time.time())
    return jwt.encode(
        {"sub": user_id, "exp": now + 3600},
        secret,
        algorithm=settings.algorithm,
    )


def auth_headers(user_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(user_id)}"}


# ── In-process async HTTP client ───────────────────────────────────────────────

@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
