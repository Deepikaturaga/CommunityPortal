"""Moderation service — queue listing and action dispatch (COMP-003 commands, IF-009).

Responsibilities:
  - list_queue: paginated query of content by status (default: flagged)
  - apply_action: validate transition, apply to content, write immutable audit record (AC-014.3/4)

All reads/writes happen within a caller-supplied AsyncSession; the caller owns the transaction
boundary (committed by get_db dependency on success, rolled back on exception).
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import CONTENT_TRANSITIONS, Content, ContentStatus
from app.models.moderation import ModerationAction, ModerationAuditRecord
from app.services.moderation.schemas import (
    AuditRecordOut,
    ContentSummary,
    ModerationActionResponse,
    QueuePage,
)

# Map inbound ModerationAction commands to target ContentStatus (COMP-003 command contract)
_ACTION_TARGET_STATUS: dict[ModerationAction, ContentStatus] = {
    ModerationAction.lock: ContentStatus.locked,
    ModerationAction.hide: ContentStatus.hidden,
    ModerationAction.delete: ContentStatus.deleted,
}


class ModerationServiceError(Exception):
    """Base error for moderation service failures."""


class ContentNotFoundError(ModerationServiceError):
    """Raised when the target content item does not exist."""


class InvalidTransitionError(ModerationServiceError):
    """Raised when the requested action is not a valid state-machine transition."""


async def list_queue(
    db: AsyncSession,
    *,
    status: ContentStatus = ContentStatus.flagged,
    page: int = 1,
    page_size: int = 20,
) -> QueuePage:
    """
    Return a paginated list of content items in the given status (default: flagged).

    Only items whose status matches the requested filter are returned.
    Results are ordered by created_at ascending (oldest-first — FIFO moderation queue).
    """
    offset = (page - 1) * page_size

    count_stmt = select(func.count()).where(Content.status == status)
    total: int = (await db.execute(count_stmt)).scalar_one()

    rows_stmt = (
        select(Content)
        .where(Content.status == status)
        .order_by(Content.created_at.asc())
        .offset(offset)
        .limit(page_size)
    )
    rows = list((await db.execute(rows_stmt)).scalars().all())

    return QueuePage(
        items=[ContentSummary.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


async def apply_action(
    db: AsyncSession,
    *,
    content_id: str,
    moderator_id: str,
    action: ModerationAction,
    reason: str | None = None,
) -> ModerationActionResponse:
    """
    Issue a moderation command (lock / hide / delete) to a content item (COMP-003).

    Steps:
      1. Load content — 404 if missing.
      2. Validate state-machine transition — 422 if illegal.
      3. Mutate content.status (and content.is_locked when action == lock).
      4. Append an immutable ModerationAuditRecord (AC-014.3).
      5. Return the result envelope; caller commits the session.

    The audit record is protected against mutation by ORM events on the model (AC-014.4).
    """
    # 1. Load content
    stmt = select(Content).where(Content.id == content_id)
    content: Content | None = (await db.execute(stmt)).scalar_one_or_none()
    if content is None:
        raise ContentNotFoundError(f"Content '{content_id}' not found")

    previous_status = content.status
    target_status = _ACTION_TARGET_STATUS[action]

    # 2. Validate transition
    if target_status not in CONTENT_TRANSITIONS.get(previous_status, set()):
        raise InvalidTransitionError(
            f"Cannot transition content from '{previous_status}' to '{target_status}' "
            f"via action '{action}'"
        )

    # 3. Mutate content
    content.status = target_status
    content.is_locked = action == ModerationAction.lock
    content.updated_at = datetime.now(timezone.utc)
    db.add(content)

    # 4. Append immutable audit record (AC-014.3)
    audit = ModerationAuditRecord(
        content_id=content_id,
        moderator_id=moderator_id,
        action=action,
        reason=reason,
        previous_status=previous_status.value,
        new_status=target_status.value,
    )
    db.add(audit)

    # Flush so audit.id and audit.created_at are populated before serialization
    await db.flush()

    return ModerationActionResponse(
        content_id=content_id,
        new_status=target_status,
        audit_record=AuditRecordOut.model_validate(audit),
    )
