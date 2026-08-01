"""Post service business logic.

Covers:
  AC-016.x  Create post
  AC-017.x  Read single post
  AC-018.x  List / paginate posts
  AC-019.x  Update post (own content; moderators may update any)
  AC-020.x  Soft-delete post (sets status=deleted; hard-delete forbidden via model)
  AC-021.x  Per-author post creation rate limiting (enforced in service layer)
"""
from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, ContentStatus, CONTENT_TRANSITIONS
from app.services.posts.schemas import PostCreateRequest, PostOut, PostPage, PostUpdateRequest

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class PostNotFoundError(Exception):
    """Raised when a requested post does not exist."""


class PostForbiddenError(Exception):
    """Raised when the caller is not permitted to perform the operation."""


class PostDeletedError(Exception):
    """Raised when a caller attempts to modify a soft-deleted post."""


class RateLimitError(Exception):
    """Raised when the per-author post-creation rate limit is exceeded.

    AC-021.1 — max 10 posts per author per rolling 60-second window.
    """


# ---------------------------------------------------------------------------
# Rate-limit constants
# ---------------------------------------------------------------------------
RATE_LIMIT_MAX_POSTS: int = 10
RATE_LIMIT_WINDOW_SECONDS: int = 60


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------


async def _get_post_or_raise(db: AsyncSession, post_id: str) -> Content:
    """Load a Content row or raise ``PostNotFoundError``."""
    stmt = select(Content).where(Content.id == post_id)
    post: Content | None = (await db.execute(stmt)).scalar_one_or_none()
    if post is None:
        raise PostNotFoundError(f"Post {post_id!r} not found.")
    return post


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def create_post(
    db: AsyncSession,
    *,
    author_id: str,
    payload: PostCreateRequest,
) -> PostOut:
    """AC-016 — create a new post.

    AC-021.1 — enforce rate limit: max ``RATE_LIMIT_MAX_POSTS`` posts per
    author within a rolling ``RATE_LIMIT_WINDOW_SECONDS``-second window.
    """
    window_start = datetime.now(UTC) - timedelta(seconds=RATE_LIMIT_WINDOW_SECONDS)
    count_stmt = (
        select(func.count())
        .select_from(Content)
        .where(
            Content.author_id == author_id,
            Content.created_at >= window_start,
        )
    )
    recent_count: int = (await db.execute(count_stmt)).scalar_one()
    if recent_count >= RATE_LIMIT_MAX_POSTS:
        raise RateLimitError(
            f"Rate limit exceeded: max {RATE_LIMIT_MAX_POSTS} posts per "
            f"{RATE_LIMIT_WINDOW_SECONDS}s window."
        )

    post = Content(
        author_id=author_id,
        title=payload.title,
        body=payload.body,
        status=ContentStatus.active,
        is_locked=False,
    )
    db.add(post)
    await db.flush()
    return PostOut.model_validate(post)


async def get_post(
    db: AsyncSession,
    *,
    post_id: str,
    caller_id: str,
    caller_role: str,
) -> PostOut:
    """AC-017 — retrieve a single post.

    Regular users may only read their own posts or non-deleted content.
    Moderators/admins may read any post.

    AC-017.3 — deleted posts are hidden from regular users (404 semantics).
    """
    post = await _get_post_or_raise(db, post_id)

    is_privileged = caller_role in ("moderator", "admin")
    if post.status == ContentStatus.deleted and not is_privileged:
        raise PostNotFoundError(f"Post {post_id!r} not found.")

    return PostOut.model_validate(post)


async def list_posts(
    db: AsyncSession,
    *,
    caller_id: str,
    caller_role: str,
    author_id: str | None = None,
    status_filter: ContentStatus | None = None,
    page: int = 1,
    page_size: int = 20,
) -> PostPage:
    """AC-018 — paginated list.

    * Regular users: see only non-deleted posts (or their own posts of any
      status when ``author_id == caller_id``).
    * Moderators/admins: see all posts regardless of status.
    """
    is_privileged = caller_role in ("moderator", "admin")

    filters: list = []

    if author_id:
        filters.append(Content.author_id == author_id)

    if status_filter:
        filters.append(Content.status == status_filter)
    elif not is_privileged:
        # Regular users cannot see deleted posts unless they are the author.
        if author_id != caller_id:
            filters.append(Content.status != ContentStatus.deleted)

    count_stmt = select(func.count()).select_from(Content)
    if filters:
        count_stmt = count_stmt.where(*filters)
    total: int = (await db.execute(count_stmt)).scalar_one()

    offset = (page - 1) * page_size
    rows_stmt = (
        select(Content)
        .order_by(Content.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    if filters:
        rows_stmt = rows_stmt.where(*filters)
    rows = list((await db.execute(rows_stmt)).scalars().all())

    return PostPage(
        items=[PostOut.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


async def update_post(
    db: AsyncSession,
    *,
    post_id: str,
    caller_id: str,
    caller_role: str,
    payload: PostUpdateRequest,
) -> PostOut:
    """AC-019 — update title and/or body.

    * Authors may edit their own non-deleted, non-locked posts.
    * Moderators/admins may edit any non-deleted post.

    AC-019.4 — locked posts cannot be edited.
    AC-019.5 — deleted posts cannot be edited.
    """
    post = await _get_post_or_raise(db, post_id)

    is_privileged = caller_role in ("moderator", "admin")

    if post.status == ContentStatus.deleted:
        raise PostDeletedError(f"Post {post_id!r} has been deleted and cannot be edited.")

    if not is_privileged and post.author_id != caller_id:
        raise PostForbiddenError("You may only edit your own posts.")

    if post.is_locked and not is_privileged:
        raise PostForbiddenError("Post is locked and cannot be edited.")

    if payload.title is not None:
        post.title = payload.title
    if payload.body is not None:
        post.body = payload.body
    post.updated_at = datetime.now(UTC)
    db.add(post)
    await db.flush()
    return PostOut.model_validate(post)


async def delete_post(
    db: AsyncSession,
    *,
    post_id: str,
    caller_id: str,
    caller_role: str,
) -> None:
    """AC-020 — soft-delete a post (status → deleted).

    * Authors may delete their own posts.
    * Moderators/admins may delete any post.
    * Already-deleted posts are idempotent (no error).
    """
    post = await _get_post_or_raise(db, post_id)

    is_privileged = caller_role in ("moderator", "admin")
    if not is_privileged and post.author_id != caller_id:
        raise PostForbiddenError("You may only delete your own posts.")

    if post.status == ContentStatus.deleted:
        # Idempotent.
        return

    allowed = CONTENT_TRANSITIONS.get(post.status, set())
    if ContentStatus.deleted not in allowed:
        # Model invariant: no status can transition away from deleted, but
        # all other statuses allow deletion — this branch should not be
        # reached in practice.
        raise PostForbiddenError(
            f"Post in status {post.status!r} cannot be deleted via this path."
        )

    post.status = ContentStatus.deleted
    post.updated_at = datetime.now(UTC)
    db.add(post)
    await db.flush()
