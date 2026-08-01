from __future__ import annotations

import re

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ForbiddenError
from app.models.kb_article import KBArticle, ArticleStatus
from app.models.user import User
from app.schemas.kb_schemas import KBArticleCreateRequest, KBArticleUpdateRequest


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:300]


async def _unique_slug(db: AsyncSession, base_slug: str) -> str:
    slug = base_slug
    i = 1
    while True:
        result = await db.execute(select(KBArticle).where(KBArticle.slug == slug))
        if not result.scalar_one_or_none():
            return slug
        slug = f"{base_slug}-{i}"
        i += 1


async def create_article(db: AsyncSession, author: User, req: KBArticleCreateRequest) -> KBArticle:
    slug = await _unique_slug(db, _slugify(req.title))
    article = KBArticle(
        title=req.title,
        slug=slug,
        body=req.body,
        summary=req.summary,
        author_id=author.id,
        category=req.category,
        tags=req.tags,
        status=ArticleStatus.draft.value,
    )
    db.add(article)
    await db.flush()
    return article


async def list_articles(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    category: str | None = None,
) -> tuple[list[KBArticle], int]:
    q = select(KBArticle)
    if status:
        q = q.where(KBArticle.status == status)
    if category:
        q = q.where(KBArticle.category == category)
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()
    q = q.order_by(KBArticle.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def get_article(db: AsyncSession, article_id: int) -> KBArticle:
    result = await db.execute(select(KBArticle).where(KBArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise NotFoundError("Article not found")
    article.view_count += 1
    db.add(article)
    await db.flush()
    return article


async def get_article_by_slug(db: AsyncSession, slug: str) -> KBArticle:
    result = await db.execute(select(KBArticle).where(KBArticle.slug == slug))
    article = result.scalar_one_or_none()
    if not article:
        raise NotFoundError("Article not found")
    article.view_count += 1
    db.add(article)
    await db.flush()
    return article


async def update_article(
    db: AsyncSession, actor: User, article_id: int, req: KBArticleUpdateRequest
) -> KBArticle:
    result = await db.execute(select(KBArticle).where(KBArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise NotFoundError("Article not found")
    if article.author_id != actor.id and actor.role not in ("admin", "moderator"):
        raise ForbiddenError("Not allowed to update this article")
    if req.title is not None:
        article.title = req.title
    if req.body is not None:
        article.body = req.body
    if req.summary is not None:
        article.summary = req.summary
    if req.category is not None:
        article.category = req.category
    if req.tags is not None:
        article.tags = req.tags
    if req.status is not None:
        valid = [s.value for s in ArticleStatus]
        if req.status not in valid:
            raise ConflictError(f"Invalid status: {req.status}")
        article.status = req.status
    db.add(article)
    await db.flush()
    return article


async def publish_article(db: AsyncSession, actor: User, article_id: int) -> KBArticle:
    result = await db.execute(select(KBArticle).where(KBArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise NotFoundError("Article not found")
    if article.author_id != actor.id and actor.role not in ("admin", "moderator"):
        raise ForbiddenError("Not allowed to publish this article")
    article.status = ArticleStatus.published.value
    db.add(article)
    await db.flush()
    return article


async def delete_article(db: AsyncSession, actor: User, article_id: int) -> None:
    result = await db.execute(select(KBArticle).where(KBArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise NotFoundError("Article not found")
    if article.author_id != actor.id and actor.role not in ("admin", "moderator"):
        raise ForbiddenError("Not allowed to delete this article")
    await db.delete(article)
    await db.flush()
