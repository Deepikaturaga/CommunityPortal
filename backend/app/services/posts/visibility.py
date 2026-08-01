"""
Post visibility rules -- AC-017.1, AC-019.3
============================================

Rules enforced here:
- DRAFT posts are only visible to their author and to admins.
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from app.models.post import Post
    from app.models.user import User
def _is_admin(user: "User") -> bool:
def _is_owner(post: "Post", user: "User") -> bool:
def _can_view_draft(post: "Post", viewer: "User | None") -> bool:
def assert_post_visible(post: "Post | None", viewer: "User | None") -> "Post":
        # Return 404 -- not 403 -- to avoid leaking draft existence (AC-017.1)
def assert_can_edit(post: "Post", editor: "User") -> None:
def assert_can_delete(post: "Post", actor: "User") -> None:
    """Alias of assert_can_edit -- same ownership semantics apply to deletion."""
def assert_post_visible_and_editable(post: "Post | None", actor: "User") -> "Post":
- Any other caller receives HTTP 404 (not 403) to avoid leaking draft existence.
- Edit (PUT/PATCH) and delete (DELETE) operations additionally require ownership
  or admin role (AC-019.x, AC-020.x).

All public-facing helpers raise HTTPException so routers can remain thin.
"""

from __future__ import annotations

from fastapi import HTTPException, status

from app.core.enums import PostStatus, UserRole


# ---------------------------------------------------------------------------
# Primitive predicates
# ---------------------------------------------------------------------------


    return user.role == UserRole.ADMIN


    return post.author_id == user.id


    """Return True when *viewer* is allowed to see a DRAFT post."""
    if viewer is None:
        return False
    return _is_owner(post, viewer) or _is_admin(viewer)


# ---------------------------------------------------------------------------
# Visibility gate (AC-017.1)
# ---------------------------------------------------------------------------


    """
    Ensure *viewer* may see *post*.

    Raises HTTP 404 in all cases where the post should not be visible so that
    draft existence is not disclosed to unauthorised callers.

    Returns the post unchanged when access is permitted.
    """
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if post.status == PostStatus.DRAFT and not _can_view_draft(post, viewer):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    return post


# ---------------------------------------------------------------------------
# Ownership gate (AC-019.3 / AC-020.x)
# ---------------------------------------------------------------------------


    """
    Ensure *editor* is allowed to mutate (edit or delete) *post*.

    Authors may only edit their own posts.  Admins may edit any post.
    Raises HTTP 403 on failure.
    """
    if _is_admin(editor) or _is_owner(post, editor):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to modify this post",
    )


    assert_can_edit(post, actor)


# ---------------------------------------------------------------------------
# Convenience: combined visibility + ownership (for edit/delete endpoints)
# ---------------------------------------------------------------------------


    """
    Resolve visibility for the *actor* (who is authenticated) and then check
    edit rights.  Draft posts are already visible to their own author, so a
    single author calling an edit endpoint receives the correct behaviour.

    Returns the resolved post on success.
    """
    resolved = assert_post_visible(post, actor)
    assert_can_edit(resolved, actor)
    return resolved
