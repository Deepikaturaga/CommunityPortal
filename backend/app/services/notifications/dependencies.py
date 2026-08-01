from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.notifications.repository import NotificationPreferenceRepository


async def get_preference_repo(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationPreferenceRepository:
    return NotificationPreferenceRepository(db)


PreferenceRepo = Annotated[NotificationPreferenceRepository, Depends(get_preference_repo)]
