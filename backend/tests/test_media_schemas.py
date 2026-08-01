"""Schema validation unit tests — AvatarUploadRequest.

VER-021: content-type allow-list and size-limit validations.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.services.media.schemas import ALLOWED_CONTENT_TYPES, AvatarUploadRequest


@pytest.mark.parametrize("ct", sorted(ALLOWED_CONTENT_TYPES))
def test_allowed_content_types_accepted(ct: str) -> None:
    req = AvatarUploadRequest(content_type=ct, size_bytes=100_000)
    assert req.content_type == ct


@pytest.mark.parametrize(
    "ct",
    ["application/pdf", "text/html", "image/tiff", "image/bmp", "application/octet-stream"],
)
def test_disallowed_content_types_rejected(ct: str) -> None:
    with pytest.raises(ValidationError, match="not permitted"):
        AvatarUploadRequest(content_type=ct, size_bytes=100_000)


def test_content_type_normalised_to_lowercase() -> None:
    req = AvatarUploadRequest(content_type="Image/JPEG", size_bytes=1000)
    assert req.content_type == "image/jpeg"


def test_size_zero_rejected() -> None:
    with pytest.raises(ValidationError):
        AvatarUploadRequest(content_type="image/jpeg", size_bytes=0)


def test_size_at_max_accepted() -> None:
    req = AvatarUploadRequest(content_type="image/jpeg", size_bytes=5_242_880)
    assert req.size_bytes == 5_242_880


def test_size_above_max_rejected() -> None:
    with pytest.raises(ValidationError):
        AvatarUploadRequest(content_type="image/jpeg", size_bytes=5_242_881)


def test_negative_size_rejected() -> None:
    with pytest.raises(ValidationError):
        AvatarUploadRequest(content_type="image/jpeg", size_bytes=-1)
