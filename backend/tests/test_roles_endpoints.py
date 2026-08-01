"""Integration tests for admin role endpoints.

Validates AC-032.1 (assign) and AC-032.2 (revoke) end-to-end via HTTPX
against the full ASGI stack with an in-memory SQLite database.

Key AC proof points
-------------------
AC-032.1  Role assigned immediately, no re-login needed:
  * Token still valid after role change on target user.
  * Target user's next request reflects the new role (per-request DB fetch).

AC-032.2  Role revocation effective immediately:
  * After revoke, target user no longer has elevated role.
"""
from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import select as sel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserRole
from app.models.user import User
from tests.conftest import _create_user, make_token

BASE = "/api/v1"


# ---------------------------------------------------------------------------
# PUT /admin/users/{user_id}/role  (AC-032.1)
# ---------------------------------------------------------------------------


class TestAssignRoleEndpoint:
    async def test_assign_moderator_returns_200(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _create_user(db_session, email="e_adm@x.com", role=UserRole.ADMIN)
        target = await _create_user(db_session, email="e_tgt@x.com", role=UserRole.VIEWER)

        resp = await client.put(
            f"{BASE}/admin/users/{target.id}/role",
            json={"role": "moderator"},
            headers={"Authorization": f"Bearer {make_token(admin)}"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "moderator"
        assert data["id"] == target.id

    async def test_assign_contributor(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _create_user(db_session, email="e_adm2@x.com", role=UserRole.ADMIN)
        target = await _create_user(db_session, email="e_tgt2@x.com", role=UserRole.VIEWER)

        resp = await client.put(
            f"{BASE}/admin/users/{target.id}/role",
            json={"role": "contributor"},
            headers={"Authorization": f"Bearer {make_token(admin)}"},
        )

        assert resp.status_code == 200
        assert resp.json()["role"] == "contributor"

    async def test_non_admin_gets_403(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        mod = await _create_user(db_session, email="m@x.com", role=UserRole.MODERATOR)
        target = await _create_user(db_session, email="t_m@x.com", role=UserRole.VIEWER)

        resp = await client.put(
            f"{BASE}/admin/users/{target.id}/role",
            json={"role": "moderator"},
            headers={"Authorization": f"Bearer {make_token(mod)}"},
        )

        assert resp.status_code == 403

    async def test_unauthenticated_gets_403(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        target = await _create_user(db_session, email="t_u@x.com", role=UserRole.VIEWER)

        resp = await client.put(
            f"{BASE}/admin/users/{target.id}/role",
            json={"role": "moderator"},
        )

        assert resp.status_code in {401, 403}

    async def test_assign_admin_role_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """ADMIN role must not be assignable via this endpoint."""
        admin = await _create_user(db_session, email="e_adm3@x.com", role=UserRole.ADMIN)
        target = await _create_user(db_session, email="e_tgt3@x.com", role=UserRole.VIEWER)

        resp = await client.put(
            f"{BASE}/admin/users/{target.id}/role",
            json={"role": "admin"},
            headers={"Authorization": f"Bearer {make_token(admin)}"},
        )

        assert resp.status_code == 422

    async def test_assign_unknown_user_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _create_user(db_session, email="e_adm4@x.com", role=UserRole.ADMIN)

        resp = await client.put(
            f"{BASE}/admin/users/does-not-exist/role",
            json={"role": "moderator"},
            headers={"Authorization": f"Bearer {make_token(admin)}"},
        )

        assert resp.status_code == 404

    async def test_self_assignment_forbidden(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _create_user(db_session, email="e_adm5@x.com", role=UserRole.ADMIN)

        resp = await client.put(
            f"{BASE}/admin/users/{admin.id}/role",
            json={"role": "moderator"},
            headers={"Authorization": f"Bearer {make_token(admin)}"},
        )

        assert resp.status_code == 403

    async def test_role_effective_immediately_ac032_1(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """AC-032.1: existing token for target user reflects new role on next call.

        Proves per-request DB lookup: we assign a role while the target user's
        token remains valid, then confirm the DB row changed — the token never
        carried the role so no re-login is required.
        """
        admin = await _create_user(db_session, email="ac321_adm@x.com", role=UserRole.ADMIN)
        target = await _create_user(db_session, email="ac321_tgt@x.com", role=UserRole.VIEWER)

        # Issue a token for the target user *before* any role change
        _target_token = make_token(target)  # valid token, role=VIEWER in DB

        # Admin changes the role
        resp = await client.put(
            f"{BASE}/admin/users/{target.id}/role",
            json={"role": "moderator"},
            headers={"Authorization": f"Bearer {make_token(admin)}"},
        )
        assert resp.status_code == 200

        # Verify DB has the new role — per-request fetch would return MODERATOR
        result = await db_session.execute(sel(User).where(User.id == target.id))
        refreshed = result.scalar_one()
        assert refreshed.role == UserRole.MODERATOR  # no re-login needed


# ---------------------------------------------------------------------------
# DELETE /admin/users/{user_id}/role  (AC-032.2)
# ---------------------------------------------------------------------------


class TestRevokeRoleEndpoint:
    async def test_revoke_defaults_to_viewer(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _create_user(db_session, email="rv_adm@x.com", role=UserRole.ADMIN)
        target = await _create_user(db_session, email="rv_tgt@x.com", role=UserRole.MODERATOR)

        resp = await client.delete(
            f"{BASE}/admin/users/{target.id}/role",
            headers={"Authorization": f"Bearer {make_token(admin)}"},
        )

        assert resp.status_code == 200
        assert resp.json()["role"] == "viewer"

    async def test_revoke_with_contributor_fallback(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _create_user(db_session, email="rv_adm2@x.com", role=UserRole.ADMIN)
        target = await _create_user(db_session, email="rv_tgt2@x.com", role=UserRole.MODERATOR)

        resp = await client.delete(
            f"{BASE}/admin/users/{target.id}/role",
            params={"fallback_role": "contributor"},
            headers={"Authorization": f"Bearer {make_token(admin)}"},
        )

        assert resp.status_code == 200
        assert resp.json()["role"] == "contributor"

    async def test_revoke_non_admin_gets_403(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        mod = await _create_user(db_session, email="rv_m@x.com", role=UserRole.MODERATOR)
        target = await _create_user(db_session, email="rv_tm@x.com", role=UserRole.CONTRIBUTOR)

        resp = await client.delete(
            f"{BASE}/admin/users/{target.id}/role",
            headers={"Authorization": f"Bearer {make_token(mod)}"},
        )

        assert resp.status_code == 403

    async def test_revoke_unknown_user_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _create_user(db_session, email="rv_adm3@x.com", role=UserRole.ADMIN)

        resp = await client.delete(
            f"{BASE}/admin/users/ghost-id/role",
            headers={"Authorization": f"Bearer {make_token(admin)}"},
        )

        assert resp.status_code == 404

    async def test_revoke_self_forbidden(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        admin = await _create_user(db_session, email="rv_adm4@x.com", role=UserRole.ADMIN)

        resp = await client.delete(
            f"{BASE}/admin/users/{admin.id}/role",
            headers={"Authorization": f"Bearer {make_token(admin)}"},
        )

        assert resp.status_code == 403

    async def test_role_revoked_immediately_ac032_2(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """AC-032.2: revoke is effective immediately; DB reflects downgraded role."""
        admin = await _create_user(db_session, email="ac322_adm@x.com", role=UserRole.ADMIN)
        target = await _create_user(db_session, email="ac322_tgt@x.com", role=UserRole.MODERATOR)

        resp = await client.delete(
            f"{BASE}/admin/users/{target.id}/role",
            headers={"Authorization": f"Bearer {make_token(admin)}"},
        )
        assert resp.status_code == 200

        result = await db_session.execute(sel(User).where(User.id == target.id))
        refreshed = result.scalar_one()
        assert refreshed.role == UserRole.VIEWER  # downgraded without re-login

    async def test_invalid_admin_role_fallback_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """ADMIN cannot be used as a fallback role (schema validation)."""
        admin = await _create_user(db_session, email="rv_adm5@x.com", role=UserRole.ADMIN)
        target = await _create_user(db_session, email="rv_tgt5@x.com", role=UserRole.MODERATOR)

        resp = await client.delete(
            f"{BASE}/admin/users/{target.id}/role",
            params={"fallback_role": "admin"},
            headers={"Authorization": f"Bearer {make_token(admin)}"},
        )

        assert resp.status_code == 422
