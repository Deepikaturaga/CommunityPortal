from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.notifications.enums import NotificationCategory, NotificationChannel
from app.services.notifications.models import Notification, NotificationPreference
from app.services.notifications.schemas import NotificationListParams


class NotificationPreferenceRepository:
    """
    All queries are scoped to the caller's user_id – self-only access is
    enforced here (not only in the router) per §7 of the implementation contract.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Preferences ──────────────────────────────────────────────────────────

    async def list_preferences(self, user_id: str) -> list[NotificationPreference]:
        result = await self._db.execute(
            select(NotificationPreference)
            .where(NotificationPreference.user_id == user_id)
            .order_by(NotificationPreference.channel, NotificationPreference.category)
        )
        return list(result.scalars().all())

    async def get_preference(
        self,
        user_id: str,
        channel: NotificationChannel,
        category: NotificationCategory,
    ) -> NotificationPreference | None:
        result = await self._db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id,
                NotificationPreference.channel == channel,
                NotificationPreference.category == category,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_preference(
        self,
        user_id: str,
        channel: NotificationChannel,
        category: NotificationCategory,
        opted_out: bool,
    ) -> NotificationPreference:
        """
        Idempotent upsert: create row if absent, update opted_out otherwise.
        Returns the persisted preference (flushed, not yet committed – the
        caller's session/unit-of-work commits on success).
        """
        existing = await self.get_preference(user_id, channel, category)
        if existing is None:
            pref = NotificationPreference(
                user_id=user_id,
                channel=channel,
                category=category,
                opted_out=opted_out,
            )
            self._db.add(pref)
            await self._db.flush()
            await self._db.refresh(pref)
            return pref

        # Only update when the value actually changes (avoids spurious updated_at bumps)
        if existing.opted_out != opted_out:
            await self._db.execute(
                update(NotificationPreference)
                .where(NotificationPreference.id == existing.id)
                .values(opted_out=opted_out)
                .execution_options(synchronize_session="fetch")
            )
            await self._db.flush()
            await self._db.refresh(existing)
        return existing

    # ── Notifications ─────────────────────────────────────────────────────────

    async def list_notifications(
        self,
        user_id: str,
        params: NotificationListParams,
    ) -> tuple[list[Notification], int]:
        """
        Returns (page_items, total_count). Bounded by page_size ≤ 100.
        All filters default to None → no-op (show all for this user).
        """
        base_where: list[Any] = [Notification.user_id == user_id]

        if params.channel is not None:
            base_where.append(Notification.channel == params.channel)
        if params.category is not None:
            base_where.append(Notification.category == params.category)
        if params.status is not None:
            base_where.append(Notification.status == params.status)

        # total count
        count_result = await self._db.execute(
            select(func.count()).select_from(Notification).where(*base_where)
        )
        total: int = count_result.scalar_one()

        # page
        offset = (params.page - 1) * params.page_size
        rows_result = await self._db.execute(
            select(Notification)
            .where(*base_where)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(params.page_size)
        )
        items = list(rows_result.scalars().all())
        return items, total
