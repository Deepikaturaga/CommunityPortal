"""Profile service — business logic layer for COMP-002 (IF-003)."""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.profile.schemas import ProfileUpdateRequest


async def get_profile(user: User) -> User:
    """
    Return the user record for self-profile view.

    Authorization is enforced at the router layer; this layer trusts
    that the supplied user is already the authenticated principal.
    """
    return user


async def update_profile(
    user: User,
    payload: ProfileUpdateRequest,
    db: AsyncSession,
) -> User:
    """
    Apply *payload* to *user* and flush to the database.

    Only explicitly supplied (non-None) fields are updated so that a
    partial PUT does not accidentally clear existing data.
    """
    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user, field, value)

    user.updated_at = datetime.now(tz=UTC)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user
