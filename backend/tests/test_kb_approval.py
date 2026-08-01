"""Tests for TASK-045: KB approve / reject endpoints.

Covers
------
AC-023.1  PUT /approve → 200, article.status == approved, IF-017 event emitted
AC-023.2  Approve requires moderator/admin; regular user → 403
AC-023.3  Only pending_review can be approved; draft → 422
AC-023.4  approved_by / approved_at populated on approval
AC-023.5  IF-017 event recorded by NoOpKBEventEmitter after commit

AC-023.2  (reject) PUT /reject → 200, article.status == draft, note stored
          Reject requires moderator/admin; regular user → 403
          Only pending_review can be rejected; draft → 422
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.main import app
from app.models.kb_article import KBArticle, KBArticleStatus
from app.models.user import User
from app.services.kb.events import NoOpKBEventEmitter, get_kb_event_emitter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def auth(user: User, role: str | None = None) -> dict[str, str]:
    r = role or user.role.value
    return {"Authorization": f"Bearer {create_access_token(user_id=user.id, role=r)}"}


# ---------------------------------------------------------------------------
# APPROVE — success paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approve_returns_200_and_approved_status(
    client: AsyncClient,
    moderator_user: User,
    kb_pending_article: KBArticle,
) -> None:
    """AC-023.1 / AC-023.4 — approve sets status=approved, approved_by, approved_at."""
    resp = await client.put(
        f"/api/v1/kb/{kb_pending_article.id}/approve",
        headers=auth(moderator_user),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["article"]["status"] == KBArticleStatus.approved.value
    assert data["article"]["approved_by"] == moderator_user.id
    assert data["article"]["approved_at"] is not None


@pytest.mark.asyncio
async def test_approve_emits_if017_event(
    client: AsyncClient,
    moderator_user: User,
    kb_pending_article: KBArticle,
) -> None:
    """AC-023.5 — IF-017 domain event emitted after commit."""
    noop = NoOpKBEventEmitter()
    app.dependency_overrides[get_kb_event_emitter] = lambda: noop

    try:
        resp = await client.put(
            f"/api/v1/kb/{kb_pending_article.id}/approve",
            headers=auth(moderator_user),
        )
        assert resp.status_code == 200
        assert len(noop.emitted) == 1
        evt = noop.emitted[0]
        assert evt.event_type == "kb.article.approved"
        assert evt.article_id == kb_pending_article.id
        assert evt.approved_by == moderator_user.id
    finally:
        app.dependency_overrides.pop(get_kb_event_emitter, None)


@pytest.mark.asyncio
async def test_approve_response_contains_audit_event(
    client: AsyncClient,
    moderator_user: User,
    kb_pending_article: KBArticle,
) -> None:
    """AC-023.1 — response body includes the immutable audit event."""
    resp = await client.put(
        f"/api/v1/kb/{kb_pending_article.id}/approve",
        headers=auth(moderator_user),
    )
    assert resp.status_code == 200
    evt = resp.json()["event"]
    assert evt["event_type"] == "kb.article.approved"
    assert evt["previous_status"] == KBArticleStatus.pending_review.value
    assert evt["new_status"] == KBArticleStatus.approved.value


# ---------------------------------------------------------------------------
# APPROVE — access control
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approve_requires_moderator_role(
    client: AsyncClient,
    regular_user: User,
    kb_pending_article: KBArticle,
) -> None:
    """AC-023.2 — regular user receives 403."""
    resp = await client.put(
        f"/api/v1/kb/{kb_pending_article.id}/approve",
        headers=auth(regular_user),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_approve_admin_allowed(
    client: AsyncClient,
    admin_user: User,
    kb_pending_article: KBArticle,
) -> None:
    """AC-023.2 — admin role is also permitted."""
    resp = await client.put(
        f"/api/v1/kb/{kb_pending_article.id}/approve",
        headers=auth(admin_user),
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_approve_unauthenticated_returns_401(
    client: AsyncClient,
    kb_pending_article: KBArticle,
) -> None:
    resp = await client.put(f"/api/v1/kb/{kb_pending_article.id}/approve")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# APPROVE — state machine / illegal transitions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approve_draft_returns_422(
    client: AsyncClient,
    moderator_user: User,
    kb_draft_article: KBArticle,
) -> None:
    """AC-023.3 — can only approve a pending_review article."""
    resp = await client.put(
        f"/api/v1/kb/{kb_draft_article.id}/approve",
        headers=auth(moderator_user),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_approve_already_approved_returns_422(
    client: AsyncClient,
    moderator_user: User,
    kb_approved_article: KBArticle,
) -> None:
    """State machine: approved is terminal — no further transitions."""
    resp = await client.put(
        f"/api/v1/kb/{kb_approved_article.id}/approve",
        headers=auth(moderator_user),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_approve_nonexistent_returns_404(
    client: AsyncClient,
    moderator_user: User,
) -> None:
    resp = await client.put(
        "/api/v1/kb/nonexistent-id/approve",
        headers=auth(moderator_user),
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# REJECT — success paths (AC-023.2: reject → back to draft with note)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reject_returns_200_and_draft_status(
    client: AsyncClient,
    moderator_user: User,
    kb_pending_article: KBArticle,
) -> None:
    """AC-023.2 — rejection sends article back to draft."""
    resp = await client.put(
        f"/api/v1/kb/{kb_pending_article.id}/reject",
        json={"reason": "Needs more detail."},
        headers=auth(moderator_user),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["article"]["status"] == KBArticleStatus.draft.value
    assert data["article"]["rejected_reason"] == "Needs more detail."
    assert data["article"]["rejected_by"] == moderator_user.id
    assert data["article"]["rejected_at"] is not None


@pytest.mark.asyncio
async def test_reject_audit_event_records_draft_transition(
    client: AsyncClient,
    moderator_user: User,
    kb_pending_article: KBArticle,
) -> None:
    """Audit event must reflect pending_review → draft transition."""
    resp = await client.put(
        f"/api/v1/kb/{kb_pending_article.id}/reject",
        json={"reason": "Incomplete."},
        headers=auth(moderator_user),
    )
    assert resp.status_code == 200
    evt = resp.json()["event"]
    assert evt["event_type"] == "kb.article.rejected"
    assert evt["previous_status"] == KBArticleStatus.pending_review.value
    assert evt["new_status"] == KBArticleStatus.draft.value
    assert evt["reason"] == "Incomplete."


@pytest.mark.asyncio
async def test_reject_without_reason_is_allowed(
    client: AsyncClient,
    moderator_user: User,
    kb_pending_article: KBArticle,
) -> None:
    """Rejection reason is optional per spec."""
    resp = await client.put(
        f"/api/v1/kb/{kb_pending_article.id}/reject",
        json={},
        headers=auth(moderator_user),
    )
    assert resp.status_code == 200
    assert resp.json()["article"]["status"] == KBArticleStatus.draft.value


# ---------------------------------------------------------------------------
# REJECT — access control
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reject_requires_moderator_role(
    client: AsyncClient,
    regular_user: User,
    kb_pending_article: KBArticle,
) -> None:
    resp = await client.put(
        f"/api/v1/kb/{kb_pending_article.id}/reject",
        json={"reason": "Nope."},
        headers=auth(regular_user),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# REJECT — state machine / illegal transitions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reject_draft_returns_422(
    client: AsyncClient,
    moderator_user: User,
    kb_draft_article: KBArticle,
) -> None:
    """Only pending_review can be rejected."""
    resp = await client.put(
        f"/api/v1/kb/{kb_draft_article.id}/reject",
        json={"reason": "Bad."},
        headers=auth(moderator_user),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_reject_approved_returns_422(
    client: AsyncClient,
    moderator_user: User,
    kb_approved_article: KBArticle,
) -> None:
    """Approved is a terminal state — cannot be rejected."""
    resp = await client.put(
        f"/api/v1/kb/{kb_approved_article.id}/reject",
        json={"reason": "Too late."},
        headers=auth(moderator_user),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_reject_nonexistent_returns_404(
    client: AsyncClient,
    moderator_user: User,
) -> None:
    resp = await client.put(
        "/api/v1/kb/nonexistent-id/reject",
        json={"reason": "?"},
        headers=auth(moderator_user),
    )
    assert resp.status_code == 404
