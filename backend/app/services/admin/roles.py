"""Admin role-assignment service.

Business rules
--------------
* Only roles in ``ASSIGNABLE_ROLES`` (MODERATOR, CONTRIBUTOR, VIEWER) may be
  granted or revoked via this API.  ADMIN cannot be self-assigned (privilege
  escalation prevention, OWASP A01).
* A user cannot change their own role.
* The target user must exist and be active.
* Role changes are written to the database immediately; because the JWT does
  not carry the role claim, the change is visible on the target user's very
  next request — no re-login required (AC-032.1 / AC-032.2).

See ``app/core/security.py`` for the token design decision.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ASSIGNABLE_ROLES, UserRole
from app.models.user import User
from app.services.admin.roles_exceptions import (
    CannotModifySelfError,
    RoleNotAssignableError,
    UserNotFoundError,
)


async def assign_role(
    *,
    db: AsyncSession,
    target_user_id: str,
    new_role: UserRole,
    acting_user_id: str,
) -> User:
    """Assign *new_role* to the user identified by *target_user_id*.

    Returns the updated ``User`` object.

    Raises
    ------
    UserNotFoundError
        When *target_user_id* does not correspond to an active user.
    RoleNotAssignableError
        When *new_role* is not in ``ASSIGNABLE_ROLES`` (e.g. ADMIN).
    CannotModifySelfError
        When the acting admin attempts to change their own role.
    """
    _guard_self(target_user_id, acting_user_id)
    _guard_assignable(new_role)

    user = await _fetch_active_user(db, target_user_id)
    user.role = new_role
    await db.flush()  # write within the caller's transaction boundary
    return user


async def revoke_role(
    *,
    db: AsyncSession,
    target_user_id: str,
    acting_user_id: str,
    fallback_role: UserRole = UserRole.VIEWER,
) -> User:
    """Revoke the elevated role of *target_user_id*, resetting to *fallback_role*.

    *fallback_role* must itself be in ``ASSIGNABLE_ROLES``.

    Returns the updated ``User`` object.

    Raises
    ------
    UserNotFoundError
        When *target_user_id* does not correspond to an active user.
    RoleNotAssignableError
        When *fallback_role* is not assignable.
    CannotModifySelfError
        When the acting admin attempts to change their own role.
    """
    _guard_self(target_user_id, acting_user_id)
    _guard_assignable(fallback_role)

    user = await _fetch_active_user(db, target_user_id)
    user.role = fallback_role
    await db.flush()
    return user


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _guard_self(target_user_id: str, acting_user_id: str) -> None:
    if target_user_id == acting_user_id:
        raise CannotModifySelfError("An admin cannot change their own role.")


def _guard_assignable(role: UserRole) -> None:
    if role not in ASSIGNABLE_ROLES:
        raise RoleNotAssignableError(
            f"Role '{role.value}' is not assignable via this API. "
            f"Allowed: {[r.value for r in ASSIGNABLE_ROLES]}"
        )


async def _fetch_active_user(db: AsyncSession, user_id: str) -> User:
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active.is_(True))
    )
    user: User | None = result.scalar_one_or_none()
    if user is None:
        raise UserNotFoundError(f"Active user '{user_id}' not found.")
    return user
