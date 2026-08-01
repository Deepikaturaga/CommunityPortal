"""
Tests for KB revision history — PHASE-031 / TASK-047.

Covers
------
VER-002  AC-026.1  Revision is created (and immutable) on every article save.
VER-004  AC-026.2  Only the article's author, moderators, and admins may read
                   revision history; all other roles receive HTTP 403.

Test strategy
-------------
* Pure-in-memory unit tests use SQLite (async, via aiosqlite) so no Postgres is
  required in CI.  SQLite does not support the immutability trigger, but the ORM-
  level listener is still exercised.
* The DB-level trigger is validated in the optional ``@pytest.mark.integration``
  suite (Postgres required).
* HTTP-layer tests use FastAPI's ``AsyncClient`` with ``ASGITransport`` so the
  full dependency-injection stack is exercised without a live server.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_current_active_user, get_db
from app.core.exceptions import ForbiddenError, NotFoundError
from app.db.base_class import Base
from app.main import app
from app.models.kb_article import KBArticle
from app.models.user import User, UserRole
from app.services.kb import revisions as revision_service

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture()
async def db_session():
    """In-memory SQLite async session for unit tests (no Postgres required)."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def _make_user(role: UserRole, user_id: int = 1) -> User:
    u = User()
    u.id = user_id
    u.role = role
    u.is_active = True
    u.email = f"user{user_id}@example.com"
    u.hashed_password = "x"
    return u


def _make_article(article_id: int = 1, author_id: int = 1) -> KBArticle:
    a = KBArticle()
    a.id = article_id
    a.author_id = author_id
    a.title = "Initial title"
    a.content = "Initial content"
    return a


async def _persist(session: AsyncSession, *objs: object) -> None:
    for obj in objs:
        session.add(obj)
    await session.flush()


# ── VER-002 / AC-026.1 ────────────────────────────────────────────────────────


class TestRevisionCreation:
    """AC-026.1 — a revision is recorded on every article save."""

    @pytest.mark.asyncio
    async def test_record_revision_creates_row(self, db_session: AsyncSession) -> None:
        author = _make_user(UserRole.author, user_id=10)
        article = _make_article(article_id=5, author_id=10)
        await _persist(db_session, author, article)

        revision = await revision_service.record_revision(
            db_session,
            article=article,
            editor_id=author.id,
            change_summary="Initial save",
        )
        await db_session.commit()

        assert revision.id is not None
        assert revision.revision_number == 1
        assert revision.article_id == 5
        assert revision.editor_id == 10
        assert revision.title_snapshot == "Initial title"
        assert revision.content_snapshot == "Initial content"
        assert revision.change_summary == "Initial save"

    @pytest.mark.asyncio
    async def test_each_save_increments_revision_number(
        self, db_session: AsyncSession
    ) -> None:
        author = _make_user(UserRole.author, user_id=11)
        article = _make_article(article_id=6, author_id=11)
        await _persist(db_session, author, article)

        r1 = await revision_service.record_revision(
            db_session, article=article, editor_id=author.id
        )
        await db_session.flush()

        article.title = "Updated title"
        article.content = "Updated content"
        r2 = await revision_service.record_revision(
            db_session, article=article, editor_id=author.id
        )
        await db_session.commit()

        assert r1.revision_number == 1
        assert r2.revision_number == 2

    @pytest.mark.asyncio
    async def test_revision_orm_update_blocked(self, db_session: AsyncSession) -> None:
        """ORM-level listener raises RuntimeError on attempted UPDATE."""
        author = _make_user(UserRole.author, user_id=12)
        article = _make_article(article_id=7, author_id=12)
        await _persist(db_session, author, article)

        revision = await revision_service.record_revision(
            db_session, article=article, editor_id=author.id
        )
        await db_session.commit()

        with pytest.raises(RuntimeError, match="append-only"):
            revision.title_snapshot = "tampered"
            await db_session.flush()

    @pytest.mark.asyncio
    async def test_revision_orm_delete_blocked(self, db_session: AsyncSession) -> None:
        """ORM-level listener raises RuntimeError on attempted DELETE."""
        author = _make_user(UserRole.author, user_id=13)
        article = _make_article(article_id=8, author_id=13)
        await _persist(db_session, author, article)

        revision = await revision_service.record_revision(
            db_session, article=article, editor_id=author.id
        )
        await db_session.commit()

        with pytest.raises(RuntimeError, match="append-only"):
            await db_session.delete(revision)
            await db_session.flush()


# ── VER-004 / AC-026.2 ────────────────────────────────────────────────────────


