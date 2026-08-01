"""
JRN-003: Discussion Journey
Happy path + key alternates:
  - HP: Authenticated user creates a discussion → 201
  - HP2: List discussions (paginated)
  - HP3: Get discussion increments view count
  - HP4: Author updates own discussion
  - HP5: Author closes discussion (state transition: open → closed)
  - ALT-1: Unauthenticated create → 401
  - ALT-2: Empty title → 422
  - ALT-3: Non-author cannot update → 403
  - ALT-4: Invalid state transition (open → archived) → 409
  - ALT-5: Delete discussion removes it
  - ALT-6: Non-author cannot delete → 403
  - ALT-7: Moderator can update any discussion
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestJRN003Discussion:
    _DISC_PAYLOAD = {
        "title": "How do I configure CORS?",
        "body": "I am trying to configure CORS in my FastAPI app.",
        "tags": "fastapi,cors",
    }

    async def _create(self, client: AsyncClient, headers: dict, payload: dict | None = None) -> dict:
        resp = await client.post(
            "/api/v1/discussions",
            headers=headers,
            json=payload or self._DISC_PAYLOAD,
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    async def test_hp_create_discussion(
        self, client: AsyncClient, member_headers
    ) -> None:
        d = await self._create(client, member_headers)
        assert d["title"] == "How do I configure CORS?"
        assert d["status"] == "open"
        assert d["view_count"] == 0
        assert d["tags"] == "fastapi,cors"

    async def test_hp2_list_discussions_paginated(
        self, client: AsyncClient, member_headers
    ) -> None:
        for i in range(3):
            await self._create(
                client,
                member_headers,
                {"title": f"Discussion {i} about something", "body": "Some body text here yes"},
            )
        resp = await client.get("/api/v1/discussions?page=1&page_size=2")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert body["total"] >= 3
        assert len(body["items"]) <= 2

    async def test_hp3_get_discussion_increments_view_count(
        self, client: AsyncClient, member_headers
    ) -> None:
        d = await self._create(client, member_headers)
        disc_id = d["id"]
        r1 = await client.get(f"/api/v1/discussions/{disc_id}")
        assert r1.status_code == 200
        assert r1.json()["view_count"] == 1
        r2 = await client.get(f"/api/v1/discussions/{disc_id}")
        assert r2.json()["view_count"] == 2

    async def test_hp4_author_updates_own_discussion(
        self, client: AsyncClient, member_headers
    ) -> None:
        d = await self._create(client, member_headers)
        resp = await client.put(
            f"/api/v1/discussions/{d['id']}",
            headers=member_headers,
            json={"title": "Updated: How do I configure CORS properly?"},
        )
        assert resp.status_code == 200
        assert "Updated" in resp.json()["title"]

    async def test_hp5_close_discussion_state_transition(
        self, client: AsyncClient, member_headers
    ) -> None:
        d = await self._create(client, member_headers)
        resp = await client.put(
            f"/api/v1/discussions/{d['id']}",
            headers=member_headers,
            json={"status": "closed"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "closed"

    async def test_alt1_unauthenticated_create_returns_401(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post("/api/v1/discussions", json=self._DISC_PAYLOAD)
        assert resp.status_code == 401

    async def test_alt2_empty_title_returns_422(
        self, client: AsyncClient, member_headers
    ) -> None:
        resp = await client.post(
            "/api/v1/discussions",
            headers=member_headers,
            json={"title": "ab", "body": "body here is fine"},  # title < 5 chars
        )
        assert resp.status_code == 422

    async def test_alt3_non_author_cannot_update(
        self, client: AsyncClient, member_headers, second_user, db_session
    ) -> None:
        from tests.conftest import auth_headers
        d = await self._create(client, member_headers)
        second_hdrs = auth_headers(second_user)
        resp = await client.put(
            f"/api/v1/discussions/{d['id']}",
            headers=second_hdrs,
            json={"title": "Updated by someone else again here"},
        )
        assert resp.status_code == 403

    async def test_alt4_invalid_state_transition_returns_409(
        self, client: AsyncClient, member_headers
    ) -> None:
        d = await self._create(client, member_headers)
        # open → archived is NOT allowed (must go open→closed first)
        resp = await client.put(
            f"/api/v1/discussions/{d['id']}",
            headers=member_headers,
            json={"status": "archived"},
        )
        assert resp.status_code == 409

    async def test_alt5_delete_removes_discussion(
        self, client: AsyncClient, member_headers
    ) -> None:
        d = await self._create(client, member_headers)
        del_resp = await client.delete(
            f"/api/v1/discussions/{d['id']}", headers=member_headers
        )
        assert del_resp.status_code == 204
        get_resp = await client.get(f"/api/v1/discussions/{d['id']}")
        assert get_resp.status_code == 404

    async def test_alt6_non_author_cannot_delete(
        self, client: AsyncClient, member_headers, second_user
    ) -> None:
        from tests.conftest import auth_headers
        d = await self._create(client, member_headers)
        second_hdrs = auth_headers(second_user)
        resp = await client.delete(
            f"/api/v1/discussions/{d['id']}", headers=second_hdrs
        )
        assert resp.status_code == 403

    async def test_alt7_moderator_can_update_any_discussion(
        self, client: AsyncClient, member_headers, moderator_headers
    ) -> None:
        d = await self._create(client, member_headers)
        resp = await client.put(
            f"/api/v1/discussions/{d['id']}",
            headers=moderator_headers,
            json={"title": "Moderated: how to configure CORS"},
        )
        assert resp.status_code == 200

    async def test_get_nonexistent_discussion_returns_404(
        self, client: AsyncClient
    ) -> None:
        resp = await client.get("/api/v1/discussions/999999")
        assert resp.status_code == 404
