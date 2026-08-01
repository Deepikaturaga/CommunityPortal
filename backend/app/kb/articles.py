"""
KB article service — create and read operations (COMP-005, TASK-044).

Responsibility boundary:
  * Accepts already-validated Pydantic input.
  * Sanitizes HTML body before persistence (AC-022.3).
  * Derives a unique slug.
  * Persists to STORE-005 (kb_articles table).
  * Returns ORM Article instances; callers map to response schemas.
"""
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import structlog

from app.kb.article_models import Article, ArticleStatus
from app.kb.article_schemas import ArticleCreate
from app.kb.sanitizer import sanitize_html
from app.kb.slugs import slugify

logger = structlog.get_logger(__name__)

_MAX_SLUG_ATTEMPTS = 10


async def _unique_slug(db: AsyncSession, base: str) -> str:
    """Return *base* slug, appending a counter suffix until unique."""
    candidate = base
    for attempt in range(_MAX_SLUG_ATTEMPTS):
        result = await db.execute(select(Article).where(Article.slug == candidate))
        if result.scalar_one_or_none() is None:
            return candidate
        candidate = f"{base}-{attempt + 1}"
    # Fallback: append random hex
    candidate = f"{base}-{uuid.uuid4().hex[:6]}"
    return candidate


async def create_article(
    *,
    db: AsyncSession,
    payload: ArticleCreate,
    author_id: uuid.UUID,
) -> Article:
    """
    Create a new KB article.

    - Sanitizes ``payload.body`` with bleach before storage (AC-022.3).
    - Generates a unique slug from the title.
    - Persists and returns the new Article ORM instance.
    """
    # AC-022.3: sanitize before any persistence
    sanitized_body = sanitize_html(payload.body)

    slug = await _unique_slug(db, slugify(payload.title))

    article = Article(
        title=payload.title.strip(),
        body=sanitized_body,
        slug=slug,
        status=payload.status,
        author_id=author_id,
    )
    db.add(article)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception("article_create_failed", author_id=str(author_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create article",
        )
    await db.refresh(article)
    logger.info("article_created", article_id=str(article.id), slug=article.slug)
    return article
