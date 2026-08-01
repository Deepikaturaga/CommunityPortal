"""Integration tests for the media router -- HTTP layer via HTTPX ASGITransport.

VER-021 coverage (HTTP endpoints):
  - POST /upload-url -> 201, presigned URL returned
  - POST /upload-url -> 401/403 without token
  - POST /upload-url -> 422 for bad content-type
  - POST /upload-url -> 422 for oversized size_bytes
  - POST /{asset_id}/confirm -> 200 pending -> confirmed
  - POST /{asset_id}/confirm -> 404 unknown asset
  - POST /{asset_id}/confirm -> 409 already confirmed
  - GET  /{asset_id}/download-url -> 200 for confirmed asset
  - GET  /{asset_id}/download-url -> 403 for pending asset
  - GET  /{asset_id}/download-url -> 404 unknown asset
  - Cross-user: another user cannot GET our download URL
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app as _app
from app.models.media_asset import AssetStatus, MediaAsset
from app.models.user import User
from app.services.media.s3_client import get_s3_client
from app.services.media.service import _build_s3_key


# ── Helpers ────────────────────────────────────────────────────────────────────


async def _make_confirmed_asset(
    db: AsyncSession, user: User, content_type: str = "image/jpeg"
) -> MediaAsset:
    asset_id = uuid.uuid4()
    asset = MediaAsset(
        id=asset_id,
        owner_id=user.id,
        asset_type="avatar",
        s3_key=_build_s3_key(user.id, asset_id),
        content_type=content_type,
        declared_size_bytes=200_000,
        status=AssetStatus.confirmed,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


async def _make_pending_asset(db: AsyncSession, user: User) -> MediaAsset:
    asset_id = uuid.uuid4()
    asset = MediaAsset(
        id=asset_id,
        owner_id=user.id,
        asset_type="avatar",
        s3_key=_build_s3_key(user.id, asset_id),
        content_type="image/jpeg",
        declared_size_bytes=100_000,
        status=AssetStatus.pending,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


# ── Upload URL tests ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upload_url_returns_201(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/media/avatars/upload-url",
        json={"content_type": "image/jpeg", "size_bytes": 500_000},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "upload_url" in body
    assert "asset_id" in body
    assert body["expires_in_seconds"] == 300
    assert body["content_type"] == "image/jpeg"


@pytest.mark.asyncio
async def test_upload_url_requires_auth(
    db_session: AsyncSession,
    mock_s3: MagicMock,
) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_app),
        base_url="http://testserver",
    ) as ac:
        resp = await ac.post(
            "/api/v1/media/avatars/upload-url",
            json={"content_type": "image/jpeg", "size_bytes": 100_000},
        )
    assert resp.status_code in {401, 403}


@pytest.mark.asyncio
async def test_upload_url_rejects_invalid_content_type(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/media/avatars/upload-url",
        json={"content_type": "application/pdf", "size_bytes": 500_000},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_upload_url_rejects_oversized_file(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/media/avatars/upload-url",
        json={"content_type": "image/jpeg", "size_bytes": 99_999_999},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_upload_url_response_has_no_public_acl(
    client: AsyncClient, mock_s3: MagicMock
) -> None:
    """Ensure no ACL-related field is propagated back to the client."""
    await client.post(
        "/api/v1/media/avatars/upload-url",
        json={"content_type": "image/jpeg", "size_bytes": 500_000},
    )
    call_kwargs = mock_s3.generate_presigned_post.call_args[1]
    conditions = call_kwargs.get("Conditions", [])
    for cond in conditions:
        if isinstance(cond, dict):
            assert "acl" not in {k.lower() for k in cond}


# ── Confirm tests ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_confirm_pending_asset_returns_200(
    client: AsyncClient, db_session: AsyncSession, test_user: User
) -> None:
    asset = await _make_pending_asset(db_session, test_user)
    resp = await client.post(f"/api/v1/media/avatars/{asset.id}/confirm")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "confirmed"
    assert uuid.UUID(body["asset_id"]) == asset.id


@pytest.mark.asyncio
async def test_confirm_unknown_asset_returns_404(client: AsyncClient) -> None:
    resp = await client.post(f"/api/v1/media/avatars/{uuid.uuid4()}/confirm")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_confirm_already_confirmed_returns_409(
    client: AsyncClient, db_session: AsyncSession, test_user: User
) -> None:
    asset = await _make_confirmed_asset(db_session, test_user)
    resp = await client.post(f"/api/v1/media/avatars/{asset.id}/confirm")
    assert resp.status_code == 409


# ── Download URL tests ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_download_url_confirmed_asset_returns_200(
    client: AsyncClient, db_session: AsyncSession, test_user: User
) -> None:
    asset = await _make_confirmed_asset(db_session, test_user)
    resp = await client.get(f"/api/v1/media/avatars/{asset.id}/download-url")
    assert resp.status_code == 200
    body = resp.json()
    assert "download_url" in body
    assert body["expires_in_seconds"] == 900


@pytest.mark.asyncio
async def test_download_url_pending_asset_returns_403(
    client: AsyncClient, db_session: AsyncSession, test_user: User
) -> None:
    asset = await _make_pending_asset(db_session, test_user)
    resp = await client.get(f"/api/v1/media/avatars/{asset.id}/download-url")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_download_url_unknown_asset_returns_404(client: AsyncClient) -> None:
    resp = await client.get(f"/api/v1/media/avatars/{uuid.uuid4()}/download-url")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_download_url_cross_user_denied(
    db_session: AsyncSession,
    mock_s3: MagicMock,
) -> None:
    """Another authenticated user must not access a different user's asset."""
    owner = User(
        id=uuid.uuid4(),
        email="owner@example.com",
        hashed_password=hash_password("pw"),
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    attacker = User(
        id=uuid.uuid4(),
        email="attacker@example.com",
        hashed_password=hash_password("pw"),
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db_session.add_all([owner, attacker])
    await db_session.commit()

    asset = await _make_confirmed_asset(db_session, owner)

    async def _db_override() -> Any:
        yield db_session

    def _s3_override() -> Any:
        yield mock_s3

    _app.dependency_overrides[get_db] = _db_override
    _app.dependency_overrides[get_s3_client] = _s3_override

    attacker_token = create_access_token(str(attacker.id))
    async with AsyncClient(
        transport=ASGITransport(app=_app),
        base_url="http://testserver",
        headers={"Authorization": f"Bearer {attacker_token}"},
    ) as ac:
        resp = await ac.get(f"/api/v1/media/avatars/{asset.id}/download-url")

    _app.dependency_overrides.clear()
    assert resp.status_code == 404, "Cross-user asset access must return 404"
