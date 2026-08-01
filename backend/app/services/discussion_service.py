from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ForbiddenError
from app.models.discussion import Discussion, DiscussionStatus
from app.models.post import Post
from app.models.user import User
from app.schemas.discussion_schemas import (
    DiscussionCreateRequest,
    DiscussionUpdateRequest,
    PostCreateRequest,
    PostUpdateRequest,
)

# Allowed discussion state transitions
_DISCUSSION_TRANSITIONS: dict[str, list[str]] = {
    DiscussionStatus.open.value: [DiscussionStatus.closed.value, DiscussionStatus.locked.value],
    DiscussionStatus.closed.value: [DiscussionStatus.open.value, DiscussionStatus.archived.value],
    DiscussionStatus.locked.value: [DiscussionStatus.archived.value],
    DiscussionStatus.archived.value: [],
}


async def create_discussion(db: AsyncSession, author: User, req: DiscussionCreateRequest) -> Discussion:
    discussion = Discussion(
        title=req.title,
        body=req.body,
        author_id=author.id,
        tags=req.tags,
        status=DiscussionStatus.open.value,
    )
    db.add(discussion)
    await db.flush()
    return discussion


async def list_discussions(
    db: AsyncSession, page: int = 1, page_size: int = 20, status: str | None = None
) -> tuple[list[Discussion], int]:
    q = select(Discussion)
    if status:
        q = q.where(Discussion.status == status)
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()
    q = q.order_by(Discussion.is_pinned.desc(), Discussion.created_at.desc())
    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def get_discussion(db: AsyncSession, discussion_id: int) -> Discussion:
    result = await db.execute(select(Discussion).where(Discussion.id == discussion_id))
    d = result.scalar_one_or_none()
    if not d:
        raise NotFoundError("Discussion not found")
    # increment view count
    d.view_count += 1
    db.add(d)
    await db.flush()
    return d


async def update_discussion(
    db: AsyncSession, actor: User, discussion_id: int, req: DiscussionUpdateRequest
) -> Discussion:
    result = await db.execute(select(Discussion).where(Discussion.id == discussion_id))
    d = result.scalar_one_or_none()
    if not d:
        raise NotFoundError("Discussion not found")
    if d.author_id != actor.id and actor.role not in ("admin", "moderator"):
        raise ForbiddenError("Not allowed to update this discussion")
    if req.status and req.status != d.status:
        allowed = _DISCUSSION_TRANSITIONS.get(d.status, [])
        if req.status not in allowed:
            raise ConflictError(f"Cannot transition from {d.status} to {req.status}")
        d.status = req.status
    if req.title is not None:
        d.title = req.title
    if req.body is not None:
        d.body = req.body
    if req.tags is not None:
        d.tags = req.tags
    db.add(d)
    await db.flush()
    return d


async def delete_discussion(db: AsyncSession, actor: User, discussion_id: int) -> None:
    result = await db.execute(select(Discussion).where(Discussion.id == discussion_id))
    d = result.scalar_one_or_none()
    if not d:
        raise NotFoundError("Discussion not found")
    if d.author_id != actor.id and actor.role not in ("admin", "moderator"):
        raise ForbiddenError("Not allowed to delete this discussion")
    await db.delete(d)
    await db.flush()


# ── Posts ──────────────────────────────────────────────────────────────────


async def create_post(
    db: AsyncSession, author: User, discussion_id: int, req: PostCreateRequest
) -> Post:
    result = await db.execute(select(Discussion).where(Discussion.id == discussion_id))
    d = result.scalar_one_or_none()
    if not d:
        raise NotFoundError("Discussion not found")
    if d.status in (DiscussionStatus.locked.value, DiscussionStatus.archived.value):
        raise ConflictError("Discussion is locked or archived")
    post = Post(
        body=req.body,
        discussion_id=discussion_id,
        author_id=author.id,
        parent_id=req.parent_id,
    )
    db.add(post)
    await db.flush()
    return post


async def list_posts(
    db: AsyncSession, discussion_id: int, page: int = 1, page_size: int = 20
) -> tuple[list[Post], int]:
    q = select(Post).where(Post.discussion_id == discussion_id, Post.is_deleted == False)  # noqa: E712
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()
    q = q.order_by(Post.created_at.asc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def get_post(db: AsyncSession, post_id: int) -> Post:
    result = await db.execute(select(Post).where(Post.id == post_id, Post.is_deleted == False))  # noqa: E712
    post = result.scalar_one_or_none()
    if not post:
        raise NotFoundError("Post not found")
    return post


async def update_post(db: AsyncSession, actor: User, post_id: int, req: PostUpdateRequest) -> Post:
    post = await get_post(db, post_id)
    if post.author_id != actor.id and actor.role not in ("admin", "moderator"):
        raise ForbiddenError("Not allowed to edit this post")
    post.body = req.body
    db.add(post)
    await db.flush()
    return post


async def delete_post(db: AsyncSession, actor: User, post_id: int) -> None:
    post = await get_post(db, post_id)
    if post.author_id != actor.id and actor.role not in ("admin", "moderator"):
        raise ForbiddenError("Not allowed to delete this post")
    post.is_deleted = True
    db.add(post)
    await db.flush()


async def mark_accepted_answer(db: AsyncSession, actor: User, discussion_id: int, post_id: int) -> Post:
    result = await db.execute(select(Discussion).where(Discussion.id == discussion_id))
    d = result.scalar_one_or_none()
    if not d:
        raise NotFoundError("Discussion not found")
    if d.author_id != actor.id and actor.role not in ("admin", "moderator"):
        raise ForbiddenError("Only discussion author or moderator can mark accepted answer")
    post = await get_post(db, post_id)
    if post.discussion_id != discussion_id:
        raise ConflictError("Post does not belong to this discussion")
    # unmark any existing
    existing = await db.execute(
        select(Post).where(Post.discussion_id == discussion_id, Post.is_accepted_answer == True)  # noqa: E712
    )
    for p in existing.scalars().all():
        p.is_accepted_answer = False
        db.add(p)
    post.is_accepted_answer = True
    db.add(post)
    await db.flush()
    return post
