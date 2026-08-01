"""Unit tests for MediaService -- no HTTP layer, direct service calls.

VER-021 coverage:
  - Presigned POST issued with correct bucket / key / content-type conditions
  - Private bucket: no ACL field in presigned conditions
  - Time-limited URL: ExpiresIn matches settings
  - Content-type validation rejects disallowed types
  - Size validation rejects oversized declarations
  - GET URL only issued for confirmed, owned assets
  - Cross-user access denied (ownership predicate)
  - State machine: only pending->confirmed is legal
  - State machine: confirmed->confirmed is rejected
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.media_asset import AssetStatus, MediaAsset
from app.models.user import User
from app.services.media.schemas import AvatarUploadRequest
from app.services.media.service import MediaService, _build_s3_key


# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_s3_mock() -> MagicMock:
    m = MagicMock()
    m.generate_presigned_post.return_value = {
        "url": "https://bucket.s3.amazonaws.com/",
        "fields": {"key": "k", "Content-Type": "image/jpeg"},
    }
    m.generate_presigned_url.return_value = "https://bucket.s3.amazonaws.com/key?sig=x"
    return m


async def _create_user(db: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@example.com",
        hashed_password=hash_password("pw"),
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _create_asset(
    db: AsyncSession,
    owner_id: uuid.UUID,
    status: AssetStatus = AssetStatus.pending,
) -> MediaAsset:
    asset_id = uuid.uuid4()
    asset = MediaAsset(
        id=asset_id,
        owner_id=owner_id,
        asset_type="avatar",
        s3_key=_build_s3_key(owner_id, asset_id),
        content_type="image/jpeg",
        declared_size_bytes=100_000,
        status=status,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


# ── Tests: issue_avatar_upload_url ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_issue_upload_url_success(db_session: AsyncSession) -> None:
    s3 = _make_s3_mock()
    user = await _create_user(db_session)
    svc = MediaService(db=db_session, s3_client=s3)
    req = AvatarUploadRequest(content_type="image/jpeg", size_bytes=500_000)

    resp = await svc.issue_avatar_upload_url(user.id, req)

    assert resp.upload_url == "https://bucket.s3.amazonaws.com/"
    assert resp.content_type == "image/jpeg"
    assert resp.expires_in_seconds == 300
    assert resp.max_size_bytes == 500_000


@pytest.mark.asyncio
async def test_issue_upload_url_presigned_post_called_with_correct_params(
    db_session: AsyncSession,
) -> None:
    s3 = _make_s3_mock()
    user = await _create_user(db_session)
    svc = MediaService(db=db_session, s3_client=s3)
    req = AvatarUploadRequest(content_type="image/png", size_bytes=1_000_000)

    await svc.issue_avatar_upload_url(user.id, req)

    s3.generate_presigned_post.assert_called_once()
    call_kwargs = s3.generate_presigned_post.call_args[1]

    assert call_kwargs["Bucket"] == "test-avatar-bucket"
    assert call_kwargs["Fields"]["Content-Type"] == "image/png"
    assert call_kwargs["ExpiresIn"] == 300

    # AC: no ACL in conditions -> bucket default (private) applies
    conditions = call_kwargs["Conditions"]
    for cond in conditions:
        if isinstance(cond, dict):
            assert "acl" not in {k.lower() for k in cond}, (
                "ACL must not be present in presigned conditions (bucket must stay private)"
            )


@pytest.mark.asyncio
async def test_issue_upload_url_persists_pending_asset(db_session: AsyncSession) -> None:
    s3 = _make_s3_mock()
    user = await _create_user(db_session)
    svc = MediaService(db=db_session, s3_client=s3)
    req = AvatarUploadRequest(content_type="image/webp", size_bytes=200_000)

    resp = await svc.issue_avatar_upload_url(user.id, req)

    result = await db_session.execute(
        select(MediaAsset).where(MediaAsset.id == resp.asset_id)
    )
    asset = result.scalar_one()
    assert asset.status == AssetStatus.pending
    assert asset.owner_id == user.id
    assert asset.content_type == "image/webp"


@pytest.mark.asyncio
async def test_issue_upload_url_rejects_disallowed_content_type(
    db_session: AsyncSession,
) -> None:
    with pytest.raises(ValidationError, match="not permitted"):
        AvatarUploadRequest(content_type="application/pdf", size_bytes=1000)


@pytest.mark.asyncio
async def test_issue_upload_url_rejects_oversized_file(db_session: AsyncSession) -> None:
    with pytest.raises(ValidationError):
        AvatarUploadRequest(content_type="image/jpeg", size_bytes=6_000_000)


@pytest.mark.asyncio
async def test_issue_upload_url_s3_key_scoped_to_user(db_session: AsyncSession) -> None:
    s3 = _make_s3_mock()
    user = await _create_user(db_session)
    svc = MediaService(db=db_session, s3_client=s3)
    req = AvatarUploadRequest(content_type="image/jpeg", size_bytes=100_000)

    resp = await svc.issue_avatar_upload_url(user.id, req)

    assert resp.s3_key.startswith(f"avatars/{user.id}/"), (
        "S3 key must be scoped to the owning user"
    )


# ── Tests: issue_avatar_get_url ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_issue_get_url_success(db_session: AsyncSession) -> None:
    s3 = _make_s3_mock()
    user = await _create_user(db_session)
    asset = await _create_asset(db_session, user.id, status=AssetStatus.confirmed)
    svc = MediaService(db=db_session, s3_client=s3)

    resp = await svc.issue_avatar_get_url(user.id, asset.id)

    assert "https://" in resp.download_url
    assert resp.expires_in_seconds == 900
    s3.generate_presigned_url.assert_called_once()
    call_kwargs = s3.generate_presigned_url.call_args[1]
    assert call_kwargs["Params"]["Bucket"] == "test-avatar-bucket"
    assert call_kwargs["Params"]["Key"] == asset.s3_key


@pytest.mark.asyncio
async def test_get_url_rejects_pending_asset(db_session: AsyncSession) -> None:
    s3 = _make_s3_mock()
    user = await _create_user(db_session)
    asset = await _create_asset(db_session, user.id, status=AssetStatus.pending)
    svc = MediaService(db=db_session, s3_client=s3)

    with pytest.raises(PermissionError, match="not confirmed"):
        await svc.issue_avatar_get_url(user.id, asset.id)


@pytest.mark.asyncio
async def test_get_url_denied_for_wrong_user(db_session: AsyncSession) -> None:
    """Cross-user access must be denied (ownership predicate)."""
    s3 = _make_s3_mock()
    owner = await _create_user(db_session)
    attacker = await _create_user(db_session)
    asset = await _create_asset(db_session, owner.id, status=AssetStatus.confirmed)
    svc = MediaService(db=db_session, s3_client=s3)

    with pytest.raises(LookupError):
        await svc.issue_avatar_get_url(attacker.id, asset.id)


# ── Tests: confirm_avatar_upload ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_confirm_transitions_pending_to_confirmed(db_session: AsyncSession) -> None:
    s3 = _make_s3_mock()
    user = await _create_user(db_session)
    asset = await _create_asset(db_session, user.id, status=AssetStatus.pending)
    svc = MediaService(db=db_session, s3_client=s3)

    resp = await svc.confirm_avatar_upload(user.id, asset.id)

    assert resp.status == "confirmed"

    result = await db_session.execute(select(MediaAsset).where(MediaAsset.id == asset.id))
    refreshed = result.scalar_one()
    assert refreshed.status == AssetStatus.confirmed


@pytest.mark.asyncio
async def test_confirm_already_confirmed_is_rejected(db_session: AsyncSession) -> None:
    """State machine: confirmed -> confirmed is an illegal transition."""
    s3 = _make_s3_mock()
    user = await _create_user(db_session)
    asset = await _create_asset(db_session, user.id, status=AssetStatus.confirmed)
    svc = MediaService(db=db_session, s3_client=s3)

    with pytest.raises(ValueError, match="cannot be confirmed from status"):
        await svc.confirm_avatar_upload(user.id, asset.id)


@pytest.mark.asyncio
async def test_confirm_denied_for_wrong_user(db_session: AsyncSession) -> None:
    """Confirm must be rejected when user does not own the asset."""
    s3 = _make_s3_mock()
    owner = await _create_user(db_session)
    attacker = await _create_user(db_session)
    asset = await _create_asset(db_session, owner.id, status=AssetStatus.pending)
    svc = MediaService(db=db_session, s3_client=s3)

    with pytest.raises(LookupError):
        await svc.confirm_avatar_upload(attacker.id, asset.id)
