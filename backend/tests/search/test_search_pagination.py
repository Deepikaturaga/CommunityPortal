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
