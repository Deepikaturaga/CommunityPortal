"""
Unit tests for app/services/posts/visibility.py

VER-002: Draft post visibility rules
  - Unauthenticated caller gets 404 on a draft post
  - Wrong-user (non-owner, non-admin) gets 404 on a draft post
  - Post owner gets the post back for their own draft
  - Admin gets the post back for any draft
  - Published posts are visible to everyone (None, reader, author, admin)

VER-004: Ownership / edit-rights enforcement
  - Owner can edit own post (published or draft)
  - Admin can edit any post
  - Non-owner, non-admin raises 403 on edit
  - Non-owner, non-admin raises 403 on delete
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

from app.core.enums import PostStatus, UserRole
from app.models.post import Post
from app.models.user import User
from app.services.posts.visibility import (
    assert_can_delete,
    assert_can_edit,
    assert_post_visible,
    assert_post_visible_and_editable,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _user(role: UserRole, uid: uuid.UUID | None = None) -> User:
    uid = uid or uuid.uuid4()
    return User(
        id=uid,
        email=f"{uid}@test.com",
        hashed_password="x",
        display_name="U",
        role=role,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _post(author: User, status: PostStatus) -> Post:
    pid = uuid.uuid4()
    return Post(
        id=pid,
        title="T",
        slug=f"slug-{pid}",
        body="B",
        status=status,
        author_id=author.id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


# ===========================================================================
# VER-002 — assert_post_visible
# ===========================================================================


class TestDraftVisibility:
    """AC-017.1: Draft posts are only visible to owner or admin."""

    def test_none_post_raises_404(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            assert_post_visible(None, viewer=None)
        assert exc_info.value.status_code == 404

    def test_draft_unauthenticated_raises_404(self) -> None:
        author = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.DRAFT)
        with pytest.raises(HTTPException) as exc_info:
            assert_post_visible(post, viewer=None)
        assert exc_info.value.status_code == 404, "Must be 404 not 403 (AC-017.1)"

    def test_draft_non_owner_reader_raises_404(self) -> None:
        author = _user(UserRole.AUTHOR)
        reader = _user(UserRole.READER)
        post = _post(author, PostStatus.DRAFT)
        with pytest.raises(HTTPException) as exc_info:
            assert_post_visible(post, viewer=reader)
        assert exc_info.value.status_code == 404

    def test_draft_non_owner_author_raises_404(self) -> None:
        author = _user(UserRole.AUTHOR)
        other = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.DRAFT)
        with pytest.raises(HTTPException) as exc_info:
            assert_post_visible(post, viewer=other)
        assert exc_info.value.status_code == 404

    def test_draft_owner_can_see_own_draft(self) -> None:
        author = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.DRAFT)
        result = assert_post_visible(post, viewer=author)
        assert result is post

    def test_draft_admin_can_see_any_draft(self) -> None:
        author = _user(UserRole.AUTHOR)
        admin = _user(UserRole.ADMIN)
        post = _post(author, PostStatus.DRAFT)
        result = assert_post_visible(post, viewer=admin)
        assert result is post

    def test_published_visible_to_none(self) -> None:
        author = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.PUBLISHED)
        result = assert_post_visible(post, viewer=None)
        assert result is post

    def test_published_visible_to_reader(self) -> None:
        author = _user(UserRole.AUTHOR)
        reader = _user(UserRole.READER)
        post = _post(author, PostStatus.PUBLISHED)
        assert assert_post_visible(post, viewer=reader) is post

    def test_published_visible_to_different_author(self) -> None:
        author = _user(UserRole.AUTHOR)
        other = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.PUBLISHED)
        assert assert_post_visible(post, viewer=other) is post

    def test_published_visible_to_admin(self) -> None:
        author = _user(UserRole.AUTHOR)
        admin = _user(UserRole.ADMIN)
        post = _post(author, PostStatus.PUBLISHED)
        assert assert_post_visible(post, viewer=admin) is post


# ===========================================================================
# VER-004 — assert_can_edit / assert_can_delete
# ===========================================================================


class TestOwnershipEnforcement:
    """AC-019.3 / AC-020.x: Only owners and admins may edit/delete."""

    def test_owner_can_edit_own_published_post(self) -> None:
        author = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.PUBLISHED)
        assert_can_edit(post, editor=author)  # no exception

    def test_owner_can_edit_own_draft(self) -> None:
        author = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.DRAFT)
        assert_can_edit(post, editor=author)

    def test_admin_can_edit_any_post(self) -> None:
        author = _user(UserRole.AUTHOR)
        admin = _user(UserRole.ADMIN)
        post = _post(author, PostStatus.PUBLISHED)
        assert_can_edit(post, editor=admin)

    def test_non_owner_reader_cannot_edit(self) -> None:
        author = _user(UserRole.AUTHOR)
        reader = _user(UserRole.READER)
        post = _post(author, PostStatus.PUBLISHED)
        with pytest.raises(HTTPException) as exc_info:
            assert_can_edit(post, editor=reader)
        assert exc_info.value.status_code == 403

    def test_non_owner_author_cannot_edit(self) -> None:
        author = _user(UserRole.AUTHOR)
        other = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.PUBLISHED)
        with pytest.raises(HTTPException) as exc_info:
            assert_can_edit(post, editor=other)
        assert exc_info.value.status_code == 403

    def test_owner_can_delete_own_post(self) -> None:
        author = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.PUBLISHED)
        assert_can_delete(post, actor=author)

    def test_admin_can_delete_any_post(self) -> None:
        author = _user(UserRole.AUTHOR)
        admin = _user(UserRole.ADMIN)
        post = _post(author, PostStatus.DRAFT)
        assert_can_delete(post, actor=admin)

    def test_non_owner_cannot_delete(self) -> None:
        author = _user(UserRole.AUTHOR)
        other = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.PUBLISHED)
        with pytest.raises(HTTPException) as exc_info:
            assert_can_delete(post, actor=other)
        assert exc_info.value.status_code == 403


# ===========================================================================
# Combined: assert_post_visible_and_editable
# ===========================================================================


class TestVisibleAndEditable:
    """Combined visibility + edit-right check used by update/delete endpoints."""

    def test_owner_of_draft_can_edit(self) -> None:
        author = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.DRAFT)
        result = assert_post_visible_and_editable(post, actor=author)
        assert result is post

    def test_stranger_on_draft_gets_404_not_403(self) -> None:
        """Non-owner of a draft must get 404 (existence not leaked)."""
        author = _user(UserRole.AUTHOR)
        stranger = _user(UserRole.AUTHOR)
        post = _post(author, PostStatus.DRAFT)
        with pytest.raises(HTTPException) as exc_info:
            assert_post_visible_and_editable(post, actor=stranger)
        assert exc_info.value.status_code == 404  # visibility check fires first

    def test_non_owner_on_published_gets_403(self) -> None:
        author = _user(UserRole.AUTHOR)
        other = _user(UserRole.READER)
        post = _post(author, PostStatus.PUBLISHED)
        with pytest.raises(HTTPException) as exc_info:
            assert_post_visible_and_editable(post, actor=other)
        assert exc_info.value.status_code == 403

    def test_none_post_gives_404(self) -> None:
        actor = _user(UserRole.ADMIN)
        with pytest.raises(HTTPException) as exc_info:
            assert_post_visible_and_editable(None, actor=actor)
        assert exc_info.value.status_code == 404
