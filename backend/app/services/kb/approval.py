"""KB approval / rejection service layer.

Business rules
--------------
* ``approve_article``  — AC-023.x
    - Fetches the KBArticle by ``article_id``.
    - Validates that the current status allows the ``approved`` transition
      (only ``pending_review → approved`` is permitted).
    - Persists the status change, sets ``approved_by`` / ``approved_at``.
    - Appends an immutable ``KBApprovalEvent`` (event_type = ``kb.article.approved``).
    - Returns ``(KBArticleOut, KBApprovalEventOut, IF017ArticleApprovedEvent)``.
    - Caller is responsible for flushing/committing and emitting the IF-017 event.

* ``reject_article``  — AC-023.2
    - Validates ``pending_review → draft`` transition.
    - Rejection sends the article back to ``draft`` with a moderator note (AC-023.2).
    - Sets ``rejected_by`` / ``rejected_at`` / ``rejected_reason`` (moderator note).
    - Appends a ``KBApprovalEvent`` (event_type = ``kb.article.rejected``) for audit.
    - Returns ``(KBArticleOut, KBApprovalEventOut)``.  No IF-017 event on rejection.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kb_article import (
    KB_ARTICLE_TRANSITIONS,
    KBApprovalEvent,
    KBArticle,
    KBArticleStatus,
)
from app.services.kb.schemas import (
    IF017ArticleApprovedEvent,
    KBApprovalEventOut,
    KBArticleOut,
    RejectRequest,
)

# ---------------------------------------------------------------------------
# Domain errors
# ---------------------------------------------------------------------------


class KBArticleNotFoundError(Exception):
    """Raised when the requested article does not exist."""


class KBInvalidTransitionError(Exception):
    """Raised when the requested status transition is not permitted."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_EVENT_APPROVED = "kb.article.approved"
_EVENT_REJECTED = "kb.article.rejected"


async def _get_article_or_raise(db: AsyncSession, article_id: str) -> KBArticle:
    stmt = select(KBArticle).where(KBArticle.id == article_id)
    article: KBArticle | None = (await db.execute(stmt)).scalar_one_or_none()
    if article is None:
        raise KBArticleNotFoundError(f"KB article {article_id!r} not found")
    return article


def _assert_transition(
    article: KBArticle,
    target: KBArticleStatus,
) -> None:
    allowed = KB_ARTICLE_TRANSITIONS.get(article.status, set())
    if target not in allowed:
        raise KBInvalidTransitionError(
            f"Cannot transition KB article from {article.status!r} to {target!r}"
        )


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


async def approve_article(
    db: AsyncSession,
    *,
    article_id: str,
    actor_id: str,
) -> tuple[KBArticleOut, KBApprovalEventOut, IF017ArticleApprovedEvent]:
    """Approve a pending-review KB article (AC-023.x).

    Mutates the article in-place, writes the audit event, and returns all
    three artefacts.  Does *not* commit — the caller (router) owns the
    transaction boundary via ``get_db``.

    The returned ``IF017ArticleApprovedEvent`` must be emitted by the caller
    *after* the DB commit to guarantee at-least-once delivery semantics.
    """
    now = datetime.now(timezone.utc)
    article = await _get_article_or_raise(db, article_id)
    previous_status = article.status

    _assert_transition(article, KBArticleStatus.approved)

    # Mutate article
    article.status = KBArticleStatus.approved
    article.approved_by = actor_id
    article.approved_at = now
    article.updated_at = now
    db.add(article)

    # Append-only audit event
    audit_evt = KBApprovalEvent(
        article_id=article_id,
        actor_id=actor_id,
        event_type=_EVENT_APPROVED,
        previous_status=previous_status.value,
        new_status=KBArticleStatus.approved.value,
        reason=None,
        occurred_at=now,
    )
    db.add(audit_evt)

    await db.flush()  # Populate generated IDs before building response objects

    article_out = KBArticleOut.model_validate(article)
    event_out = KBApprovalEventOut.model_validate(audit_evt)

    # IF-017 domain event (AC-023.5) — emitted by router after commit
    if017_event = IF017ArticleApprovedEvent(
        article_id=article_id,
        approved_by=actor_id,
        approved_at=now,
        title=article.title,
        author_id=article.author_id,
        audit_event_id=audit_evt.id,
    )

    return article_out, event_out, if017_event


async def reject_article(
    db: AsyncSession,
    *,
    article_id: str,
    actor_id: str,
    payload: RejectRequest,
) -> tuple[KBArticleOut, KBApprovalEventOut]:
    """Reject a pending-review KB article, returning it to draft (AC-023.2).

    Rejection transitions ``pending_review → draft`` and stores the moderator
    note in ``rejected_reason``.  No IF-017 event is emitted for rejection.
    """
    now = datetime.now(timezone.utc)
    article = await _get_article_or_raise(db, article_id)
    previous_status = article.status

    # Rejection returns the article to draft (AC-023.2 — "reject → back to draft with note").
    _assert_transition(article, KBArticleStatus.draft)

    # Mutate article — status goes back to draft; note recorded for author
    article.status = KBArticleStatus.draft
    article.rejected_by = actor_id
    article.rejected_at = now
    article.rejected_reason = payload.reason
    article.updated_at = now
    db.add(article)

    # Append-only audit event
    audit_evt = KBApprovalEvent(
        article_id=article_id,
        actor_id=actor_id,
        event_type=_EVENT_REJECTED,
        previous_status=previous_status.value,
        new_status=KBArticleStatus.draft.value,
        reason=payload.reason,
        occurred_at=now,
    )
    db.add(audit_evt)

    await db.flush()

    article_out = KBArticleOut.model_validate(article)
    event_out = KBApprovalEventOut.model_validate(audit_evt)

    return article_out, event_out
