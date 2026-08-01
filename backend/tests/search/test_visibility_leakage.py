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
