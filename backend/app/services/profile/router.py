"""Profile router — GET/PUT /api/v1/profile (COMP-002 / IF-003)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.profile.schemas import ProfileResponse, ProfileUpdateRequest
from app.services.profile.service import get_profile, update_profile

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get(
    "",
    response_model=ProfileResponse,
    summary="Get own profile",
    status_code=status.HTTP_200_OK,
)
async def read_profile(
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> ProfileResponse:
    """
    Return the authenticated member's own profile.

    AC-007.x: Only the token-owning member may read their profile.
    A valid token is required; 401 is returned for missing/invalid tokens.
    """
    user = await get_profile(current_user)
    return ProfileResponse.model_validate(user)


@router.put(
    "",
    response_model=ProfileResponse,
    summary="Update own profile",
    status_code=status.HTTP_200_OK,
)
async def write_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ProfileResponse:
    """
    Update the authenticated member's own profile.

    AC-007.x: Self-only — the identity in the JWT governs which row is
    updated; no cross-user path parameter is accepted by this endpoint.
    """
    updated = await update_profile(current_user, payload, db)
    return ProfileResponse.model_validate(updated)
