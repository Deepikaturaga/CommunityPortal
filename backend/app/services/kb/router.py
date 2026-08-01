"""KB approval / rejection HTTP router.

Routes
------
  PUT /api/v1/kb/{article_id}/approve   — AC-023.x  (moderator/admin only)
  PUT /api/v1/kb/{article_id}/reject    — AC-025.x  (moderator/admin only)

Auth: Bearer JWT, roles moderator | admin enforced by ``require_moderator``.

IF-017 event: emitted *after* the DB transaction is committed on successful
approval (AC-023.5).  Rejection does NOT emit IF-017.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import TokenPayload, require_moderator
from app.services.kb.approval import (
    KBArticleNotFoundError,
    KBInvalidTransitionError,
    approve_article,
    reject_article,
)
from app.services.kb.events import KBEventEmitter, get_kb_event_emitter
from app.services.kb.schemas import (
    ApproveRequest,
    ApproveResponse,
    RejectRequest,
    RejectResponse,
)

router = APIRouter(prefix="/kb", tags=["kb-approval"])


@router.put(
    "/{article_id}/approve",
    response_model=ApproveResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve a KB article (AC-023.x)",
)
async def approve_article_endpoint(
    article_id: str,
    body: ApproveRequest = ApproveRequest(),  # noqa: B008
    moderator: TokenPayload = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
    emitter: KBEventEmitter = Depends(get_kb_event_emitter),
) -> ApproveResponse:
    """Approve a pending-review KB article.

    * 200 — article approved, IF-017 event emitted.
    * 401 — missing/invalid JWT.
    * 403 — caller is not moderator or admin.
    * 404 — article not found.
    * 422 — article is not in ``pending_review`` status.
    """
    try:
        article_out, event_out, if017_event = await approve_article(
            db, article_id=article_id, actor_id=moderator.sub
        )
    except KBArticleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except KBInvalidTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    # Emit IF-017 after the DB transaction is committed (get_db commits on exit).
    # The router awaits the emitter here; if the emitter is async-fire-and-forget
    # in production, that wiring belongs in the concrete emitter implementation.
    await emitter.emit_article_approved(if017_event)

    return ApproveResponse(article=article_out, event=event_out)


@router.put(
    "/{article_id}/reject",
    response_model=RejectResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject a KB article (AC-025.x)",
)
async def reject_article_endpoint(
    article_id: str,
    body: RejectRequest = RejectRequest(),  # noqa: B008
    moderator: TokenPayload = Depends(require_moderator),
    db: AsyncSession = Depends(get_db),
) -> RejectResponse:
    """Reject a pending-review KB article.

    * 200 — article rejected.  No IF-017 event (rejection is approval-only).
    * 401 — missing/invalid JWT.
    * 403 — caller is not moderator or admin.
    * 404 — article not found.
    * 422 — article is not in ``pending_review`` status.
    """
    try:
        article_out, event_out = await reject_article(
            db, article_id=article_id, actor_id=moderator.sub, payload=body
        )
    except KBArticleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except KBInvalidTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return RejectResponse(article=article_out, event=event_out)
