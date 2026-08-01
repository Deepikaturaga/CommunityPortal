"""HTTP integration tests for GET /api/v1/search (IF-014, VER-003, VER-009).

Uses HTTPX ASGITransport against the real FastAPI app with an in-memory
SQLite database via the shared conftest fixtures.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.search.models import Document, Visibility


async def _seed(db: AsyncSession, **kwargs) -> Document:  # type: ignore[no-untyped-def]
    doc = Document(**kwargs)
    db.add(doc)
    await db.flush()
    return doc


class TestSearchEndpointAuth:
    @pytest.mark.asyncio
    async def test_unauthenticated_request_returns_401(
        self, client: AsyncClient
    ) -> None:
        resp = await client.get("/api/v1/search", params={"q": "hello"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_authenticated_request_returns_200(
        self, client: AsyncClient, viewer_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/search",
            params={"q": "anything"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 200


class TestSearchEndpointInputValidation:
    @pytest.mark.asyncio
    async def test_missing_q_returns_422(
        self, client: AsyncClient, viewer_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/search",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_blank_q_returns_422(
        self, client: AsyncClient, viewer_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/search",
            params={"q": "   "},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        # Pydantic strips whitespace → min_length=1 fails
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_limit_exceeding_max_returns_422(
        self, client: AsyncClient, viewer_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/search",
            params={"q": "test", "limit": "999"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_negative_offset_returns_422(
        self, client: AsyncClient, viewer_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/search",
            params={"q": "test", "offset": "-1"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 422


class TestSearchEndpointEmptyState:
    """AC-027.3 — empty-state on no results."""

    @pytest.mark.asyncio
    async def test_no_results_returns_empty_items(
        self, client: AsyncClient, viewer_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/search",
            params={"q": "zzz_no_match_ever_zzz"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []
        assert body["query"] == "zzz_no_match_ever_zzz"


class TestSearchEndpointVisibilityFilter:
    """Role-aware visibility — IF-014."""

    @pytest.mark.asyncio
    async def test_viewer_does_not_see_internal_docs(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        viewer_token: str,
    ) -> None:
        await _seed(
            db_session,
            title="http-internal-secret",
            visibility=Visibility.internal,
        )
        resp = await client.get(
            "/api/v1/search",
            params={"q": "http-internal-secret"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_admin_sees_private_docs(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        admin_token: str,
    ) -> None:
        await _seed(
            db_session,
            title="http-private-doc",
            visibility=Visibility.private,
        )
        resp = await client.get(
            "/api/v1/search",
            params={"q": "http-private-doc"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    @pytest.mark.asyncio
    async def test_editor_sees_internal_not_private(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        editor_token: str,
    ) -> None:
        await _seed(
            db_session,
            title="http-editor-internal-doc",
            visibility=Visibility.internal,
        )
        await _seed(
            db_session,
            title="http-editor-private-doc",
            visibility=Visibility.private,
        )
        resp_internal = await client.get(
            "/api/v1/search",
            params={"q": "http-editor-internal-doc"},
            headers={"Authorization": f"Bearer {editor_token}"},
        )
        assert resp_internal.json()["total"] == 1

        resp_private = await client.get(
            "/api/v1/search",
            params={"q": "http-editor-private-doc"},
            headers={"Authorization": f"Bearer {editor_token}"},
        )
        assert resp_private.json()["total"] == 0


class TestSearchEndpointResponseShape:
    @pytest.mark.asyncio
    async def test_response_contains_required_fields(
        self, client: AsyncClient, viewer_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/search",
            params={"q": "anything"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        body = resp.json()
        assert "total" in body
        assert "items" in body
        assert "query" in body
        assert "limit" in body
        assert "offset" in body

    @pytest.mark.asyncio
    async def test_query_is_echoed_in_response(
        self, client: AsyncClient, viewer_token: str
    ) -> None:
        resp = await client.get(
            "/api/v1/search",
            params={"q": "my search term"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.json()["query"] == "my search term"
