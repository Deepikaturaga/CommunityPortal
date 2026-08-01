"""
KB article HTTP router (IF-007, COMP-005).

POST /api/v1/kb/articles
  - Requires Contributor or Admin role (AC-022.2).
  - Sanitizes HTML body before storage (AC-022.3).
  - Returns 201 Created with ArticleRead payload.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_contributor
from app.auth.models import User
from app.core.database import get_db
from app.kb.article_schemas import ArticleCreate, ArticleRead
from app.kb.articles import create_article

router = APIRouter(prefix="/kb", tags=["kb"])


@router.post(
    "/articles",
    response_model=ArticleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a KB article",
    description=(
        "Creates a new Knowledge-Base article. "
        "Requires **Contributor** or **Admin** role (AC-022.2). "
        "HTML body is sanitized server-side before storage (AC-022.3)."
    ),
)
async def create_article_endpoint(
    payload: ArticleCreate,
    current_user: User = Depends(require_contributor),  # AC-022.2
    db: AsyncSession = Depends(get_db),
) -> ArticleRead:
    article = await create_article(
        db=db,
        payload=payload,
        author_id=current_user.id,
    )
    return ArticleRead.model_validate(article)
