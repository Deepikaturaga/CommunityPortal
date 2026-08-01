"""
Notification preference and list router (IF-010 / COMP-008).

Routes
------
GET  /api/v1/notifications/preferences
    List all preference rows for the authenticated user.

GET  /api/v1/notifications/preferences/{channel}/{category}
    Read a single preference.  Returns the default (opted_in) if the row
    does not exist yet, without persisting anything.

PUT  /api/v1/notifications/preferences/{channel}/{category}
    Upsert the opted_out flag for one (channel, category) pair.
    Idempotent – safe to retry.

GET  /api/v1/notifications/
    Paginated, filterable notification list for the authenticated user.

Access control
--------------
All endpoints enforce *self-only* access: the user_id is taken exclusively
from the validated JWT payload – never from a path/query parameter supplied
by the caller.  This satisfies AC-029.x and IF-010 self-only requirement.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Query, status

from app.core.security import CurrentUser
from app.services.notifications.dependencies import PreferenceRepo
from app.services.notifications.enums import (
    NotificationCategory,
    NotificationChannel,
    NotificationStatus,
)
from app.services.notifications.schemas import (
    NotificationListParams,
    NotificationListResponse,
    NotificationRead,
    PreferenceListResponse,
    PreferencePut,
    PreferenceRead,
)

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
)

_NULL_UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)

# ── Preference endpoints ───────────────────────────────────────────────────────


@router.get(
    "/preferences",
    response_model=PreferenceListResponse,
    summary="List notification preferences",
    status_code=status.HTTP_200_OK,
)
async def list_preferences(
    current_user: CurrentUser,
    repo: PreferenceRepo,
) -> PreferenceListResponse:
    """Return all persisted preference rows for the calling user."""
    items = await repo.list_preferences(current_user.user_id)
    return PreferenceListResponse(
        items=[PreferenceRead.model_validate(p) for p in items],
        total=len(items),
    )


@router.get(
    "/preferences/{channel}/{category}",
    response_model=PreferenceRead,
    summary="Get a single notification preference",
    status_code=status.HTTP_200_OK,
)
async def get_preference(
    channel: NotificationChannel,
    category: NotificationCategory,
    current_user: CurrentUser,
    repo: PreferenceRepo,
) -> PreferenceRead:
    """
    Return the preference for (channel, category).  If the row has never been
    written the default is opted_in (opted_out=False), returned as a synthetic
    response without persisting.
    """
    pref = await repo.get_preference(current_user.user_id, channel, category)
    if pref is None:
        # Return default without writing – no side-effects on GET
        return PreferenceRead(
            id=_NULL_UUID,
            user_id=current_user.user_id,
            channel=channel,
            category=category,
            opted_out=False,
            created_at=_EPOCH,
            updated_at=_EPOCH,
        )
    return PreferenceRead.model_validate(pref)


@router.put(
    "/preferences/{channel}/{category}",
    response_model=PreferenceRead,
    summary="Set a notification preference opt-out flag",
    status_code=status.HTTP_200_OK,
)
async def put_preference(
    channel: NotificationChannel,
    category: NotificationCategory,
    body: PreferencePut,
    current_user: CurrentUser,
    repo: PreferenceRepo,
) -> PreferenceRead:
    """
    Persist the opted_out flag for (channel, category).  Idempotent.
    The user_id is taken from the JWT – callers cannot set preferences for
    other users (self-only access, AC-029.x).
    """
    pref = await repo.upsert_preference(
        user_id=current_user.user_id,
        channel=channel,
        category=category,
        opted_out=body.opted_out,
    )
    return PreferenceRead.model_validate(pref)


# ── Notification list endpoint ────────────────────────────────────────────────


@router.get(
    "/",
    response_model=NotificationListResponse,
    summary="List notifications for the authenticated user",
    status_code=status.HTTP_200_OK,
)
async def list_notifications(
    current_user: CurrentUser,
    repo: PreferenceRepo,
    channel: NotificationChannel | None = Query(default=None),
    category: NotificationCategory | None = Query(default=None),
    notification_status: NotificationStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> NotificationListResponse:
    """
    Paginated notification list filtered by channel / category / status.
    Results are ordered by created_at DESC (newest first).
    Maximum page_size is 100 (bounded read).
    """
    params = NotificationListParams(
        channel=channel,
        category=category,
        status=notification_status,
        page=page,
        page_size=page_size,
    )
    items, total = await repo.list_notifications(current_user.user_id, params)
    return NotificationListResponse(
        items=[NotificationRead.model_validate(n) for n in items],
        total=total,
        page=page,
        page_size=page_size,
    )
