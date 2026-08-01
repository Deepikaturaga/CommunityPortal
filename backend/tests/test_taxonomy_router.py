"""HTTP integration tests for the taxonomy admin router (COMP-009 / TASK-030).

Exercises the full FastAPI request/response cycle via HTTPX AsyncClient + ASGITransport.
DB is in-memory SQLite (injected via dependency override in conftest).

Coverage:
  - Category CRUD (create, read, list, patch, delete)
  - Tag CRUD
  - Archive / restore endpoints
  - AC-028.2: archived category/tag not selectable for new content (status preserved on existing)
  - 401 when unauthenticated
  - 404 on missing resources
  - 409 on duplicate slug / content-ref block
  - Pagination + status filter on list endpoints
  - Slug validation (422 for invalid format)
"""

from __future__ import annotations

import pytest


# ===========================================================================
# Categories
# ===========================================================================


class TestCategoryCreate:
    async def test_create_201(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "engineering", "label": "Engineering"},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["slug"] == "engineering"
        assert data["status"] == "active"
        assert data["id"] is not None

    async def test_create_duplicate_slug_409(self, client) -> None:
        await client.post(
            "/api/v1/admin/categories", json={"slug": "dup", "label": "Dup"}
        )
        r = await client.post(
            "/api/v1/admin/categories", json={"slug": "dup", "label": "Dup 2"}
        )
        assert r.status_code == 409

    async def test_create_invalid_slug_422(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "Has Spaces!", "label": "Bad Slug"},
        )
        assert r.status_code == 422

    async def test_create_missing_label_422(self, client) -> None:
        r = await client.post("/api/v1/admin/categories", json={"slug": "no-label"})
        assert r.status_code == 422

    async def test_create_with_parent(self, client) -> None:
        r1 = await client.post(
            "/api/v1/admin/categories", json={"slug": "root", "label": "Root"}
        )
        parent_id = r1.json()["id"]
        r2 = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "leaf", "label": "Leaf", "parent_id": parent_id},
        )
        assert r2.status_code == 201
        assert r2.json()["parent_id"] == parent_id

    async def test_create_invalid_parent_404(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "orphan", "label": "Orphan", "parent_id": 99999},
        )
        assert r.status_code == 404


class TestCategoryRead:
    async def test_get_200(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories", json={"slug": "get-me", "label": "Get Me"}
        )
        cat_id = r.json()["id"]
        r2 = await client.get(f"/api/v1/admin/categories/{cat_id}")
        assert r2.status_code == 200
        assert r2.json()["slug"] == "get-me"

    async def test_get_404(self, client) -> None:
        r = await client.get("/api/v1/admin/categories/99999")
        assert r.status_code == 404


class TestCategoryList:
    async def test_list_empty(self, client) -> None:
        r = await client.get("/api/v1/admin/categories")
        assert r.status_code == 200
        assert r.json()["total"] == 0

    async def test_list_pagination(self, client) -> None:
        for i in range(5):
            await client.post(
                "/api/v1/admin/categories",
                json={"slug": f"list-{i}", "label": f"List {i}"},
            )
        r = await client.get("/api/v1/admin/categories?page=1&page_size=3")
        data = r.json()
        assert data["total"] == 5
        assert len(data["items"]) == 3

    async def test_list_status_filter_active(self, client) -> None:
        r1 = await client.post(
            "/api/v1/admin/categories", json={"slug": "active-cat", "label": "Active"}
        )
        r2 = await client.post(
            "/api/v1/admin/categories", json={"slug": "archived-cat", "label": "Archived"}
        )
        await client.post(f"/api/v1/admin/categories/{r2.json()['id']}/archive")
        r = await client.get("/api/v1/admin/categories?status=active")
        data = r.json()
        assert data["total"] == 1
        assert data["items"][0]["slug"] == "active-cat"

    async def test_list_status_filter_archived(self, client) -> None:
        r1 = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "will-archive", "label": "Will Archive"},
        )
        await client.post(f"/api/v1/admin/categories/{r1.json()['id']}/archive")
        r = await client.get("/api/v1/admin/categories?status=archived")
        data = r.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "archived"


