"""
HTTP integration tests for the notification preference and list endpoints.
Uses HTTPX ASGITransport + app dependency overrides (no real DB).

Covers (VER-004 / AC-029.x):
  - GET /preferences  → 200 with items list
  - GET /preferences/{channel}/{category} → 200, synthetic default when absent
  - PUT /preferences/{channel}/{category} → 200, opted_out persisted
  - GET /notifications/ → 200, paginated
  - Self-only: JWT user_id cannot be overridden by caller
  - Unauthenticated → 401
  - Wrong/expired token → 401
"""
from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from jose import jwt as jose_jwt

from app.core.config import settings
from app.main import app
from app.services.notifications.dependencies import get_preference_repo
from app.services.notifications.enums import (
    NotificationCategory,
    NotificationChannel,
    NotificationStatus,
)
from app.services.notifications.models import Notification, NotificationPreference
from app.services.notifications.repository import NotificationPreferenceRepository
from tests.conftest import auth_headers, make_token

USER_A = "user-aaa"
USER_B = "user-bbb"

_NOW = datetime.now(UTC)


def _pref(
    user_id: str = USER_A,
    channel: NotificationChannel = NotificationChannel.EMAIL,
    category: NotificationCategory = NotificationCategory.MARKETING,
    opted_out: bool = False,
) -> NotificationPreference:
    p = NotificationPreference(
        user_id=user_id,
        channel=channel,
        category=category,
        opted_out=opted_out,
    )
    p.id = uuid.uuid4()
    p.created_at = _NOW
    p.updated_at = _NOW
    return p


def _notif(user_id: str = USER_A) -> Notification:
    n = Notification(
        user_id=user_id,
        channel=NotificationChannel.EMAIL,
        category=NotificationCategory.TRANSACTIONAL,
        status=NotificationStatus.SENT,
        body="Hello",
    )
    n.id = uuid.uuid4()
    n.created_at = _NOW
    n.preference_id = None
    n.subject = None
    n.sent_at = None
    n.read_at = None
    return n


def _make_repo_stub(
    prefs: list[NotificationPreference] | None = None,
    single_pref: NotificationPreference | None = None,
    upserted_pref: NotificationPreference | None = None,
    notifs: list[Notification] | None = None,
    notif_total: int = 0,
) -> NotificationPreferenceRepository:
    repo = AsyncMock(spec=NotificationPreferenceRepository)
    repo.list_preferences = AsyncMock(return_value=prefs or [])
    repo.get_preference = AsyncMock(return_value=single_pref)
    repo.upsert_preference = AsyncMock(return_value=upserted_pref or _pref())
    repo.list_notifications = AsyncMock(return_value=(notifs or [], notif_total))
    return repo  # type: ignore[return-value]


