"""
Unit tests for NotificationPreferenceRepository (no real DB – patched session).
Covers: list, get, upsert (create path and update path).
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.notifications.enums import NotificationCategory, NotificationChannel
from app.services.notifications.models import NotificationPreference
from app.services.notifications.repository import NotificationPreferenceRepository


def _make_pref(
    user_id: str = "user-1",
    channel: NotificationChannel = NotificationChannel.EMAIL,
    category: NotificationCategory = NotificationCategory.MARKETING,
    opted_out: bool = False,
) -> NotificationPreference:
    pref = NotificationPreference(
        user_id=user_id,
        channel=channel,
        category=category,
        opted_out=opted_out,
    )
    pref.id = uuid.uuid4()
    pref.created_at = datetime.now(UTC)
    pref.updated_at = datetime.now(UTC)
    return pref


class TestListPreferences:
    @pytest.mark.asyncio
    async def test_returns_only_current_user_preferences(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [_make_pref("u1"), _make_pref("u1")]
        db.execute = AsyncMock(return_value=mock_result)

        repo = NotificationPreferenceRepository(db)
        result = await repo.list_preferences("u1")
        assert len(result) == 2
        assert all(p.user_id == "u1" for p in result)


class TestGetPreference:
    @pytest.mark.asyncio
    async def test_returns_none_when_absent(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        repo = NotificationPreferenceRepository(db)
        result = await repo.get_preference(
            "u1",
            NotificationChannel.EMAIL,
            NotificationCategory.MARKETING,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_existing_preference(self) -> None:
        pref = _make_pref("u1")
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = pref
        db.execute = AsyncMock(return_value=mock_result)

        repo = NotificationPreferenceRepository(db)
        result = await repo.get_preference(
            "u1",
            NotificationChannel.EMAIL,
            NotificationCategory.MARKETING,
        )
        assert result is pref


class TestUpsertPreference:
    @pytest.mark.asyncio
    async def test_creates_new_row_when_absent(self) -> None:
        db = AsyncMock()
        # get_preference returns None → create path
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_get_result)
        db.add = MagicMock()
        db.flush = AsyncMock()

        created_pref = _make_pref("u1", opted_out=True)

        def _side_effect(obj: NotificationPreference) -> None:
            obj.id = created_pref.id
            obj.created_at = created_pref.created_at
            obj.updated_at = created_pref.updated_at

        db.refresh = AsyncMock(side_effect=_side_effect)

        repo = NotificationPreferenceRepository(db)
        result = await repo.upsert_preference(
            "u1",
            NotificationChannel.EMAIL,
            NotificationCategory.MARKETING,
            opted_out=True,
        )

        db.add.assert_called_once()
        db.flush.assert_awaited()
        assert result.opted_out is True

    @pytest.mark.asyncio
    async def test_updates_existing_row_when_value_changes(self) -> None:
        existing = _make_pref("u1", opted_out=False)
        db = AsyncMock()
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = existing

        mock_update_result = MagicMock()
        db.execute = AsyncMock(side_effect=[mock_get_result, mock_update_result])
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        repo = NotificationPreferenceRepository(db)
        await repo.upsert_preference(
            "u1",
            NotificationChannel.EMAIL,
            NotificationCategory.MARKETING,
            opted_out=True,
        )

        # execute called twice: select + update
        assert db.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_no_update_when_value_unchanged(self) -> None:
        existing = _make_pref("u1", opted_out=True)
        db = AsyncMock()
        mock_get_result = MagicMock()
        mock_get_result.scalar_one_or_none.return_value = existing
        db.execute = AsyncMock(return_value=mock_get_result)

        repo = NotificationPreferenceRepository(db)
        result = await repo.upsert_preference(
            "u1",
            NotificationChannel.EMAIL,
            NotificationCategory.MARKETING,
            opted_out=True,
        )

        # Only the SELECT was executed; no UPDATE
        db.execute.assert_awaited_once()
        assert result is existing