class TestCategoryPatch:
    async def test_patch_label(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories", json={"slug": "patch-me", "label": "Before"}
        )
        cat_id = r.json()["id"]
        r2 = await client.patch(
            f"/api/v1/admin/categories/{cat_id}", json={"label": "After"}
        )
        assert r2.status_code == 200
        assert r2.json()["label"] == "After"

    async def test_patch_404(self, client) -> None:
        r = await client.patch(
            "/api/v1/admin/categories/99999", json={"label": "Ghost"}
        )
        assert r.status_code == 404

    async def test_patch_empty_body_422(self, client) -> None:
        r1 = await client.post(
            "/api/v1/admin/categories", json={"slug": "no-change", "label": "No Change"}
        )
        r = await client.patch(
            f"/api/v1/admin/categories/{r1.json()['id']}", json={}
        )
        assert r.status_code == 422


class TestCategoryArchive:
    async def test_archive_200(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "to-archive", "label": "To Archive"},
        )
        cat_id = r.json()["id"]
        r2 = await client.post(f"/api/v1/admin/categories/{cat_id}/archive")
        assert r2.status_code == 200
        assert r2.json()["status"] == "archived"

    # AC-028.2: archived category does not appear in active list
    async def test_archived_not_in_active_list(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "no-list", "label": "No List"},
        )
        cat_id = r.json()["id"]
        await client.post(f"/api/v1/admin/categories/{cat_id}/archive")
        r2 = await client.get("/api/v1/admin/categories?status=active")
        slugs = [i["slug"] for i in r2.json()["items"]]
        assert "no-list" not in slugs

    # AC-028.2: archived category is still returned by ID (preserved on existing content)
    async def test_archived_category_retrievable_by_id(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "keep-label", "label": "Keep Label"},
        )
        cat_id = r.json()["id"]
        await client.post(f"/api/v1/admin/categories/{cat_id}/archive")
        r2 = await client.get(f"/api/v1/admin/categories/{cat_id}")
        assert r2.status_code == 200
        assert r2.json()["status"] == "archived"
        assert r2.json()["label"] == "Keep Label"

    async def test_archive_idempotent(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "idem-arch", "label": "Idem Arch"},
        )
        cat_id = r.json()["id"]
        await client.post(f"/api/v1/admin/categories/{cat_id}/archive")
        r2 = await client.post(f"/api/v1/admin/categories/{cat_id}/archive")
        assert r2.status_code == 200

    async def test_restore_200(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "restore-http", "label": "Restore HTTP"},
        )
        cat_id = r.json()["id"]
        await client.post(f"/api/v1/admin/categories/{cat_id}/archive")
        r2 = await client.post(f"/api/v1/admin/categories/{cat_id}/restore")
        assert r2.status_code == 200
        assert r2.json()["status"] == "active"


class TestCategoryDelete:
    async def test_delete_204(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/categories",
            json={"slug": "delete-cat", "label": "Delete Cat"},
        )
        cat_id = r.json()["id"]
        r2 = await client.delete(f"/api/v1/admin/categories/{cat_id}")
        assert r2.status_code == 204
        r3 = await client.get(f"/api/v1/admin/categories/{cat_id}")
        assert r3.status_code == 404

    async def test_delete_404(self, client) -> None:
        r = await client.delete("/api/v1/admin/categories/99999")
        assert r.status_code == 404


# ===========================================================================
# Tags
# ===========================================================================


class TestTagCreate:
    async def test_create_201(self, client) -> None:
        r = await client.post("/api/v1/admin/tags", json={"slug": "python", "label": "Python"})
        assert r.status_code == 201
        assert r.json()["status"] == "active"

    async def test_create_duplicate_slug_409(self, client) -> None:
        await client.post("/api/v1/admin/tags", json={"slug": "dup-tag", "label": "D"})
        r = await client.post("/api/v1/admin/tags", json={"slug": "dup-tag", "label": "D2"})
        assert r.status_code == 409

    async def test_create_invalid_slug_422(self, client) -> None:
        r = await client.post("/api/v1/admin/tags", json={"slug": "BAD SLUG", "label": "Bad"})
        assert r.status_code == 422


