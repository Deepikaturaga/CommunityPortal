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