class TestRevisionAccess:
    """AC-026.2 — only author (own article), moderator, or admin may read revisions."""

    @pytest.mark.asyncio
    async def test_admin_can_read_any_revision(self, db_session: AsyncSession) -> None:
        admin = _make_user(UserRole.admin, user_id=20)
        author = _make_user(UserRole.author, user_id=21)
        article = _make_article(article_id=10, author_id=21)
        await _persist(db_session, admin, author, article)
        await revision_service.record_revision(
            db_session, article=article, editor_id=21
        )
        await db_session.commit()

        result = await revision_service.get_revisions(
            db_session, article_id=10, current_user=admin
        )
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_moderator_can_read_any_revision(
        self, db_session: AsyncSession
    ) -> None:
        mod = _make_user(UserRole.moderator, user_id=22)
        author = _make_user(UserRole.author, user_id=23)
        article = _make_article(article_id=11, author_id=23)
        await _persist(db_session, mod, author, article)
        await revision_service.record_revision(
            db_session, article=article, editor_id=23
        )
        await db_session.commit()

        result = await revision_service.get_revisions(
            db_session, article_id=11, current_user=mod
        )
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_author_can_read_own_article_revisions(
        self, db_session: AsyncSession
    ) -> None:
        author = _make_user(UserRole.author, user_id=24)
        article = _make_article(article_id=12, author_id=24)
        await _persist(db_session, author, article)
        await revision_service.record_revision(
            db_session, article=article, editor_id=24
        )
        await db_session.commit()

        result = await revision_service.get_revisions(
            db_session, article_id=12, current_user=author
        )
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_author_cannot_read_other_authors_revisions(
        self, db_session: AsyncSession
    ) -> None:
        owner = _make_user(UserRole.author, user_id=25)
        interloper = _make_user(UserRole.author, user_id=26)
        article = _make_article(article_id=13, author_id=25)
        await _persist(db_session, owner, interloper, article)
        await revision_service.record_revision(
            db_session, article=article, editor_id=25
        )
        await db_session.commit()

        with pytest.raises(ForbiddenError):
            await revision_service.get_revisions(
                db_session, article_id=13, current_user=interloper
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "role",
        [
            r
            for r in UserRole
            if r not in (UserRole.admin, UserRole.moderator, UserRole.author)
        ],
    )
    async def test_non_privileged_roles_forbidden(
        self, db_session: AsyncSession, role: UserRole
    ) -> None:
        owner = _make_user(UserRole.author, user_id=30)
        article = _make_article(article_id=14, author_id=30)
        caller = _make_user(role, user_id=31)
        await _persist(db_session, owner, caller, article)
        await revision_service.record_revision(
            db_session, article=article, editor_id=30
        )
        await db_session.commit()

        with pytest.raises(ForbiddenError):
            await revision_service.get_revisions(
                db_session, article_id=14, current_user=caller
            )

    @pytest.mark.asyncio
    async def test_get_revision_by_id_not_found(self, db_session: AsyncSession) -> None:
        admin = _make_user(UserRole.admin, user_id=40)
        author = _make_user(UserRole.author, user_id=41)
        article = _make_article(article_id=15, author_id=41)
        await _persist(db_session, admin, author, article)
        await db_session.commit()

        with pytest.raises(NotFoundError):
            await revision_service.get_revision_by_id(
                db_session,
                article_id=15,
                revision_id=9999,
                current_user=admin,
            )


# ── HTTP integration tests ────────────────────────────────────────────────────


def _auth_override(user: User):  # type: ignore[return]
    async def _dep() -> User:
        return user

    return _dep


def _db_override(session: AsyncSession):  # type: ignore[return]
    async def _dep():
        yield session

    return _dep


class TestRevisionHTTP:
    """Smoke tests through the FastAPI router."""

    @pytest.mark.asyncio
    async def test_list_revisions_403_for_non_privileged(
        self, db_session: AsyncSession
    ) -> None:
        """A non-privileged role receives HTTP 403."""
        non_priv_roles = [
            r
            for r in UserRole
            if r not in (UserRole.admin, UserRole.moderator, UserRole.author)
        ]
        assert non_priv_roles, "No non-privileged role found — update the test"
        reader = _make_user(non_priv_roles[0], user_id=50)
        author = _make_user(UserRole.author, user_id=51)
        article = _make_article(article_id=20, author_id=51)
        await _persist(db_session, reader, author, article)
        await revision_service.record_revision(
            db_session, article=article, editor_id=51
        )
        await db_session.commit()

        app.dependency_overrides[get_current_active_user] = _auth_override(reader)
        app.dependency_overrides[get_db] = _db_override(db_session)
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/kb/articles/20/revisions")
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_list_revisions_200_for_moderator(
        self, db_session: AsyncSession
    ) -> None:
        mod = _make_user(UserRole.moderator, user_id=52)
        author = _make_user(UserRole.author, user_id=53)
        article = _make_article(article_id=21, author_id=53)
        await _persist(db_session, mod, author, article)
        await revision_service.record_revision(
            db_session, article=article, editor_id=53
        )
        await db_session.commit()

        app.dependency_overrides[get_current_active_user] = _auth_override(mod)
        app.dependency_overrides[get_db] = _db_override(db_session)
        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/kb/articles/21/revisions")
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert len(body["items"]) == 1
        assert body["items"][0]["revision_number"] == 1
