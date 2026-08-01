"""Unit tests for the admin roles service layer (no HTTP).

Covers
------
* assign_role – happy path, user not found, self-assignment guard,
  ADMIN role blocked, idempotent re-assignment
* revoke_role – happy path, custom fallback, user not found,
  self-assignment guard, invalid fallback
"""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserRole
from app.services.admin.roles import assign_role, revoke_role
from app.services.admin.roles_exceptions import (
    CannotModifySelfError,
    RoleNotAssignableError,
    UserNotFoundError,
)
from tests.conftest import _create_user


class TestAssignRole:
    async def test_assign_moderator_happy_path(self, db_session: AsyncSession) -> None:
        admin = await _create_user(db_session, email="a@x.com", role=UserRole.ADMIN)
        target = await _create_user(db_session, email="t@x.com", role=UserRole.VIEWER)

        updated = await assign_role(
            db=db_session,
            target_user_id=target.id,
            new_role=UserRole.MODERATOR,
            acting_user_id=admin.id,
        )

        assert updated.role == UserRole.MODERATOR
        assert updated.id == target.id

    async def test_assign_contributor_happy_path(self, db_session: AsyncSession) -> None:
        admin = await _create_user(db_session, email="a2@x.com", role=UserRole.ADMIN)
        target = await _create_user(db_session, email="t2@x.com", role=UserRole.VIEWER)

        updated = await assign_role(
            db=db_session,
            target_user_id=target.id,
            new_role=UserRole.CONTRIBUTOR,
            acting_user_id=admin.id,
        )

        assert updated.role == UserRole.CONTRIBUTOR

    async def test_assign_viewer_happy_path(self, db_session: AsyncSession) -> None:
        admin = await _create_user(db_session, email="a3@x.com", role=UserRole.ADMIN)
        target = await _create_user(db_session, email="t3@x.com", role=UserRole.MODERATOR)

        updated = await assign_role(
            db=db_session,
            target_user_id=target.id,
            new_role=UserRole.VIEWER,
            acting_user_id=admin.id,
        )

        assert updated.role == UserRole.VIEWER

    async def test_assign_role_returns_updated_user(self, db_session: AsyncSession) -> None:
        """The returned object reflects the new role (DB write verified)."""
        admin = await _create_user(db_session, email="a4@x.com", role=UserRole.ADMIN)
        target = await _create_user(db_session, email="t4@x.com", role=UserRole.VIEWER)

        updated = await assign_role(
            db=db_session,
            target_user_id=target.id,
            new_role=UserRole.MODERATOR,
            acting_user_id=admin.id,
        )
        assert updated.role == UserRole.MODERATOR

    async def test_user_not_found_raises(self, db_session: AsyncSession) -> None:
        admin = await _create_user(db_session, email="a5@x.com", role=UserRole.ADMIN)

        with pytest.raises(UserNotFoundError):
            await assign_role(
                db=db_session,
                target_user_id="nonexistent-id",
                new_role=UserRole.MODERATOR,
                acting_user_id=admin.id,
            )

    async def test_inactive_user_not_found(self, db_session: AsyncSession) -> None:
        admin = await _create_user(db_session, email="a6@x.com", role=UserRole.ADMIN)
        inactive = await _create_user(
            db_session, email="inactive@x.com", role=UserRole.VIEWER, is_active=False
        )

        with pytest.raises(UserNotFoundError):
            await assign_role(
                db=db_session,
                target_user_id=inactive.id,
                new_role=UserRole.MODERATOR,
                acting_user_id=admin.id,
            )

    async def test_cannot_assign_admin_role(self, db_session: AsyncSession) -> None:
        """ADMIN role is not in ASSIGNABLE_ROLES – privilege escalation guard."""
        admin = await _create_user(db_session, email="a7@x.com", role=UserRole.ADMIN)
        target = await _create_user(db_session, email="t7@x.com", role=UserRole.VIEWER)

        with pytest.raises(RoleNotAssignableError):
            await assign_role(
                db=db_session,
                target_user_id=target.id,
                new_role=UserRole.ADMIN,
                acting_user_id=admin.id,
            )

    async def test_cannot_modify_self(self, db_session: AsyncSession) -> None:
        admin = await _create_user(db_session, email="a8@x.com", role=UserRole.ADMIN)

        with pytest.raises(CannotModifySelfError):
            await assign_role(
                db=db_session,
                target_user_id=admin.id,
                new_role=UserRole.MODERATOR,
                acting_user_id=admin.id,
            )

    async def test_idempotent_reassignment(self, db_session: AsyncSession) -> None:
        """Assigning the same role twice should succeed without error."""
        admin = await _create_user(db_session, email="a9@x.com", role=UserRole.ADMIN)
        target = await _create_user(db_session, email="t9@x.com", role=UserRole.MODERATOR)

        updated = await assign_role(
            db=db_session,
            target_user_id=target.id,
            new_role=UserRole.MODERATOR,
            acting_user_id=admin.id,
        )
        assert updated.role == UserRole.MODERATOR


class TestRevokeRole:
    async def test_revoke_defaults_to_viewer(self, db_session: AsyncSession) -> None:
        admin = await _create_user(db_session, email="ra1@x.com", role=UserRole.ADMIN)
        target = await _create_user(db_session, email="rt1@x.com", role=UserRole.MODERATOR)

        updated = await revoke_role(
            db=db_session,
            target_user_id=target.id,
            acting_user_id=admin.id,
        )

        assert updated.role == UserRole.VIEWER

    async def test_revoke_with_custom_fallback(self, db_session: AsyncSession) -> None:
        admin = await _create_user(db_session, email="ra2@x.com", role=UserRole.ADMIN)
        target = await _create_user(db_session, email="rt2@x.com", role=UserRole.MODERATOR)

        updated = await revoke_role(
            db=db_session,
            target_user_id=target.id,
            acting_user_id=admin.id,
            fallback_role=UserRole.CONTRIBUTOR,
        )

        assert updated.role == UserRole.CONTRIBUTOR

    async def test_revoke_user_not_found(self, db_session: AsyncSession) -> None:
        admin = await _create_user(db_session, email="ra3@x.com", role=UserRole.ADMIN)

        with pytest.raises(UserNotFoundError):
            await revoke_role(
                db=db_session,
                target_user_id="ghost",
                acting_user_id=admin.id,
            )

    async def test_revoke_cannot_modify_self(self, db_session: AsyncSession) -> None:
        admin = await _create_user(db_session, email="ra4@x.com", role=UserRole.ADMIN)

        with pytest.raises(CannotModifySelfError):
            await revoke_role(
                db=db_session,
                target_user_id=admin.id,
                acting_user_id=admin.id,
            )

    async def test_revoke_admin_fallback_blocked(self, db_session: AsyncSession) -> None:
        """Cannot use ADMIN as a fallback role (it is not assignable)."""
        admin = await _create_user(db_session, email="ra5@x.com", role=UserRole.ADMIN)
        target = await _create_user(db_session, email="rt5@x.com", role=UserRole.MODERATOR)

        with pytest.raises(RoleNotAssignableError):
            await revoke_role(
                db=db_session,
                target_user_id=target.id,
                acting_user_id=admin.id,
                fallback_role=UserRole.ADMIN,
            )
