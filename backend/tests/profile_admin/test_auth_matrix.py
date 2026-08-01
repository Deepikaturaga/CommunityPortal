"""
TASK-031 – Authorization negative-test matrix across all 5 roles.

Covers: profile / admin / taxonomy endpoints.

Matrix legend
─────────────
Role rank:   viewer(0) < contributor(1) < editor(2) < admin(3) < superadmin(4)

Profile endpoints
─────────────────
  GET  /api/v1/profile/me        → 200 for ALL roles (positive baseline)
  PATCH /api/v1/profile/me       → 200 for ALL roles (self-service baseline)
  GET  /api/v1/profile/{id}      → 403 for viewer, contributor, editor  | 200 for admin, superadmin
  DELETE /api/v1/profile/{id}    → 403 for viewer, contributor, editor, admin | 204 for superadmin

Admin endpoints
───────────────
  GET  /api/v1/admin/users       → 403 for viewer, contributor, editor | 200 for admin, superadmin
  POST /api/v1/admin/users       → 403 for viewer, contributor, editor, admin | 201 for superadmin
  PATCH /api/v1/admin/users/{id} → 403 for viewer, contributor, editor | 200 for admin, superadmin
  DELETE /api/v1/admin/users/{id}→ 403 for viewer, contributor, editor, admin | 204 for superadmin

Taxonomy – vocabulary endpoints
──────────────────────────────
  GET  /api/v1/taxonomy/vocabularies     → 200 for ALL roles (positive baseline)
  POST /api/v1/taxonomy/vocabularies     → 403 for viewer, contributor | 201 for editor, admin, superadmin
  PATCH /api/v1/taxonomy/vocabularies/{id} → 403 for viewer, contributor | 200 for editor, admin, superadmin
  DELETE /api/v1/taxonomy/vocabularies/{id}→ 403 for viewer, contributor, editor | 204 for admin, superadmin

Taxonomy – term endpoints
─────────────────────────
  GET  /api/v1/taxonomy/vocabularies/{id}/terms   → 200 for ALL roles
  POST /api/v1/taxonomy/vocabularies/{id}/terms   → 403 for viewer | 201 for contributor, editor, admin, superadmin
  PATCH /api/v1/taxonomy/vocabularies/{id}/terms/{tid} → 403 for viewer, contributor | 200 for editor+
  DELETE /api/v1/taxonomy/vocabularies/{id}/terms/{tid}→ 403 for viewer, contributor, editor | 204 for admin+

Unauthenticated
───────────────
  Every protected endpoint → 403 (no bearer) for anon
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.taxonomy import TaxonomyTerm, TaxonomyVocabulary
from app.models.user import User
from tests.profile_admin.conftest import _create_user, auth_headers
from app.models.enums import UserRole

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

ALL_ROLES = [r.value for r in UserRole]
VIEWER = UserRole.VIEWER.value
CONTRIBUTOR = UserRole.CONTRIBUTOR.value
EDITOR = UserRole.EDITOR.value
ADMIN = UserRole.ADMIN.value
SUPERADMIN = UserRole.SUPERADMIN.value


# ──────────────────────────────────────────────────────────────────────────────
# Additional fixtures: vocabulary + term seeds
# ──────────────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture()
async def vocab(db_session: AsyncSession) -> TaxonomyVocabulary:
    v = TaxonomyVocabulary(
        id=str(uuid.uuid4()), slug="test-vocab", name="Test Vocab"
    )
    db_session.add(v)
    await db_session.commit()
    await db_session.refresh(v)
    return v


@pytest_asyncio.fixture()
async def term(db_session: AsyncSession, vocab: TaxonomyVocabulary) -> TaxonomyTerm:
    t = TaxonomyTerm(
        id=str(uuid.uuid4()),
        vocabulary_id=vocab.id,
        slug="test-term",
        name="Test Term",
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


# ──────────────────────────────────────────────────────────────────────────────
# Section 1: Unauthenticated → 403 everywhere
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestUnauthenticated:
    async def test_profile_me_anon(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/profile/me")
        assert resp.status_code == 403, resp.text

    async def test_profile_by_id_anon(self, client: AsyncClient, users: dict[str, User]) -> None:
        resp = await client.get(f"/api/v1/profile/{users[VIEWER].id}")
        assert resp.status_code == 403, resp.text

    async def test_profile_delete_anon(self, client: AsyncClient, users: dict[str, User]) -> None:
        resp = await client.delete(f"/api/v1/profile/{users[VIEWER].id}")
        assert resp.status_code == 403, resp.text

    async def test_admin_list_users_anon(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/admin/users")
        assert resp.status_code == 403, resp.text

    async def test_admin_create_user_anon(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/admin/users", json={
            "email": "anon@test.example",
            "password": "Test1234!",
            "role": "viewer",
        })
        assert resp.status_code == 403, resp.text

    async def test_taxonomy_vocabs_anon(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/taxonomy/vocabularies")
        assert resp.status_code == 403, resp.text

    async def test_taxonomy_create_vocab_anon(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/taxonomy/vocabularies", json={
            "slug": "anon-vocab", "name": "Anon"
        })
        assert resp.status_code == 403, resp.text

    async def test_taxonomy_terms_anon(
        self, client: AsyncClient, vocab: TaxonomyVocabulary
    ) -> None:
        resp = await client.get(f"/api/v1/taxonomy/vocabularies/{vocab.id}/terms")
        assert resp.status_code == 403, resp.text


# ──────────────────────────────────────────────────────────────────────────────
# Section 2: Profile /me – positive baseline (all roles get 200)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestProfileMeAllRoles:
    @pytest.mark.parametrize("role", ALL_ROLES)
    async def test_get_my_profile(
        self, client: AsyncClient, tokens: dict[str, str], role: str
    ) -> None:
        resp = await client.get("/api/v1/profile/me", headers=auth_headers(tokens[role]))
        assert resp.status_code == 200, f"role={role}: {resp.text}"
        assert resp.json()["role"] == role

    @pytest.mark.parametrize("role", ALL_ROLES)
    async def test_patch_my_profile(
        self, client: AsyncClient, tokens: dict[str, str], role: str
    ) -> None:
        resp = await client.patch(
            "/api/v1/profile/me",
            headers=auth_headers(tokens[role]),
            json={"full_name": f"{role} Updated"},
        )
        assert resp.status_code == 200, f"role={role}: {resp.text}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 3: Profile GET /{id} – admin+ allowed; viewer/contributor/editor → 403
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestProfileGetById:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR, EDITOR])
    async def test_forbidden_for_low_roles(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        users: dict[str, User],
        role: str,
    ) -> None:
        target_id = users[VIEWER].id
        resp = await client.get(
            f"/api/v1/profile/{target_id}", headers=auth_headers(tokens[role])
        )
        assert resp.status_code == 403, f"Expected 403 for role={role}, got {resp.status_code}"

    @pytest.mark.parametrize("role", [ADMIN, SUPERADMIN])
    async def test_allowed_for_admin_plus(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        users: dict[str, User],
        role: str,
    ) -> None:
        target_id = users[VIEWER].id
        resp = await client.get(
            f"/api/v1/profile/{target_id}", headers=auth_headers(tokens[role])
        )
        assert resp.status_code == 200, f"Expected 200 for role={role}, got {resp.status_code}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 4: Profile DELETE /{id} – superadmin only; all others → 403
# ──────────────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture()
async def deletable_user(db_session: AsyncSession) -> User:
    return await _create_user(db_session, UserRole.VIEWER, suffix="deletable")


@pytest.mark.asyncio
class TestProfileDelete:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR, EDITOR, ADMIN])
    async def test_forbidden_for_non_superadmin(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        deletable_user: User,
        role: str,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/profile/{deletable_user.id}", headers=auth_headers(tokens[role])
        )
        assert resp.status_code == 403, f"Expected 403 for role={role}, got {resp.status_code}"

    async def test_superadmin_can_delete(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        deletable_user: User,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/profile/{deletable_user.id}",
            headers=auth_headers(tokens[SUPERADMIN]),
        )
        assert resp.status_code == 204, f"Expected 204, got {resp.status_code}: {resp.text}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 5: Admin GET /users – admin+ allowed; low roles → 403
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestAdminListUsers:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR, EDITOR])
    async def test_forbidden(
        self, client: AsyncClient, tokens: dict[str, str], role: str
    ) -> None:
        resp = await client.get("/api/v1/admin/users", headers=auth_headers(tokens[role]))
        assert resp.status_code == 403, f"role={role}: {resp.status_code}"

    @pytest.mark.parametrize("role", [ADMIN, SUPERADMIN])
    async def test_allowed(
        self, client: AsyncClient, tokens: dict[str, str], role: str
    ) -> None:
        resp = await client.get("/api/v1/admin/users", headers=auth_headers(tokens[role]))
        assert resp.status_code == 200, f"role={role}: {resp.status_code}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 6: Admin POST /users – superadmin only
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestAdminCreateUser:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR, EDITOR, ADMIN])
    async def test_forbidden_for_non_superadmin(
        self, client: AsyncClient, tokens: dict[str, str], role: str
    ) -> None:
        resp = await client.post(
            "/api/v1/admin/users",
            headers=auth_headers(tokens[role]),
            json={"email": f"new-{role}@x.example", "password": "Test1234!", "role": "viewer"},
        )
        assert resp.status_code == 403, f"role={role}: {resp.status_code}"

    async def test_superadmin_can_create(
        self, client: AsyncClient, tokens: dict[str, str]
    ) -> None:
        resp = await client.post(
            "/api/v1/admin/users",
            headers=auth_headers(tokens[SUPERADMIN]),
            json={
                "email": f"created-{uuid.uuid4().hex[:6]}@x.example",
                "password": "Test1234!",
                "role": "viewer",
            },
        )
        assert resp.status_code == 201, resp.text


# ──────────────────────────────────────────────────────────────────────────────
# Section 7: Admin PATCH /users/{id} – admin+ allowed; low roles → 403
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestAdminUpdateUser:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR, EDITOR])
    async def test_forbidden(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        users: dict[str, User],
        role: str,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/admin/users/{users[VIEWER].id}",
            headers=auth_headers(tokens[role]),
            json={"full_name": "hacked"},
        )
        assert resp.status_code == 403, f"role={role}: {resp.status_code}"

    @pytest.mark.parametrize("role", [ADMIN, SUPERADMIN])
    async def test_allowed(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        users: dict[str, User],
        role: str,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/admin/users/{users[VIEWER].id}",
            headers=auth_headers(tokens[role]),
            json={"full_name": f"Updated by {role}"},
        )
        assert resp.status_code == 200, f"role={role}: {resp.status_code}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 8: Admin DELETE /users/{id} – superadmin only
# ──────────────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture()
async def admin_deletable_user(db_session: AsyncSession) -> User:
    return await _create_user(db_session, UserRole.VIEWER, suffix="admin-del")


@pytest.mark.asyncio
class TestAdminDeleteUser:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR, EDITOR, ADMIN])
    async def test_forbidden_for_non_superadmin(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        admin_deletable_user: User,
        role: str,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/admin/users/{admin_deletable_user.id}",
            headers=auth_headers(tokens[role]),
        )
        assert resp.status_code == 403, f"role={role}: {resp.status_code}"

    async def test_superadmin_can_delete(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        admin_deletable_user: User,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/admin/users/{admin_deletable_user.id}",
            headers=auth_headers(tokens[SUPERADMIN]),
        )
        assert resp.status_code == 204, resp.text


# ──────────────────────────────────────────────────────────────────────────────
# Section 9: Taxonomy GET /vocabularies – all roles 200
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestTaxonomyListVocabularies:
    @pytest.mark.parametrize("role", ALL_ROLES)
    async def test_all_roles_can_list(
        self, client: AsyncClient, tokens: dict[str, str], role: str
    ) -> None:
        resp = await client.get(
            "/api/v1/taxonomy/vocabularies", headers=auth_headers(tokens[role])
        )
        assert resp.status_code == 200, f"role={role}: {resp.status_code}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 10: Taxonomy POST /vocabularies – editor+ allowed; viewer/contributor → 403
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestTaxonomyCreateVocabulary:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR])
    async def test_forbidden(
        self, client: AsyncClient, tokens: dict[str, str], role: str
    ) -> None:
        resp = await client.post(
            "/api/v1/taxonomy/vocabularies",
            headers=auth_headers(tokens[role]),
            json={"slug": f"slug-{role}", "name": "Vocab"},
        )
        assert resp.status_code == 403, f"role={role}: {resp.status_code}"

    @pytest.mark.parametrize("role", [EDITOR, ADMIN, SUPERADMIN])
    async def test_allowed(
        self, client: AsyncClient, tokens: dict[str, str], role: str
    ) -> None:
        slug = f"vocab-{role}-{uuid.uuid4().hex[:6]}"
        resp = await client.post(
            "/api/v1/taxonomy/vocabularies",
            headers=auth_headers(tokens[role]),
            json={"slug": slug, "name": f"Vocab {role}"},
        )
        assert resp.status_code == 201, f"role={role}: {resp.text}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 11: Taxonomy PATCH /vocabularies/{id} – editor+ allowed; viewer/contributor → 403
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestTaxonomyUpdateVocabulary:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR])
    async def test_forbidden(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        vocab: TaxonomyVocabulary,
        role: str,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/taxonomy/vocabularies/{vocab.id}",
            headers=auth_headers(tokens[role]),
            json={"name": "Hacked"},
        )
        assert resp.status_code == 403, f"role={role}: {resp.status_code}"

    @pytest.mark.parametrize("role", [EDITOR, ADMIN, SUPERADMIN])
    async def test_allowed(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        vocab: TaxonomyVocabulary,
        role: str,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/taxonomy/vocabularies/{vocab.id}",
            headers=auth_headers(tokens[role]),
            json={"name": f"Updated by {role}"},
        )
        assert resp.status_code == 200, f"role={role}: {resp.text}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 12: Taxonomy DELETE /vocabularies/{id} – admin+ allowed; viewer/contributor/editor → 403
# ──────────────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture()
async def deletable_vocab(db_session: AsyncSession) -> TaxonomyVocabulary:
    v = TaxonomyVocabulary(
        id=str(uuid.uuid4()), slug=f"del-vocab-{uuid.uuid4().hex[:6]}", name="Deletable"
    )
    db_session.add(v)
    await db_session.commit()
    await db_session.refresh(v)
    return v


@pytest_asyncio.fixture()
async def deletable_vocab_for_admin(db_session: AsyncSession) -> TaxonomyVocabulary:
    v = TaxonomyVocabulary(
        id=str(uuid.uuid4()), slug=f"del-admin-{uuid.uuid4().hex[:6]}", name="Deletable Admin"
    )
    db_session.add(v)
    await db_session.commit()
    await db_session.refresh(v)
    return v


@pytest.mark.asyncio
class TestTaxonomyDeleteVocabulary:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR, EDITOR])
    async def test_forbidden(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        deletable_vocab: TaxonomyVocabulary,
        role: str,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/taxonomy/vocabularies/{deletable_vocab.id}",
            headers=auth_headers(tokens[role]),
        )
        assert resp.status_code == 403, f"role={role}: {resp.status_code}"

    async def test_admin_can_delete(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        deletable_vocab_for_admin: TaxonomyVocabulary,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/taxonomy/vocabularies/{deletable_vocab_for_admin.id}",
            headers=auth_headers(tokens[ADMIN]),
        )
        assert resp.status_code == 204, resp.text

    async def test_superadmin_can_delete(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        db_session: AsyncSession,
    ) -> None:
        v = TaxonomyVocabulary(
            id=str(uuid.uuid4()), slug=f"sa-del-{uuid.uuid4().hex[:6]}", name="SA Del"
        )
        db_session.add(v)
        await db_session.commit()
        resp = await client.delete(
            f"/api/v1/taxonomy/vocabularies/{v.id}",
            headers=auth_headers(tokens[SUPERADMIN]),
        )
        assert resp.status_code == 204, resp.text


# ──────────────────────────────────────────────────────────────────────────────
# Section 13: Term GET – all roles 200
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestTermListAllRoles:
    @pytest.mark.parametrize("role", ALL_ROLES)
    async def test_all_roles_can_list_terms(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        vocab: TaxonomyVocabulary,
        role: str,
    ) -> None:
        resp = await client.get(
            f"/api/v1/taxonomy/vocabularies/{vocab.id}/terms",
            headers=auth_headers(tokens[role]),
        )
        assert resp.status_code == 200, f"role={role}: {resp.status_code}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 14: Term POST – viewer → 403; contributor+ → 201
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestTermCreate:
    async def test_viewer_forbidden(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        vocab: TaxonomyVocabulary,
    ) -> None:
        resp = await client.post(
            f"/api/v1/taxonomy/vocabularies/{vocab.id}/terms",
            headers=auth_headers(tokens[VIEWER]),
            json={"slug": "blocked-term", "name": "Blocked"},
        )
        assert resp.status_code == 403, resp.text

    @pytest.mark.parametrize("role", [CONTRIBUTOR, EDITOR, ADMIN, SUPERADMIN])
    async def test_contributor_plus_allowed(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        vocab: TaxonomyVocabulary,
        role: str,
    ) -> None:
        slug = f"term-{role}-{uuid.uuid4().hex[:6]}"
        resp = await client.post(
            f"/api/v1/taxonomy/vocabularies/{vocab.id}/terms",
            headers=auth_headers(tokens[role]),
            json={"slug": slug, "name": f"Term {role}"},
        )
        assert resp.status_code == 201, f"role={role}: {resp.text}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 15: Term PATCH – editor+ allowed; viewer/contributor → 403
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestTermUpdate:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR])
    async def test_forbidden(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        vocab: TaxonomyVocabulary,
        term: TaxonomyTerm,
        role: str,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/taxonomy/vocabularies/{vocab.id}/terms/{term.id}",
            headers=auth_headers(tokens[role]),
            json={"name": "Hacked"},
        )
        assert resp.status_code == 403, f"role={role}: {resp.status_code}"

    @pytest.mark.parametrize("role", [EDITOR, ADMIN, SUPERADMIN])
    async def test_allowed(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        vocab: TaxonomyVocabulary,
        term: TaxonomyTerm,
        role: str,
    ) -> None:
        resp = await client.patch(
            f"/api/v1/taxonomy/vocabularies/{vocab.id}/terms/{term.id}",
            headers=auth_headers(tokens[role]),
            json={"name": f"Updated by {role}"},
        )
        assert resp.status_code == 200, f"role={role}: {resp.text}"


# ──────────────────────────────────────────────────────────────────────────────
# Section 16: Term DELETE – admin+ allowed; viewer/contributor/editor → 403
# ──────────────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture()
async def deletable_term(
    db_session: AsyncSession, vocab: TaxonomyVocabulary
) -> TaxonomyTerm:
    t = TaxonomyTerm(
        id=str(uuid.uuid4()),
        vocabulary_id=vocab.id,
        slug=f"del-term-{uuid.uuid4().hex[:6]}",
        name="Deletable Term",
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


@pytest_asyncio.fixture()
async def deletable_term_for_admin(
    db_session: AsyncSession, vocab: TaxonomyVocabulary
) -> TaxonomyTerm:
    t = TaxonomyTerm(
        id=str(uuid.uuid4()),
        vocabulary_id=vocab.id,
        slug=f"del-term-admin-{uuid.uuid4().hex[:6]}",
        name="Deletable Term Admin",
    )
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


@pytest.mark.asyncio
class TestTermDelete:
    @pytest.mark.parametrize("role", [VIEWER, CONTRIBUTOR, EDITOR])
    async def test_forbidden(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        vocab: TaxonomyVocabulary,
        deletable_term: TaxonomyTerm,
        role: str,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/taxonomy/vocabularies/{vocab.id}/terms/{deletable_term.id}",
            headers=auth_headers(tokens[role]),
        )
        assert resp.status_code == 403, f"role={role}: {resp.status_code}"

    async def test_admin_can_delete(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        vocab: TaxonomyVocabulary,
        deletable_term_for_admin: TaxonomyTerm,
    ) -> None:
        resp = await client.delete(
            f"/api/v1/taxonomy/vocabularies/{vocab.id}/terms/{deletable_term_for_admin.id}",
            headers=auth_headers(tokens[ADMIN]),
        )
        assert resp.status_code == 204, resp.text

    async def test_superadmin_can_delete(
        self,
        client: AsyncClient,
        tokens: dict[str, str],
        vocab: TaxonomyVocabulary,
        db_session: AsyncSession,
    ) -> None:
        t = TaxonomyTerm(
            id=str(uuid.uuid4()),
            vocabulary_id=vocab.id,
            slug=f"sa-del-term-{uuid.uuid4().hex[:6]}",
            name="SA Del Term",
        )
        db_session.add(t)
        await db_session.commit()
        resp = await client.delete(
            f"/api/v1/taxonomy/vocabularies/{vocab.id}/terms/{t.id}",
            headers=auth_headers(tokens[SUPERADMIN]),
        )
        assert resp.status_code == 204, resp.text
