"""Media / avatar router - pre-signed URL endpoints (IF-013).

Routes:
  POST /api/v1/media/avatars/upload-url          - issue presigned PUT URL
  POST /api/v1/media/avatars/{asset_id}/confirm  - confirm successful PUT
  GET  /api/v1/media/avatars/{asset_id}/download-url - issue presigned GET URL
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status  # noqa: B008
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.media.s3_client import get_s3_client
from app.services.media.schemas import (
    AvatarConfirmResponse,
    AvatarGetResponse,
    AvatarUploadRequest,
    AvatarUploadResponse,
)
from app.services.media.service import MediaService

router = APIRouter(prefix="/media/avatars", tags=["media"])


def _build_service(
    db: AsyncSession = Depends(get_db),  # noqa: B008
    s3_client: object = Depends(get_s3_client),  # noqa: B008
) -> MediaService:
    return MediaService(db=db, s3_client=s3_client)


@router.post(
    "/upload-url",
    response_model=AvatarUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue a pre-signed PUT URL for avatar upload",
    description=(
        "Returns a time-limited, content-type-locked presigned POST URL targeting a "
        "private S3 bucket. The client must PUT/POST to the returned URL within the "
        "expiry window and then call /confirm to activate the asset."
    ),
)
async def request_avatar_upload_url(
    body: AvatarUploadRequest,
    current_user: User = Depends(get_current_user),  # noqa: B008
    service: MediaService = Depends(_build_service),  # noqa: B008
) -> AvatarUploadResponse:
    try:
        return await service.issue_avatar_upload_url(current_user.id, body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.post(
    "/{asset_id}/confirm",
    response_model=AvatarConfirmResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm a successful avatar upload",
    description=(
        "Transitions the asset from 'pending' to 'confirmed'. "
        "Call this after the S3 PUT/POST succeeds."
    ),
)
async def confirm_avatar_upload(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),  # noqa: B008
    service: MediaService = Depends(_build_service),  # noqa: B008
) -> AvatarConfirmResponse:
    try:
        return await service.confirm_avatar_upload(current_user.id, asset_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc


@router.get(
    "/{asset_id}/download-url",
    response_model=AvatarGetResponse,
    status_code=status.HTTP_200_OK,
    summary="Issue a pre-signed GET URL for avatar download",
    description=(
        "Returns a time-limited presigned GET URL. "
        "Only confirmed assets owned by the requesting user are accessible."
    ),
)
async def request_avatar_download_url(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),  # noqa: B008
    service: MediaService = Depends(_build_service),  # noqa: B008
) -> AvatarGetResponse:
    try:
        return await service.issue_avatar_get_url(current_user.id, asset_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