class TestPreferenceListEndpoint:
    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.get("/api/v1/notifications/preferences")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_prefs(
        self, async_client: AsyncClient
    ) -> None:
        repo = _make_repo_stub(prefs=[])
        app.dependency_overrides[get_preference_repo] = lambda: repo
        try:
            resp = await async_client.get(
                "/api/v1/notifications/preferences",
                headers=auth_headers(USER_A),
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["items"] == []
            assert data["total"] == 0
        finally:
            app.dependency_overrides.pop(get_preference_repo, None)

    @pytest.mark.asyncio
    async def test_returns_user_preferences(
        self, async_client: AsyncClient
    ) -> None:
        pref = _pref(USER_A, opted_out=True)
        repo = _make_repo_stub(prefs=[pref])
        app.dependency_overrides[get_preference_repo] = lambda: repo
        try:
            resp = await async_client.get(
                "/api/v1/notifications/preferences",
                headers=auth_headers(USER_A),
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert data["items"][0]["opted_out"] is True
            repo.list_preferences.assert_awaited_once_with(USER_A)
        finally:
            app.dependency_overrides.pop(get_preference_repo, None)


class TestPreferenceGetEndpoint:
    @pytest.mark.asyncio
    async def test_returns_default_when_row_absent(
        self, async_client: AsyncClient
    ) -> None:
        repo = _make_repo_stub(single_pref=None)
        app.dependency_overrides[get_preference_repo] = lambda: repo
        try:
            resp = await async_client.get(
                "/api/v1/notifications/preferences/email/marketing",
                headers=auth_headers(USER_A),
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["opted_out"] is False
            assert data["channel"] == "email"
            assert data["category"] == "marketing"
        finally:
            app.dependency_overrides.pop(get_preference_repo, None)

    @pytest.mark.asyncio
    async def test_returns_existing_preference(
        self, async_client: AsyncClient
    ) -> None:
        pref = _pref(USER_A, opted_out=True)
        repo = _make_repo_stub(single_pref=pref)
        app.dependency_overrides[get_preference_repo] = lambda: repo
        try:
            resp = await async_client.get(
                "/api/v1/notifications/preferences/email/marketing",
                headers=auth_headers(USER_A),
            )
            assert resp.status_code == 200
            assert resp.json()["opted_out"] is True
        finally:
            app.dependency_overrides.pop(get_preference_repo, None)

    @pytest.mark.asyncio
    async def test_invalid_channel_returns_422(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.get(
            "/api/v1/notifications/preferences/fax/marketing",
            headers=auth_headers(USER_A),
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_category_returns_422(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.get(
            "/api/v1/notifications/preferences/email/unknown_cat",
            headers=auth_headers(USER_A),
        )
        assert resp.status_code == 422


class TestPreferencePutEndpoint:
    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.put(
            "/api/v1/notifications/preferences/email/marketing",
            json={"opted_out": True},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_opt_out_persisted(self, async_client: AsyncClient) -> None:
        upserted = _pref(USER_A, opted_out=True)
        repo = _make_repo_stub(upserted_pref=upserted)
        app.dependency_overrides[get_preference_repo] = lambda: repo
        try:
            resp = await async_client.put(
                "/api/v1/notifications/preferences/email/marketing",
                json={"opted_out": True},
                headers=auth_headers(USER_A),
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["opted_out"] is True
            repo.upsert_preference.assert_awaited_once_with(
                user_id=USER_A,
                channel=NotificationChannel.EMAIL,
                category=NotificationCategory.MARKETING,
                opted_out=True,
            )
        finally:
            app.dependency_overrides.pop(get_preference_repo, None)

    @pytest.mark.asyncio
    async def test_opt_in_persisted(self, async_client: AsyncClient) -> None:
        upserted = _pref(USER_A, opted_out=False)
        repo = _make_repo_stub(upserted_pref=upserted)
        app.dependency_overrides[get_preference_repo] = lambda: repo
        try:
            resp = await async_client.put(
                "/api/v1/notifications/preferences/email/marketing",
                json={"opted_out": False},
                headers=auth_headers(USER_A),
            )
            assert resp.status_code == 200
            assert resp.json()["opted_out"] is False
        finally:
            app.dependency_overrides.pop(get_preference_repo, None)

    @pytest.mark.asyncio
    async def test_missing_body_returns_422(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.put(
            "/api/v1/notifications/preferences/email/marketing",
            headers=auth_headers(USER_A),
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_idempotent_put_same_value(
        self, async_client: AsyncClient
    ) -> None:
        """PUT with the same opted_out twice returns 200 both times."""
        upserted = _pref(USER_A, opted_out=True)
        repo = _make_repo_stub(upserted_pref=upserted)
        app.dependency_overrides[get_preference_repo] = lambda: repo
        try:
            for _ in range(2):
                resp = await async_client.put(
                    "/api/v1/notifications/preferences/email/marketing",
                    json={"opted_out": True},
                    headers=auth_headers(USER_A),
                )
                assert resp.status_code == 200
        finally:
            app.dependency_overrides.pop(get_preference_repo, None)


class TestSelfOnlyAccess:
    """
    Verify that user_id in JWT cannot be overridden by the caller.
    AC-029.x: a token for USER_B cannot read/write USER_A's preferences.
    """

    @pytest.mark.asyncio
    async def test_put_uses_jwt_user_not_body_user(
        self, async_client: AsyncClient
    ) -> None:
        upserted = _pref(USER_B, opted_out=True)
        repo = _make_repo_stub(upserted_pref=upserted)
        app.dependency_overrides[get_preference_repo] = lambda: repo
        try:
            resp = await async_client.put(
                "/api/v1/notifications/preferences/email/marketing",
                json={"opted_out": True},
                headers=auth_headers(USER_B),
            )
            assert resp.status_code == 200
            args = repo.upsert_preference.call_args
            assert args.kwargs["user_id"] == USER_B
        finally:
            app.dependency_overrides.pop(get_preference_repo, None)

    @pytest.mark.asyncio
    async def test_expired_token_returns_401(
        self, async_client: AsyncClient
    ) -> None:
        expired_token = jose_jwt.encode(
            {"sub": USER_A, "exp": int(time.time()) - 10},
            settings.secret_key,
            algorithm=settings.algorithm,
        )
        resp = await async_client.get(
            "/api/v1/notifications/preferences",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_tampered_token_returns_401(
        self, async_client: AsyncClient
    ) -> None:
        token = make_token(USER_A, secret="wrong-secret-that-is-long-enough-32+")
        resp = await async_client.get(
            "/api/v1/notifications/preferences",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401


class TestNotificationListEndpoint:
    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.get("/api/v1/notifications/")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_paginated_notifications(
        self, async_client: AsyncClient
    ) -> None:
        notifs = [_notif(USER_A) for _ in range(3)]
        repo = _make_repo_stub(notifs=notifs, notif_total=3)
        app.dependency_overrides[get_preference_repo] = lambda: repo
        try:
            resp = await async_client.get(
                "/api/v1/notifications/?page=1&page_size=10",
                headers=auth_headers(USER_A),
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 3
            assert data["page"] == 1
            assert data["page_size"] == 10
            assert len(data["items"]) == 3
        finally:
            app.dependency_overrides.pop(get_preference_repo, None)

    @pytest.mark.asyncio
    async def test_page_size_bounded_at_100(
        self, async_client: AsyncClient
    ) -> None:
        """page_size > 100 must be rejected."""
        resp = await async_client.get(
            "/api/v1/notifications/?page_size=200",
            headers=auth_headers(USER_A),
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_filter_by_channel(self, async_client: AsyncClient) -> None:
        repo = _make_repo_stub(notifs=[], notif_total=0)
        app.dependency_overrides[get_preference_repo] = lambda: repo
        try:
            resp = await async_client.get(
                "/api/v1/notifications/?channel=email",
                headers=auth_headers(USER_A),
            )
            assert resp.status_code == 200
            params_used = repo.list_notifications.call_args.args[1]
            assert params_used.channel == NotificationChannel.EMAIL
        finally:
            app.dependency_overrides.pop(get_preference_repo, None)

    @pytest.mark.asyncio
    async def test_invalid_status_filter_returns_422(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.get(
            "/api/v1/notifications/?status=flying",
            headers=auth_headers(USER_A),
        )
        assert resp.status_code == 422
