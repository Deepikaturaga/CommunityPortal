"""S3 client factory — injectable, respects Settings.

Production: boto3 uses IAM instance role / ECS task role (no static creds).
Testing:    Caller injects a mock/stub via override_s3_client().
LocalStack: Set AWS_ENDPOINT_URL in environment.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING, Any

import boto3
from botocore.config import Config

from app.core.config import get_settings

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client  # only available when boto3-stubs[s3] is installed


def _make_s3_client() -> Any:
    """Build a real boto3 S3 client from settings."""
    settings = get_settings()

    kwargs: dict[str, Any] = {
        "region_name": settings.aws_region,
        "config": Config(
            signature_version="s3v4",
            retries={"max_attempts": 3, "mode": "standard"},
            connect_timeout=5,
            read_timeout=10,
        ),
    }
    # Static credentials only for local/CI overrides — production uses IAM roles
    if settings.aws_access_key_id:
        kwargs["aws_access_key_id"] = settings.aws_access_key_id
        kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    if settings.aws_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_endpoint_url

    return boto3.client("s3", **kwargs)


# Module-level singleton — replaced in tests via dependency override
_s3_client: Any = None


def get_s3_client() -> Generator[Any, None, None]:
    """FastAPI dependency that yields the S3 client singleton."""
    global _s3_client  # noqa: PLW0603
    if _s3_client is None:
        _s3_client = _make_s3_client()
    yield _s3_client


def override_s3_client(client: Any) -> None:
    """Test helper — inject a pre-configured stub/mock."""
    global _s3_client  # noqa: PLW0603
    _s3_client = client


def reset_s3_client() -> None:
    """Test helper — restore the real factory."""
    global _s3_client  # noqa: PLW0603
    _s3_client = None
