from __future__ import annotations

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discussion import Discussion
from app.models.kb_article import KBArticle, ArticleStatus


async def full_text_search(
    db: AsyncSession, query: str, page: int = 1, page_size: int = 20
) -> dict:
    """Simple LIKE-based search over discussions and KB articles."""
    pattern = f"%{query}%"

    # Discussions
    disc_q = select(Discussion).where(
        or_(Discussion.title.ilike(pattern), Discussion.body.ilike(pattern))
    )
    disc_count = (await db.execute(select(func.count()).select_from(disc_q.subquery()))).scalar_one()
    disc_q = disc_q.order_by(Discussion.created_at.desc()).limit(page_size)
    discussions = list((await db.execute(disc_q)).scalars().all())

    # KB articles (published only)
    kb_q = select(KBArticle).where(
        KBArticle.status == ArticleStatus.published.value,
        or_(KBArticle.title.ilike(pattern), KBArticle.body.ilike(pattern)),
    )
    kb_count = (await db.execute(select(func.count()).select_from(kb_q.subquery()))).scalar_one()
    kb_q = kb_q.order_by(KBArticle.updated_at.desc()).limit(page_size)
    articles = list((await db.execute(kb_q)).scalars().all())

    return {
        "query": query,
        "discussions": [
            {"id": d.id, "title": d.title, "status": d.status, "created_at": d.created_at.isoformat()}
            for d in discussions
        ],
        "kb_articles": [
            {"id": a.id, "title": a.title, "slug": a.slug, "category": a.category}
            for a in articles
        ],
        "total": disc_count + kb_count,
    }
