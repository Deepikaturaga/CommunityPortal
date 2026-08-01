"""Tests for the moderation review queue & actions (TASK-037 / AC-014.x).

Coverage map:
  AC-014.1  queue returns only flagged items by default
  AC-014.2  queue supports status filter + pagination
  AC-014.3  every action writes an audit record
  AC-014.4  audit records are immutable (ORM event guard)
  OWASP:    403 for non-moderator on every endpoint
  State:    illegal transitions are rejected
  404:      non-existent content_id returns 404
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus
from app.models.moderation import ModerationAuditRecord
from app.models.user import User
from tests.conftest import make_moderator_token, make_user_token


# ============================================================================
# Helper
# ============================================================================


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# GET /api/v1/moderation/queue — queue listing
# ============================================================================


class TestQueueListing:
    async def test_returns_flagged_items_by_default(
        self,
        client: AsyncClient,
        moderator_user: User,
        flagged_content: Content,
    ) -> None:
        """AC-014.1 — default queue returns flagged items."""
        token = make_moderator_token(moderator_user)
        resp = await client.get(
            "/api/v1/moderation/queue", headers=auth_headers(token)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        ids = [item["id"] for item in data["items"]]
        assert flagged_content.id in ids

    async def test_active_items_not_in_default_queue(
        self,
        client: AsyncClient,
        moderator_user: User,
        active_content: Content,
        flagged_content: Content,
    ) -> None:
        """Active content must not appear in the flagged queue."""
        token = make_moderator_token(moderator_user)
        resp = await client.get(
            "/api/v1/moderation/queue", headers=auth_headers(token)
        )
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["items"]]
        assert active_content.id not in ids

    async def test_status_filter_active(
        self,
        client: AsyncClient,
        moderator_user: User,
        active_content: Content,
    ) -> None:
        """AC-014.2 — status filter returns items with requested status."""
        token = make_moderator_token(moderator_user)
        resp = await client.get(
            "/api/v1/moderation/queue?status=active", headers=auth_headers(token)
        )
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["items"]]
        assert active_content.id in ids

    async def test_pagination_page_size(
        self,
        client: AsyncClient,
        moderator_user: User,
        db_session: AsyncSession,
        regular_user: User,
    ) -> None:
        """AC-014.2 — page_size is respected."""
        # Add 5 flagged items
        for i in range(5):
            c = Content(
                author_id=regular_user.id,
                title=f"Paged post {i}",
                body="body",
                status=ContentStatus.flagged,
            )
            db_session.add(c)
        await db_session.flush()

        token = make_moderator_token(moderator_user)
        resp = await client.get(
            "/api/v1/moderation/queue?page_size=2", headers=auth_headers(token)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 2
        assert data["page_size"] == 2

    async def test_queue_requires_auth(self, client: AsyncClient) -> None:
        """Unauthenticated request returns 401."""
        resp = await client.get("/api/v1/moderation/queue")
        assert resp.status_code == 401

    async def test_queue_rejects_regular_user(
        self,
        client: AsyncClient,
        regular_user: User,
    ) -> None:
        """OWASP / AC-014.3 — non-moderator gets 403 on queue endpoint."""
        token = make_user_token(regular_user)
        resp = await client.get(
            "/api/v1/moderation/queue", headers=auth_headers(token)
        )
        assert resp.status_code == 403


# ============================================================================
# POST /api/v1/moderation/queue/{content_id}/actions — action dispatch
# ============================================================================


class TestModerationActions:
    async def test_lock_action_updates_status(
        self,
        client: AsyncClient,
        moderator_user: User,
        flagged_content: Content,
        db_session: AsyncSession,
    ) -> None:
        """AC-014.3 — lock action transitions status and writes audit record."""
        token = make_moderator_token(moderator_user)
        resp = await client.post(
            f"/api/v1/moderation/queue/{flagged_content.id}/actions",
            json={"action": "lock", "reason": "Spam"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["new_status"] == "locked"
        assert body["audit_record"]["action"] == "lock"
        assert body["audit_record"]["reason"] == "Spam"
        assert body["audit_record"]["previous_status"] == "flagged"
        assert body["audit_record"]["new_status"] == "locked"

        # Verify DB state
        await db_session.refresh(flagged_content)
        assert flagged_content.status == ContentStatus.locked
        assert flagged_content.is_locked is True

    async def test_hide_action_updates_status(
        self,
        client: AsyncClient,
        moderator_user: User,
        flagged_content: Content,
        db_session: AsyncSession,
    ) -> None:
        """AC-014.3 — hide action transitions status and writes audit record."""
        token = make_moderator_token(moderator_user)
        resp = await client.post(
            f"/api/v1/moderation/queue/{flagged_content.id}/actions",
            json={"action": "hide"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["new_status"] == "hidden"
        assert body["audit_record"]["action"] == "hide"

    async def test_delete_action_updates_status(
        self,
        client: AsyncClient,
        moderator_user: User,
        flagged_content: Content,
        db_session: AsyncSession,
    ) -> None:
        """AC-014.3 — delete action transitions status and writes audit record."""
        token = make_moderator_token(moderator_user)
        resp = await client.post(
            f"/api/v1/moderation/queue/{flagged_content.id}/actions",
            json={"action": "delete", "reason": "Hate speech"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["new_status"] == "deleted"

        await db_session.refresh(flagged_content)
        assert flagged_content.status == ContentStatus.deleted

    async def test_audit_record_written_in_db(
        self,
        client: AsyncClient,
        moderator_user: User,
        active_content: Content,
        db_session: AsyncSession,
    ) -> None:
        """AC-014.3 — audit record exists in DB after action."""
        token = make_moderator_token(moderator_user)
        await client.post(
            f"/api/v1/moderation/queue/{active_content.id}/actions",
            json={"action": "lock"},
            headers=auth_headers(token),
        )
        stmt = select(ModerationAuditRecord).where(
            ModerationAuditRecord.content_id == active_content.id
        )
        record = (await db_session.execute(stmt)).scalar_one_or_none()
        assert record is not None
        assert record.action.value == "lock"
        assert record.moderator_id == moderator_user.id

    async def test_action_without_auth_returns_401(
        self,
        client: AsyncClient,
        flagged_content: Content,
    ) -> None:
        """Unauthenticated action returns 401."""
        resp = await client.post(
            f"/api/v1/moderation/queue/{flagged_content.id}/actions",
            json={"action": "lock"},
        )
        assert resp.status_code == 401

    async def test_action_rejects_regular_user_403(
        self,
        client: AsyncClient,
        regular_user: User,
        flagged_content: Content,
    ) -> None:
        """OWASP / AC-014.3 — non-moderator gets 403 on action endpoint."""
        token = make_user_token(regular_user)
        resp = await client.post(
            f"/api/v1/moderation/queue/{flagged_content.id}/actions",
            json={"action": "lock"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 403

    async def test_action_on_nonexistent_content_returns_404(
        self,
        client: AsyncClient,
        moderator_user: User,
    ) -> None:
        """Non-existent content_id returns 404."""
        token = make_moderator_token(moderator_user)
        resp = await client.post(
            "/api/v1/moderation/queue/nonexistent-id/actions",
            json={"action": "lock"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 404

    async def test_illegal_transition_returns_422(
        self,
        client: AsyncClient,
        moderator_user: User,
        db_session: AsyncSession,
        regular_user: User,
    ) -> None:
        """State-machine guard — transitioning from 'deleted' raises 422."""
        # Create a deleted content item
        deleted_content = Content(
            author_id=regular_user.id,
            title="Deleted post",
            body="body",
            status=ContentStatus.deleted,
        )
        db_session.add(deleted_content)
        await db_session.flush()

        token = make_moderator_token(moderator_user)
        resp = await client.post(
            f"/api/v1/moderation/queue/{deleted_content.id}/actions",
            json={"action": "lock"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 422

    async def test_reason_is_optional(
        self,
        client: AsyncClient,
        moderator_user: User,
        flagged_content: Content,
    ) -> None:
        """Reason field is optional; omitting it succeeds."""
        token = make_moderator_token(moderator_user)
        resp = await client.post(
            f"/api/v1/moderation/queue/{flagged_content.id}/actions",
            json={"action": "hide"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["audit_record"]["reason"] is None


# ============================================================================
# AC-014.4 — audit record immutability (ORM event guards)
# ============================================================================


class TestAuditImmutability:
    async def test_orm_update_raises(
        self,
        db_session: AsyncSession,
        moderator_user: User,
        flagged_content: Content,
    ) -> None:
        """AC-014.4 — ORM UPDATE on ModerationAuditRecord raises RuntimeError."""
        record = ModerationAuditRecord(
            content_id=flagged_content.id,
            moderator_id=moderator_user.id,
            action="lock",
            reason="original",
            previous_status="flagged",
            new_status="locked",
        )
        db_session.add(record)
        await db_session.flush()

        # Attempt to mutate
        record.reason = "tampered"
        with pytest.raises(RuntimeError, match="immutable"):
            await db_session.flush()

    async def test_orm_delete_raises(
        self,
        db_session: AsyncSession,
        moderator_user: User,
        flagged_content: Content,
    ) -> None:
        """AC-014.4 — ORM DELETE on ModerationAuditRecord raises RuntimeError."""
        record = ModerationAuditRecord(
            content_id=flagged_content.id,
            moderator_id=moderator_user.id,
            action="hide",
            reason=None,
            previous_status="flagged",
            new_status="hidden",
        )
        db_session.add(record)
        await db_session.flush()

        await db_session.delete(record)
        with pytest.raises(RuntimeError, match="immutable"):
            await db_session.flush()


# ============================================================================
# Health endpoint smoke test
# ============================================================================


async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
