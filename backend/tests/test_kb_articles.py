"""
Integration tests for POST /api/v1/kb/articles (TASK-044).

Coverage map:
  AC-022.2  →  test_403_for_viewer, test_403_for_unauthenticated
  AC-022.3  →  test_body_sanitized_on_create
  VER-002   →  test_contributor_can_create_article (happy-path HTTP + DB)
  VER-010   →  test_admin_can_create_article
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Role
from app.kb.article_models import Article
from tests.conftest import get_token, make_user


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture()
async def contributor_token(client: AsyncClient, db_session: AsyncSession) -> str:
    await make_user(
        db_session,
        email="contrib@example.com",
        password="secret1234",
        role=Role.CONTRIBUTOR,
    )
    return await get_token(client, email="contrib@example.com", password="secret1234")


@pytest_asyncio.fixture()
async def admin_token(client: AsyncClient, db_session: AsyncSession) -> str:
    await make_user(
        db_session,
        email="admin@example.com",
        password="secret1234",
        role=Role.ADMIN,
    )
    return await get_token(client, email="admin@example.com", password="secret1234")


@pytest_asyncio.fixture()
async def viewer_token(client: AsyncClient, db_session: AsyncSession) -> str:
    await make_user(
        db_session,
        email="viewer@example.com",
        password="secret1234",
        role=Role.VIEWER,
    )
    return await get_token(client, email="viewer@example.com", password="secret1234")


# ---------------------------------------------------------------------------
# AC-022.2 — role enforcement
# ---------------------------------------------------------------------------

async def test_unauthenticated_returns_401(client: AsyncClient) -> None:
    """No bearer token → 401."""
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "No auth", "body": "<p>test</p>"},
    )
    assert resp.status_code == 401


async def test_viewer_returns_403(
    client: AsyncClient, viewer_token: str
) -> None:
    """Viewer role → 403 Forbidden (AC-022.2)."""
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "Viewer attempt", "body": "<p>hello</p>"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert resp.status_code == 403


async def test_contributor_can_create_article(
    client: AsyncClient,
    db_session: AsyncSession,
    contributor_token: str,
) -> None:
    """Contributor role → 201 Created (AC-022.2, VER-002)."""
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "My First Article", "body": "<p>Hello <strong>world</strong></p>"},
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "My First Article"
    assert data["slug"] == "my-first-article"
    assert data["status"] == "draft"
    assert "id" in data
    assert "author_id" in data

    # Verify persistence in DB
    result = await db_session.execute(
        select(Article).where(Article.slug == "my-first-article")
    )
    article = result.scalar_one_or_none()
    assert article is not None
    assert article.title == "My First Article"


async def test_admin_can_create_article(
    client: AsyncClient,
    admin_token: str,
) -> None:
    """Admin role is also allowed (AC-022.2, VER-010)."""
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "Admin Article", "body": "<p>content</p>"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["title"] == "Admin Article"


# ---------------------------------------------------------------------------
# AC-022.3 — sanitization enforced at storage boundary
# ---------------------------------------------------------------------------

async def test_body_sanitized_on_create(
    client: AsyncClient,
    db_session: AsyncSession,
    contributor_token: str,
) -> None:
    """
    XSS payload in body is stripped before storage.
    The stored article body must not contain the script tag (AC-022.3).
    """
    xss_payload = "<p>Safe text</p><script>alert('xss')</script>"
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "XSS Test Article", "body": xss_payload},
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    assert resp.status_code == 201
    returned_body = resp.json()["body"]
    assert "<script>" not in returned_body
    assert "alert" not in returned_body
    assert "Safe text" in returned_body

    # Confirm sanitization happened at the DB layer too
    result = await db_session.execute(
        select(Article).where(Article.slug == "xss-test-article")
    )
    article = result.scalar_one_or_none()
    assert article is not None
    assert "<script>" not in article.body
    assert "alert" not in article.body


async def test_javascript_href_sanitized(
    client: AsyncClient,
    contributor_token: str,
) -> None:
    """javascript: URI in href is stripped before storage (AC-022.3)."""
    body = '<a href="javascript:evil()">click me</a>'
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "JS Href Article", "body": body},
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    assert resp.status_code == 201
    stored_body = resp.json()["body"]
    assert "javascript:" not in stored_body
    # Text preserved
    assert "click me" in stored_body


async def test_safe_html_preserved(
    client: AsyncClient,
    contributor_token: str,
) -> None:
    """Legitimate formatting tags survive sanitization (AC-022.3)."""
    body = "<h2>Title</h2><p>Para with <em>emphasis</em> and <code>code</code>.</p>"
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "Safe HTML Article", "body": body},
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    assert resp.status_code == 201
    stored_body = resp.json()["body"]
    assert "<h2>" in stored_body
    assert "<em>" in stored_body
    assert "<code>" in stored_body


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

async def test_empty_title_returns_422(
    client: AsyncClient,
    contributor_token: str,
) -> None:
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "", "body": "<p>body</p>"},
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    assert resp.status_code == 422


async def test_blank_title_returns_422(
    client: AsyncClient,
    contributor_token: str,
) -> None:
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "   ", "body": "<p>body</p>"},
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    assert resp.status_code == 422


async def test_missing_body_returns_422(
    client: AsyncClient,
    contributor_token: str,
) -> None:
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "No body"},
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    assert resp.status_code == 422


async def test_slug_deduplication(
    client: AsyncClient,
    contributor_token: str,
) -> None:
    """Creating two articles with the same title yields distinct slugs."""
    payload = {"title": "Duplicate Title", "body": "<p>body</p>"}
    r1 = await client.post(
        "/api/v1/kb/articles",
        json=payload,
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    r2 = await client.post(
        "/api/v1/kb/articles",
        json=payload,
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["slug"] != r2.json()["slug"]


async def test_custom_status_draft(
    client: AsyncClient,
    contributor_token: str,
) -> None:
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "Draft Status", "body": "<p>x</p>", "status": "draft"},
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "draft"


async def test_invalid_status_returns_422(
    client: AsyncClient,
    contributor_token: str,
) -> None:
    resp = await client.post(
        "/api/v1/kb/articles",
        json={"title": "Bad Status", "body": "<p>x</p>", "status": "bogus"},
        headers={"Authorization": f"Bearer {contributor_token}"},
    )
    assert resp.status_code == 422
