"""KB article visibility service + router.

Routes
------
  GET /api/v1/kb/{article_id}   — AC-025.3

Visibility rules
----------------
* Any caller (authenticated or not) may fetch an **approved** article.
* Moderators and admins may fetch articles in **any** status.
* For all other combinations (unauthenticated callers, or authenticated
  callers whose role is not moderator/admin), a non-approved article
  returns **404** — identical to "not found" — to avoid leaking draft or
  pending-review existence (AC-025.3).

Design notes
------------
- The endpoint uses ``get_optional_user_payload`` so that unauthenticated
  callers are not rejected with 401; they simply receive 404 for hidden articles.
- Visibility is checked in the service layer (not only the router) so that
  any future internal callers inherit the same guard.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import TokenPayload, get_optional_user_payload
from app.models.kb_article import KBArticle, KBArticleStatus
from app.services.kb.schemas import KBArticleOut

router = APIRouter(prefix="/kb", tags=["kb-visibility"])

# ---------------------------------------------------------------------------
# Service-layer helper
# ---------------------------------------------------------------------------

_PRIVILEGED_ROLES: frozenset[str] = frozenset({"moderator", "admin"})


async def get_visible_article(
    db: AsyncSession,
    *,
    article_id: str,
    caller: Optional[TokenPayload],
) -> KBArticle:
    """Return the article if the caller is allowed to see it.

    Raises
    ------
    HTTPException 404
        Article does not exist *or* caller is not privileged and the article
        is not approved (AC-025.3 — existence must not be leaked).
    """
    stmt = select(KBArticle).where(KBArticle.id == article_id)
    article: KBArticle | None = (await db.execute(stmt)).scalar_one_or_none()

    # Privileged callers bypass the visibility filter.
    is_privileged = caller is not None and caller.role in _PRIVILEGED_ROLES

    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    if not is_privileged and article.status != KBArticleStatus.approved:
        # Return generic 404 — do not reveal that the article exists in a
        # non-approved state (AC-025.3 / OWASP A01 — broken access control).
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    return article


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------


@router.get(
    "/{article_id}",
    response_model=KBArticleOut,
    status_code=status.HTTP_200_OK,
    summary="Fetch a KB article (AC-025.3)",
)
async def get_article_endpoint(
    article_id: str,
    caller: Optional[TokenPayload] = Depends(get_optional_user_payload),
    db: AsyncSession = Depends(get_db),
) -> KBArticleOut:
    """Retrieve a KB article by ID.

    * 200 — article found and visible to the caller.
    * 404 — article does not exist, **or** the article is not yet approved
            and the caller is not a moderator/admin.

    Unauthenticated callers receive the same 404 as non-privileged authenticated
    callers when the article is not approved (AC-025.3).
    """
    article = await get_visible_article(db, article_id=article_id, caller=caller)
    return KBArticleOut.model_validate(article)
