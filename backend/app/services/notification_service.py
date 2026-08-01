from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationKind
from app.models.user import User


async def create_notification(
    db: AsyncSession,
    recipient_id: int,
    kind: NotificationKind,
    title: str,
    body: str | None = None,
    resource_url: str | None = None,
) -> Notification:
    notif = Notification(
        recipient_id=recipient_id,
        kind=kind.value,
        title=title,
        body=body,
        resource_url=resource_url,
        is_read=False,
    )
    db.add(notif)
    await db.flush()
    return notif


async def list_notifications(
    db: AsyncSession, recipient: User, page: int = 1, page_size: int = 20, unread_only: bool = False
) -> tuple[list[Notification], int]:
    q = select(Notification).where(Notification.recipient_id == recipient.id)
    if unread_only:
        q = q.where(Notification.is_read == False)  # noqa: E712
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()
    q = q.order_by(Notification.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def mark_read(db: AsyncSession, recipient: User, notification_ids: list[int]) -> int:
    result = await db.execute(
        select(Notification).where(
            Notification.id.in_(notification_ids),
            Notification.recipient_id == recipient.id,
        )
    )
    notifications = result.scalars().all()
    count = 0
    for n in notifications:
        if not n.is_read:
            n.is_read = True
            db.add(n)
            count += 1
    await db.flush()
    return count


async def mark_all_read(db: AsyncSession, recipient: User) -> int:
    result = await db.execute(
        select(Notification).where(
            Notification.recipient_id == recipient.id,
            Notification.is_read == False,  # noqa: E712
        )
    )
    notifications = result.scalars().all()
    for n in notifications:
        n.is_read = True
        db.add(n)
    await db.flush()
    return len(notifications)


async def get_unread_count(db: AsyncSession, recipient: User) -> int:
    result = await db.execute(
        select(func.count()).where(
            Notification.recipient_id == recipient.id,
            Notification.is_read == False,  # noqa: E712
        )
    )
    return result.scalar_one()
