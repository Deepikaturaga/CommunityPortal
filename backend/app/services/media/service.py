"""Media service - pre-signed PUT/GET URL issuance, asset lifecycle.

Security invariants (AC: TASK-026):
  - Bucket NEVER has a public ACL. ACL param is intentionally absent from
    generate_presigned_url calls; access is purely via signed URLs.
  - URLs are time-limited (configurable, 60-900 s for PUT, 60-3600 s for GET).
  - Content-Type and Content-Length are bound inside the presigned conditions
    via a presigned POST policy (generate_presigned_post) so the caller cannot
    swap the content type or exceed the declared size after the URL is issued.
  - S3 key includes the authenticated user-id to prevent path traversal.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.media_asset import AssetStatus, MediaAsset
from app.services.media.schemas import (
    ALLOWED_CONTENT_TYPES,
    AvatarConfirmResponse,
    AvatarGetResponse,
    AvatarUploadRequest,
    AvatarUploadResponse,
)


def _build_s3_key(user_id: uuid.UUID, asset_id: uuid.UUID) -> str:
    """Return a deterministic, ownership-scoped S3 object key.

    Format: avatars/{user_id}/{asset_id}
    Contains no PII; scoped to the user so S3 bucket policies can
    enforce per-user prefix isolation.
    """
    return f"avatars/{user_id}/{asset_id}"


class MediaService:
    """Domain service for media asset lifecycle operations."""

    def __init__(self, db: AsyncSession, s3_client: Any) -> None:
        self._db = db
        self._s3 = s3_client

    # ── PUT (upload) ───────────────────────────────────────────────────────────

    async def issue_avatar_upload_url(
        self,
        user_id: uuid.UUID,
        request: AvatarUploadRequest,
    ) -> AvatarUploadResponse:
        """Issue a time-limited presigned POST for avatar upload.

        Uses generate_presigned_post so that content-type AND size constraints
        are embedded in the S3 policy document that AWS validates server-side.
        The client cannot bypass them after signing.

        AC compliance:
          - Private bucket: no ACL field in conditions; bucket default (private) applies.
          - No public ACL: ACL is explicitly excluded from presigned conditions.
          - Time-limited URL: ExpiresIn = settings.avatar_presign_put_expires_seconds.
          - Content-type validation: locked to the declared content_type.
          - Size validation: locked to [1, declared_size_bytes].
        """
        settings = get_settings()

        # Runtime size check (belt-and-suspenders on top of Pydantic schema validator)
        if request.size_bytes > settings.avatar_max_size_bytes:
            raise ValueError(
                f"size_bytes {request.size_bytes} exceeds maximum "
                f"{settings.avatar_max_size_bytes} bytes."
            )

        if request.content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError(f"content_type '{request.content_type}' is not permitted.")

        asset_id = uuid.uuid4()
        s3_key = _build_s3_key(user_id, asset_id)

        # Persist the pending record BEFORE calling S3 so the DB row always
        # exists when we return the presigned URL to the client.
        asset = MediaAsset(
            id=asset_id,
            owner_id=user_id,
            asset_type="avatar",
            s3_key=s3_key,
            content_type=request.content_type,
            declared_size_bytes=request.size_bytes,
            status=AssetStatus.pending,
        )
        self._db.add(asset)
        await self._db.commit()
        await self._db.refresh(asset)

        # Generate presigned POST -- conditions enforce content-type + size
        presigned = self._s3.generate_presigned_post(
            Bucket=settings.s3_avatar_bucket,
            Key=s3_key,
            Fields={"Content-Type": request.content_type},
            Conditions=[
                {"Content-Type": request.content_type},
                ["content-length-range", 1, request.size_bytes],
                # No ACL condition -> bucket default private ACL applies
            ],
            ExpiresIn=settings.avatar_presign_put_expires_seconds,
        )

        return AvatarUploadResponse(
            asset_id=asset_id,
            upload_url=presigned["url"],
            expires_in_seconds=settings.avatar_presign_put_expires_seconds,
            s3_key=s3_key,
            content_type=request.content_type,
            max_size_bytes=request.size_bytes,
        )

    # ── GET (download) ─────────────────────────────────────────────────────────

    async def issue_avatar_get_url(
        self,
        user_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> AvatarGetResponse:
        """Issue a time-limited presigned GET URL for an owned, confirmed asset.

        Enforces resource-ownership: the requesting user must own the asset.
        Only confirmed assets are accessible (pending/deleted are rejected).
        """
        settings = get_settings()
        asset = await self._get_owned_confirmed_asset(user_id, asset_id)

        presigned_url: str = self._s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.s3_avatar_bucket,
                "Key": asset.s3_key,
                "ResponseContentType": asset.content_type,
            },
            ExpiresIn=settings.avatar_presign_get_expires_seconds,
        )

        return AvatarGetResponse(
            asset_id=asset.id,
            download_url=presigned_url,
            expires_in_seconds=settings.avatar_presign_get_expires_seconds,
            content_type=asset.content_type,
        )

    # ── Confirm ────────────────────────────────────────────────────────────────

    async def confirm_avatar_upload(
        self,
        user_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> AvatarConfirmResponse:
        """Transition a pending asset to confirmed after the client PUT to S3.

        State machine: pending -> confirmed (only legal transition from pending).
        """
        asset = await self._get_owned_asset(user_id, asset_id)

        if asset.status != AssetStatus.pending:
            raise ValueError(
                f"Asset {asset_id} cannot be confirmed from status '{asset.status.value}'. "
                "Only pending assets may be confirmed."
            )

        asset.status = AssetStatus.confirmed
        asset.updated_at = datetime.now(UTC)
        await self._db.commit()
        await self._db.refresh(asset)

        return AvatarConfirmResponse(
            asset_id=asset.id,
            status="confirmed",
            message="Avatar upload confirmed successfully.",
        )

    # ── Internal helpers ───────────────────────────────────────────────────────

    async def _get_owned_asset(
        self, user_id: uuid.UUID, asset_id: uuid.UUID
    ) -> MediaAsset:
        result = await self._db.execute(
            select(MediaAsset).where(
                MediaAsset.id == asset_id,
                MediaAsset.owner_id == user_id,
            )
        )
        asset = result.scalar_one_or_none()
        if asset is None:
            raise LookupError(f"Asset {asset_id} not found for user {user_id}.")
        return asset

    async def _get_owned_confirmed_asset(
        self, user_id: uuid.UUID, asset_id: uuid.UUID
    ) -> MediaAsset:
        asset = await self._get_owned_asset(user_id, asset_id)
        if asset.status != AssetStatus.confirmed:
            raise PermissionError(
                f"Asset {asset_id} is not confirmed (status: {asset.status.value})."
            )
        return asset
