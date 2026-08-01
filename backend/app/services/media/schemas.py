"""Pydantic schemas for the media/avatar presigned-URL API.

Keeps request, response, and persistence models separate (IF-013).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

# ── Constants ──────────────────────────────────────────────────────────────────

#: Allowed MIME types for avatar uploads.
ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/gif"}
)

#: Hard cap — must not exceed Settings.avatar_max_size_bytes.
#: This value is used for schema validation (defaults to 5 MiB);
#: the authoritative limit comes from Settings at runtime.
_DEFAULT_MAX_SIZE_BYTES: int = 5_242_880  # 5 MiB


# ── Request schemas ────────────────────────────────────────────────────────────


class AvatarUploadRequest(BaseModel):
    """Body sent by the client to request a presigned PUT URL."""

    content_type: Annotated[str, Field(description="MIME type of the image to be uploaded")]
    size_bytes: Annotated[
        int,
        Field(gt=0, le=_DEFAULT_MAX_SIZE_BYTES, description="Declared file size in bytes"),
    ]

    @field_validator("content_type")
    @classmethod
    def _content_type_must_be_allowed(cls, v: str) -> str:
        normalised = v.strip().lower()
        if normalised not in ALLOWED_CONTENT_TYPES:
            raise ValueError(
                f"content_type '{v}' is not permitted. "
                f"Allowed: {sorted(ALLOWED_CONTENT_TYPES)}"
            )
        return normalised


# ── Response schemas ───────────────────────────────────────────────────────────


class AvatarUploadResponse(BaseModel):
    """Returned to the client after the presigned PUT URL is issued."""

    asset_id: uuid.UUID = Field(description="Opaque ID for this upload slot")
    upload_url: str = Field(description="Time-limited presigned PUT URL")
    expires_in_seconds: int = Field(description="Seconds until the presigned URL expires")
    s3_key: str = Field(description="S3 object key — needed to confirm the upload")
    content_type: str = Field(description="Content-Type the PUT request must use")
    max_size_bytes: int = Field(description="Maximum allowed Content-Length for the PUT")


class AvatarGetResponse(BaseModel):
    """Returned when the client requests a presigned GET (download) URL."""

    asset_id: uuid.UUID
    download_url: str = Field(description="Time-limited presigned GET URL")
    expires_in_seconds: int
    content_type: str


class AvatarConfirmResponse(BaseModel):
    """Returned after the client confirms a successful PUT."""

    asset_id: uuid.UUID
    status: str  # "confirmed"
    message: str