class TestTagArchive:
    async def test_archive_sets_archived(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/tags", json={"slug": "arch-tag", "label": "Arch Tag"}
        )
        tag_id = r.json()["id"]
        r2 = await client.post(f"/api/v1/admin/tags/{tag_id}/archive")
        assert r2.status_code == 200
        assert r2.json()["status"] == "archived"

    # AC-028.2: archived tag not in active list but label preserved
    async def test_archived_tag_label_preserved(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/tags",
            json={"slug": "keep-tag-label", "label": "Keep This Label"},
        )
        tag_id = r.json()["id"]
        await client.post(f"/api/v1/admin/tags/{tag_id}/archive")
        r2 = await client.get(f"/api/v1/admin/tags/{tag_id}")
        assert r2.status_code == 200
        assert r2.json()["label"] == "Keep This Label"
        assert r2.json()["status"] == "archived"

    async def test_archived_tag_not_in_active_list(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/tags",
            json={"slug": "hide-tag", "label": "Hide Tag"},
        )
        tag_id = r.json()["id"]
        await client.post(f"/api/v1/admin/tags/{tag_id}/archive")
        r2 = await client.get("/api/v1/admin/tags?status=active")
        slugs = [i["slug"] for i in r2.json()["items"]]
        assert "hide-tag" not in slugs

    async def test_restore_tag_200(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/tags", json={"slug": "restore-tag-http", "label": "Restore Tag HTTP"}
        )
        tag_id = r.json()["id"]
        await client.post(f"/api/v1/admin/tags/{tag_id}/archive")
        r2 = await client.post(f"/api/v1/admin/tags/{tag_id}/restore")
        assert r2.status_code == 200
        assert r2.json()["status"] == "active"


class TestTagPatch:
    async def test_patch_label(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/tags", json={"slug": "patch-tag", "label": "Before Tag"}
        )
        tag_id = r.json()["id"]
        r2 = await client.patch(f"/api/v1/admin/tags/{tag_id}", json={"label": "After Tag"})
        assert r2.status_code == 200
        assert r2.json()["label"] == "After Tag"


class TestTagDelete:
    async def test_delete_204(self, client) -> None:
        r = await client.post(
            "/api/v1/admin/tags", json={"slug": "delete-tag", "label": "Delete Tag"}
        )
        tag_id = r.json()["id"]
        r2 = await client.delete(f"/api/v1/admin/tags/{tag_id}")
        assert r2.status_code == 204

    async def test_delete_404(self, client) -> None:
        r = await client.delete("/api/v1/admin/tags/99999")
        assert r.status_code == 404


# ===========================================================================
# Auth enforcement
# ===========================================================================


class TestAuthEnforcement:
    async def test_list_categories_requires_auth(self, unauth_client) -> None:
        r = await unauth_client.get("/api/v1/admin/categories")
        assert r.status_code == 401

    async def test_create_category_requires_auth(self, unauth_client) -> None:
        r = await unauth_client.post(
            "/api/v1/admin/categories", json={"slug": "no-auth", "label": "No Auth"}
        )
        assert r.status_code == 401

    async def test_list_tags_requires_auth(self, unauth_client) -> None:
        r = await unauth_client.get("/api/v1/admin/tags")
        assert r.status_code == 401

    async def test_create_tag_requires_auth(self, unauth_client) -> None:
        r = await unauth_client.post(
            "/api/v1/admin/tags", json={"slug": "no-auth", "label": "No Auth"}
        )
        assert r.status_code == 401


# ===========================================================================
# Health endpoint
# ===========================================================================


class TestHealth:
    async def test_healthz(self, client) -> None:
        r = await client.get("/healthz")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
