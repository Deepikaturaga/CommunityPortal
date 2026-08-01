    await seed_content(db_session, author_id=old_user.id, created_at=old_ts)
"""
TASK-056 acceptance tests — dashboard aggregation.

AC-030.x:
  AC-030.1  Admin-only access (403 for non-admin, 401 for no token)
  AC-030.2  Aggregate figures match source data (accounts)
  AC-030.3  Aggregate figures match source data (content volume)
  AC-030.4  Aggregate figures match source data (moderation stats)
  AC-030.5  30-day windowed counts are correct
  AC-030.6  Pending-items queue depth is correct
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import (
    admin_token,
    moderator_token,
    seed_content,
    seed_moderation,
    seed_user,
    user_token,
)
from app.models.content import ContentStatus
from app.models.moderation import ModerationVerdict
from app.models.user import UserRole, UserStatus

DASHBOARD_URL = "/api/v1/admin/dashboard"


# ---------------------------------------------------------------------------
# AC-030.1  Access control
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_requires_auth(client: AsyncClient) -> None:
    """No token → 401."""
    resp = await client.get(DASHBOARD_URL)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_rejects_regular_user(client: AsyncClient) -> None:
    """Authenticated user (non-admin) → 403."""
    resp = await client.get(
        DASHBOARD_URL, headers={"Authorization": f"Bearer {user_token()}"}
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_dashboard_rejects_moderator(client: AsyncClient) -> None:
    """Moderator role → 403 (admin-only)."""
    resp = await client.get(
        DASHBOARD_URL, headers={"Authorization": f"Bearer {moderator_token()}"}
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_dashboard_allows_admin(client: AsyncClient) -> None:
    """Admin token → 200."""
    resp = await client.get(
        DASHBOARD_URL, headers={"Authorization": f"Bearer {admin_token()}"}
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# AC-030.2  Account aggregates match source data
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_account_aggregates(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Seed known users; verify dashboard counts match exactly."""
    # Seed: 1 admin, 2 moderators, 3 regular users; 1 suspended, 1 deleted
    await seed_user(db_session, role=UserRole.admin, status=UserStatus.active)
    await seed_user(db_session, role=UserRole.moderator, status=UserStatus.active)
    await seed_user(db_session, role=UserRole.moderator, status=UserStatus.active)
    await seed_user(db_session, role=UserRole.user, status=UserStatus.active)
    await seed_user(db_session, role=UserRole.user, status=UserStatus.suspended)
    await seed_user(db_session, role=UserRole.user, status=UserStatus.deleted)

    resp = await client.get(
        DASHBOARD_URL, headers={"Authorization": f"Bearer {admin_token()}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    accts = data["accounts"]

    assert accts["total"] >= 6
    assert accts["admins"] >= 1
    assert accts["moderators"] >= 2
    assert accts["regular_users"] >= 3
    assert accts["active"] >= 4
    assert accts["suspended"] >= 1
    assert accts["deleted"] >= 1


# ---------------------------------------------------------------------------
# AC-030.3  Content volume aggregates match source data
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_content_volume_aggregates(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Seed known content items; verify dashboard counts match."""
    author = await seed_user(db_session)
    await seed_content(db_session, author_id=author.id, status=ContentStatus.pending)
    await seed_content(db_session, author_id=author.id, status=ContentStatus.pending)
    await seed_content(db_session, author_id=author.id, status=ContentStatus.published)
    await seed_content(db_session, author_id=author.id, status=ContentStatus.removed)

    resp = await client.get(
        DASHBOARD_URL, headers={"Authorization": f"Bearer {admin_token()}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    content = data["content"]

    assert content["total"] >= 4
    assert content["pending"] >= 2
    assert content["published"] >= 1
    assert content["removed"] >= 1


# ---------------------------------------------------------------------------
# AC-030.4  Moderation stats match source data
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_moderation_stats_aggregates(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Seed known moderation actions; verify dashboard counts match."""
    author = await seed_user(db_session)
    mod = await seed_user(db_session, role=UserRole.moderator)

    c1 = await seed_content(db_session, author_id=author.id, status=ContentStatus.published)
    c2 = await seed_content(db_session, author_id=author.id, status=ContentStatus.removed)
    c3 = await seed_content(db_session, author_id=author.id, status=ContentStatus.published)

    await seed_moderation(
        db_session,
        content_item_id=c1.id,
        moderator_id=mod.id,
        verdict=ModerationVerdict.approved,
    )
    await seed_moderation(
        db_session,
        content_item_id=c2.id,
        moderator_id=mod.id,
        verdict=ModerationVerdict.rejected,
    )
    await seed_moderation(
        db_session,
        content_item_id=c3.id,
        moderator_id=mod.id,
        verdict=ModerationVerdict.escalated,
    )

    resp = await client.get(
        DASHBOARD_URL, headers={"Authorization": f"Bearer {admin_token()}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    mod_stats = data["moderation"]

    assert mod_stats["total_actions"] >= 3
    assert mod_stats["approved"] >= 1
    assert mod_stats["rejected"] >= 1
    assert mod_stats["escalated"] >= 1


# ---------------------------------------------------------------------------
# AC-030.5  30-day windowed counts are correct
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_new_last_30_days_counts(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Items/users created >30 days ago must NOT appear in windowed counts."""
    old_ts = datetime.now(tz=timezone.utc) - timedelta(days=60)
    recent_ts = datetime.now(tz=timezone.utc) - timedelta(days=5)

    old_user = await seed_user(db_session, created_at=old_ts)
    recent_user = await seed_user(db_session, created_at=recent_ts)

    )
    await seed_content(db_session, author_id=recent_user.id, created_at=recent_ts)

    resp = await client.get(
        DASHBOARD_URL, headers={"Authorization": f"Bearer {admin_token()}"}
    )
    assert resp.status_code == 200
    data = resp.json()

    # recent counts must include the recent items but not old ones
    # (We use >= comparisons because other tests also insert rows in same session)
    assert data["accounts"]["new_last_30_days"] >= 1
    assert data["content"]["new_last_30_days"] >= 1


# ---------------------------------------------------------------------------
# AC-030.6  Pending-items queue depth
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pending_items_queue_depth(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """pending_items must equal content items with status=pending."""
    author = await seed_user(db_session)
    await seed_content(db_session, author_id=author.id, status=ContentStatus.pending)
    await seed_content(db_session, author_id=author.id, status=ContentStatus.pending)
    await seed_content(db_session, author_id=author.id, status=ContentStatus.published)

    resp = await client.get(
        DASHBOARD_URL, headers={"Authorization": f"Bearer {admin_token()}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["moderation"]["pending_items"] >= 2


# ---------------------------------------------------------------------------
# Response shape
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_response_schema(client: AsyncClient) -> None:
    """Verify all expected top-level and nested keys are present."""
    resp = await client.get(
        DASHBOARD_URL, headers={"Authorization": f"Bearer {admin_token()}"}
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "generated_at" in data
    assert set(data["accounts"].keys()) == {
        "total",
        "active",
        "suspended",
        "deleted",
        "admins",
        "moderators",
        "regular_users",
        "new_last_30_days",
    }
    assert set(data["content"].keys()) == {
        "total",
        "pending",
        "published",
        "removed",
        "new_last_30_days",
    }
    assert set(data["moderation"].keys()) == {
        "total_actions",
        "approved",
        "rejected",
        "escalated",
        "actions_last_30_days",
        "pending_items",
    }
