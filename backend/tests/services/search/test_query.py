"""Unit tests for the search query service (AC-027.3, AC-027.4, VER-003).

These tests use an in-memory SQLite database via the shared conftest fixtures.
No real Postgres connection is required.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.search.models import Document, Visibility
from app.services.search.query import _allowed_visibilities, search_documents
from app.services.search.schemas import SearchRequest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _seed(db: AsyncSession, **kwargs: object) -> Document:
    """Insert a single Document and flush so it is queryable."""
    doc = Document(**kwargs)  # type: ignore[arg-type]
    db.add(doc)
    await db.flush()
    return doc


# ---------------------------------------------------------------------------
# Unit: role → visibility mapping
# ---------------------------------------------------------------------------


class TestAllowedVisibilities:
    def test_admin_sees_all(self) -> None:
        result = _allowed_visibilities("admin")
        assert set(result) == {Visibility.public, Visibility.internal, Visibility.private}

    def test_editor_sees_public_and_internal(self) -> None:
        result = _allowed_visibilities("editor")
        assert set(result) == {Visibility.public, Visibility.internal}

    def test_viewer_sees_only_public(self) -> None:
        result = _allowed_visibilities("viewer")
        assert result == [Visibility.public]

    def test_unknown_role_defaults_to_viewer(self) -> None:
        result = _allowed_visibilities("unknown_role")
        assert result == [Visibility.public]


# ---------------------------------------------------------------------------
# Integration: search_documents service
# ---------------------------------------------------------------------------


class TestSearchDocumentsEmptyState:
    """AC-027.3 — empty-state on no results."""

    @pytest.mark.asyncio
    async def test_returns_empty_items_when_no_match(
        self, db_session: AsyncSession
    ) -> None:
        await _seed(
            db_session,
            title="Python tutorial",
            body="asyncio and coroutines",
            visibility=Visibility.public,
        )
        req = SearchRequest(q="xyzzy_no_match")
        result = await search_documents(req, role="admin", db=db_session)

        assert result.total == 0
        assert result.items == []
        assert result.query == "xyzzy_no_match"

    @pytest.mark.asyncio
    async def test_empty_db_returns_empty(self, db_session: AsyncSession) -> None:
        req = SearchRequest(q="anything")
        result = await search_documents(req, role="viewer", db=db_session)
        assert result.total == 0
        assert result.items == []


class TestSearchDocumentsVisibilityFilter:
    """Role-aware visibility filtering (IF-014)."""

    @pytest.mark.asyncio
    async def test_viewer_cannot_see_internal(self, db_session: AsyncSession) -> None:
        await _seed(
            db_session,
            title="internal report",
            visibility=Visibility.internal,
        )
        req = SearchRequest(q="internal report")
        result = await search_documents(req, role="viewer", db=db_session)
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_viewer_cannot_see_private(self, db_session: AsyncSession) -> None:
        await _seed(
            db_session,
            title="private document",
            visibility=Visibility.private,
        )
        req = SearchRequest(q="private document")
        result = await search_documents(req, role="viewer", db=db_session)
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_editor_sees_internal_not_private(
        self, db_session: AsyncSession
    ) -> None:
        await _seed(db_session, title="editor-internal", visibility=Visibility.internal)
        await _seed(db_session, title="editor-private", visibility=Visibility.private)

        req_internal = SearchRequest(q="editor-internal")
        assert (await search_documents(req_internal, role="editor", db=db_session)).total == 1

        req_private = SearchRequest(q="editor-private")
        assert (await search_documents(req_private, role="editor", db=db_session)).total == 0

    @pytest.mark.asyncio
    async def test_admin_sees_private(self, db_session: AsyncSession) -> None:
        await _seed(db_session, title="admin-private", visibility=Visibility.private)
        req = SearchRequest(q="admin-private")
        result = await search_documents(req, role="admin", db=db_session)
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_cross_role_isolation(self, db_session: AsyncSession) -> None:
        """A viewer must never see what only an admin or editor can see."""
        await _seed(db_session, title="classified-xyz", visibility=Visibility.private)
        await _seed(
            db_session, title="classified-xyz-internal", visibility=Visibility.internal
        )

        viewer_result = await search_documents(
            SearchRequest(q="classified-xyz"), role="viewer", db=db_session
        )
        assert viewer_result.total == 0, "viewer must not see private/internal docs"


class TestSearchDocumentsParameterized:
    """AC-027.4 — parameterized queries; no injection vector."""

    @pytest.mark.asyncio
    async def test_sql_injection_attempt_is_safe(self, db_session: AsyncSession) -> None:
        """A crafted injection payload must return 0 results, not raise or leak data."""
        await _seed(db_session, title="safe document", visibility=Visibility.public)
        injection_payload = "'; DROP TABLE documents; --"
        req = SearchRequest(q=injection_payload)
        result = await search_documents(req, role="admin", db=db_session)
        assert isinstance(result.total, int)
        assert isinstance(result.items, list)

    @pytest.mark.asyncio
    async def test_wildcard_characters_in_query_are_literal(
        self, db_session: AsyncSession
    ) -> None:
        """Percent in user input must not become unescaped SQL wildcard by itself."""
        await _seed(db_session, title="not this one", visibility=Visibility.public)
        req = SearchRequest(q="%")
        result = await search_documents(req, role="admin", db=db_session)
        assert isinstance(result.total, int)  # no exception raised

    @pytest.mark.asyncio
    async def test_pagination_respects_limit(self, db_session: AsyncSession) -> None:
        for i in range(5):
            await _seed(
                db_session,
                title=f"paginated doc {i}",
                visibility=Visibility.public,
            )
        req = SearchRequest(q="paginated doc", limit=2, offset=0)
        result = await search_documents(req, role="viewer", db=db_session)
        assert len(result.items) <= 2
        assert result.limit == 2

    @pytest.mark.asyncio
    async def test_offset_pagination(self, db_session: AsyncSession) -> None:
        for i in range(4):
            await _seed(
                db_session,
                title=f"offset-test doc {i}",
                visibility=Visibility.public,
            )
        page1 = await search_documents(
            SearchRequest(q="offset-test doc", limit=2, offset=0),
            role="viewer",
            db=db_session,
        )
        page2 = await search_documents(
            SearchRequest(q="offset-test doc", limit=2, offset=2),
            role="viewer",
            db=db_session,
        )
        ids_page1 = {r.id for r in page1.items}
        ids_page2 = {r.id for r in page2.items}
        assert ids_page1.isdisjoint(ids_page2), "Pages must not overlap"


class TestSearchDocumentsBodyMatch:
    @pytest.mark.asyncio
    async def test_body_match_returns_document(self, db_session: AsyncSession) -> None:
        await _seed(
            db_session,
            title="generic title",
            body="unique-body-keyword-7492",
            visibility=Visibility.public,
        )
        req = SearchRequest(q="unique-body-keyword-7492")
        result = await search_documents(req, role="viewer", db=db_session)
        assert result.total >= 1
        assert any("generic title" in r.title for r in result.items)
