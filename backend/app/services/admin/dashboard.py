from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import ContentItem, ContentStatus
from app.models.moderation import ModerationAction, ModerationVerdict
from app.models.user import User, UserRole, UserStatus
from app.services.admin.schemas import (
    AccountStats,
    ContentVolumeStats,
    DashboardResponse,
    ModerationStats,
)


async def _account_stats(db: AsyncSession) -> AccountStats:
    """Aggregate user account figures in a single query pass."""
    thirty_days_ago = datetime.now(tz=timezone.utc) - timedelta(days=30)

    result = await db.execute(
        select(
            func.count().label("total"),
            func.sum(case((User.status == UserStatus.active, 1), else_=0)).label("active"),
            func.sum(case((User.status == UserStatus.suspended, 1), else_=0)).label("suspended"),
            func.sum(case((User.status == UserStatus.deleted, 1), else_=0)).label("deleted"),
            func.sum(case((User.role == UserRole.admin, 1), else_=0)).label("admins"),
            func.sum(case((User.role == UserRole.moderator, 1), else_=0)).label("moderators"),
            func.sum(case((User.role == UserRole.user, 1), else_=0)).label("regular_users"),
            func.sum(
                case((User.created_at >= thirty_days_ago, 1), else_=0)
            ).label("new_last_30_days"),
        )
    )
    row = result.one()
    return AccountStats(
        total=row.total or 0,
        active=row.active or 0,
        suspended=row.suspended or 0,
        deleted=row.deleted or 0,
        admins=row.admins or 0,
        moderators=row.moderators or 0,
        regular_users=row.regular_users or 0,
        new_last_30_days=row.new_last_30_days or 0,
    )


async def _content_volume_stats(db: AsyncSession) -> ContentVolumeStats:
    """Aggregate content item figures in a single query pass."""
    thirty_days_ago = datetime.now(tz=timezone.utc) - timedelta(days=30)

    result = await db.execute(
        select(
            func.count().label("total"),
            func.sum(
                case((ContentItem.status == ContentStatus.pending, 1), else_=0)
            ).label("pending"),
            func.sum(
                case((ContentItem.status == ContentStatus.published, 1), else_=0)
            ).label("published"),
            func.sum(
                case((ContentItem.status == ContentStatus.removed, 1), else_=0)
            ).label("removed"),
            func.sum(
                case((ContentItem.created_at >= thirty_days_ago, 1), else_=0)
            ).label("new_last_30_days"),
        )
    )
    row = result.one()
    return ContentVolumeStats(
        total=row.total or 0,
        pending=row.pending or 0,
        published=row.published or 0,
        removed=row.removed or 0,
        new_last_30_days=row.new_last_30_days or 0,
    )


async def _moderation_stats(db: AsyncSession) -> ModerationStats:
    """Aggregate moderation action figures in a single query pass."""
    thirty_days_ago = datetime.now(tz=timezone.utc) - timedelta(days=30)

    # Actions aggregate
    actions_result = await db.execute(
        select(
            func.count().label("total_actions"),
            func.sum(
                case((ModerationAction.verdict == ModerationVerdict.approved, 1), else_=0)
            ).label("approved"),
            func.sum(
                case((ModerationAction.verdict == ModerationVerdict.rejected, 1), else_=0)
            ).label("rejected"),
            func.sum(
                case((ModerationAction.verdict == ModerationVerdict.escalated, 1), else_=0)
            ).label("escalated"),
            func.sum(
                case((ModerationAction.created_at >= thirty_days_ago, 1), else_=0)
            ).label("actions_last_30_days"),
        )
    )
    actions_row = actions_result.one()

    # Pending items = content items with no moderation action yet
    pending_result = await db.execute(
        select(func.count()).select_from(ContentItem).where(
            ContentItem.status == ContentStatus.pending
        )
    )
    pending_items = pending_result.scalar_one()

    return ModerationStats(
        total_actions=actions_row.total_actions or 0,
        approved=actions_row.approved or 0,
        rejected=actions_row.rejected or 0,
        escalated=actions_row.escalated or 0,
        actions_last_30_days=actions_row.actions_last_30_days or 0,
        pending_items=pending_items or 0,
    )


async def get_dashboard_aggregates(db: AsyncSession) -> DashboardResponse:
    """
    Compute admin dashboard aggregates.

    Executes three focused aggregate queries (accounts, content, moderation)
    within the caller's session/transaction.  All counts are consistent within
    the same DB snapshot.
    """
    accounts = await _account_stats(db)
    content = await _content_volume_stats(db)
    moderation = await _moderation_stats(db)

    return DashboardResponse(
        generated_at=datetime.now(tz=timezone.utc),
        accounts=accounts,
        content=content,
        moderation=moderation,
    )
