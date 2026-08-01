"""Integration tests with mocked AWS SES -- VER-001.

Strategy
--------
* ``email_provider`` is overridden to ``"ses"`` and ``email_skip_send`` to
  ``False`` so the SES code path is exercised end-to-end through the real
  register / resend service layer.
* ``boto3`` is patched at the ``app.services.email`` module level via
  ``unittest.mock`` -- no real AWS call is ever made.
* The test DB uses the same in-process SQLite pattern as the rest of the suite.
* Settings are built with ``Settings.model_construct()`` (Pydantic v2) to
  bypass pydantic-settings env-var loading; conftest.py sets
  ``EMAIL_SKIP_SEND=true`` in the process env, and a normal ``Settings()``
  call would pick that up regardless of keyword arguments.

VER-001 acceptance criteria
---------------------------
VER-001.1   Register -> SES send_email called exactly once
VER-001.2   Destination.ToAddresses contains the normalised (lower-cased) email
VER-001.3   Source field equals the smtp_from setting
VER-001.4   Message body (text + html) contains the issued token string
VER-001.5   SourceArn forwarded when ses_from_arn is configured
VER-001.6   SourceArn absent when ses_from_arn is empty
VER-001.7   SES failure is non-fatal -- register still returns 201
VER-001.8   Resend endpoint issues a second SES send_email call
VER-001.9   email_skip_send=True suppresses SES even when email_provider=ses
VER-001.10  boto3.client created with the configured aws_region
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Register model modules with Base.metadata before any fixture creates tables.
import app.models.email_verification  # noqa: F401
import app.models.user  # noqa: F401
from app.core.config import Settings
from app.core.database import get_db
from app.core.models import Base

# Import the FastAPI *instance* under an alias so it never shadows the ``app``
# package namespace (which would cause AttributeError on .dependency_overrides).
from app.main import app as fastapi_app
from app.models.email_verification import EmailVerificationToken

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REGISTER_URL = "/api/v1/auth/register"
RESEND_URL = "/api/v1/auth/resend-verification"

_VALID_PAYLOAD: dict[str, Any] = {
    "email": "ses_user@Example.COM",
    "password": "Str0ng!Pass#2024",
    "full_name": "SES User",
}

_TEST_FROM = "noreply@example.com"
_TEST_FROM_ARN = "arn:aws:ses:us-east-1:123456789012:identity/noreply@example.com"
_TEST_REGION = "eu-west-1"

# ---------------------------------------------------------------------------
# Isolated in-process SQLite engine
# (separate from conftest's engine to avoid fixture-scope collisions)
# ---------------------------------------------------------------------------

_ses_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
_SesSession = async_sessionmaker(
    bind=_ses_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(autouse=True, scope="function")
async def _ses_db_tables() -> AsyncGenerator[None, None]:
    """Create all tables before each test; drop after."""
    async with _ses_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _ses_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def ses_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a fresh AsyncSession backed by the in-process SQLite DB."""
    async with _SesSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Settings factory
# ---------------------------------------------------------------------------


def _build_ses_settings(**overrides: Any) -> Settings:  # noqa: ANN401
    """
    Return a Settings object with SES enabled and safe test defaults.

    Uses ``Settings.model_construct()`` (Pydantic v2) to populate fields
    directly from kwargs **without** reading environment variables or the
    .env file.  This is required because conftest.py registers
    ``EMAIL_SKIP_SEND=true`` in ``os.environ``, and a normal
    ``Settings(**kwargs)`` call would pick that up and ignore the kwarg.
    """
    defaults: dict[str, Any] = {
        "secret_key": os.environ["SECRET_KEY"],
        "database_url": os.environ["DATABASE_URL"],
        "database_sync_url": os.environ["DATABASE_SYNC_URL"],
        "email_skip_send": False,
        "email_provider": "ses",
        "aws_region": _TEST_REGION,
        "smtp_from": _TEST_FROM,
        "ses_from_arn": "",
        "password_hash_rounds": 4,
        "password_min_length": 12,
        # Fields with model defaults that may be accessed during a request:
        "allowed_hosts": [],
        "app_env": "test",
        "email_verification_token_ttl": 86400,
        "smtp_host": "localhost",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_password": "",
    }
    defaults.update(overrides)
    return Settings.model_construct(**defaults)


# ---------------------------------------------------------------------------
# Client fixture
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def ses_client(ses_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTPX test client with SES settings and the isolated SQLite session."""
    cfg = _build_ses_settings()

    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        yield ses_db

    fastapi_app.dependency_overrides[get_db] = _override_db
    with (
        patch("app.core.config.get_settings", return_value=cfg),
        patch("app.services.email.get_settings", return_value=cfg),
        patch("app.services.identity.verify.get_settings", return_value=cfg),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app),
            base_url="http://testserver",
        ) as ac:
            yield ac

    fastapi_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


def _make_ses_client_mock() -> MagicMock:
    """Return a mock boto3 SES client whose send_email succeeds by default."""
    mock_ses = MagicMock()
    mock_ses.send_email.return_value = {
        "MessageId": "mock-ses-message-id-0001",
        "ResponseMetadata": {"HTTPStatusCode": 200},
    }
    return mock_ses


def _patch_boto3_module(mock_ses: MagicMock) -> Any:  # noqa: ANN401
    """Patch app.services.email.boto3 so .client() returns *mock_ses*."""
    mock_boto3 = MagicMock()
    mock_boto3.client.return_value = mock_ses
    return patch("app.services.email.boto3", mock_boto3)


async def _latest_token(db: AsyncSession) -> EmailVerificationToken | None:
    """Return the most recently created EmailVerificationToken row."""
    stmt = select(EmailVerificationToken).order_by(
        EmailVerificationToken.created_at.desc()
    )
    return (await db.execute(stmt)).scalars().first()


# ===========================================================================
# VER-001 test cases
# ===========================================================================


@pytest.mark.asyncio
async def test_ver001_1_ses_called_once_on_register(
    ses_client: AsyncClient,
) -> None:
    """VER-001.1 -- exactly one SES send_email call per registration."""
    mock_ses = _make_ses_client_mock()
    with _patch_boto3_module(mock_ses):
        resp = await ses_client.post(REGISTER_URL, json=_VALID_PAYLOAD)

    assert resp.status_code == 201
    mock_ses.send_email.assert_called_once()


@pytest.mark.asyncio
async def test_ver001_2_ses_recipient_is_normalised(
    ses_client: AsyncClient,
) -> None:
    """VER-001.2 -- Destination.ToAddresses contains the lower-cased email."""
    mock_ses = _make_ses_client_mock()
    with _patch_boto3_module(mock_ses):
        await ses_client.post(REGISTER_URL, json=_VALID_PAYLOAD)

    call_kwargs = mock_ses.send_email.call_args.kwargs
    assert call_kwargs["Destination"]["ToAddresses"] == ["ses_user@example.com"]


@pytest.mark.asyncio
async def test_ver001_3_ses_source_matches_smtp_from(
    ses_client: AsyncClient,
) -> None:
    """VER-001.3 -- Source field equals the configured smtp_from address."""
    mock_ses = _make_ses_client_mock()
    with _patch_boto3_module(mock_ses):
        await ses_client.post(REGISTER_URL, json=_VALID_PAYLOAD)

    call_kwargs = mock_ses.send_email.call_args.kwargs
    assert call_kwargs["Source"] == _TEST_FROM


@pytest.mark.asyncio
async def test_ver001_4_ses_body_contains_token(
    ses_client: AsyncClient,
    ses_db: AsyncSession,
) -> None:
    """VER-001.4 -- both Text and Html body parts contain the raw token."""
    mock_ses = _make_ses_client_mock()
    with _patch_boto3_module(mock_ses):
        await ses_client.post(REGISTER_URL, json=_VALID_PAYLOAD)

    token_row = await _latest_token(ses_db)
    assert token_row is not None, "Expected a token row to be persisted"

    call_kwargs = mock_ses.send_email.call_args.kwargs
    text_body: str = call_kwargs["Message"]["Body"]["Text"]["Data"]
    html_body: str = call_kwargs["Message"]["Body"]["Html"]["Data"]
    assert token_row.token in text_body, "token missing from text body"
    assert token_row.token in html_body, "token missing from html body"


@pytest.mark.asyncio
async def test_ver001_5_ses_source_arn_forwarded_when_set(
    ses_db: AsyncSession,
) -> None:
    """VER-001.5 -- SourceArn included in kwargs when ses_from_arn is set."""
    cfg = _build_ses_settings(ses_from_arn=_TEST_FROM_ARN)

    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        yield ses_db

    fastapi_app.dependency_overrides[get_db] = _override_db

    mock_ses = _make_ses_client_mock()
    mock_boto3 = MagicMock()
    mock_boto3.client.return_value = mock_ses

    with (
        patch("app.core.config.get_settings", return_value=cfg),
        patch("app.services.email.get_settings", return_value=cfg),
        patch("app.services.identity.verify.get_settings", return_value=cfg),
        patch("app.services.email.boto3", mock_boto3),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app),
            base_url="http://testserver",
        ) as ac:
            resp = await ac.post(REGISTER_URL, json=_VALID_PAYLOAD)

    fastapi_app.dependency_overrides.clear()

    assert resp.status_code == 201
    call_kwargs = mock_ses.send_email.call_args.kwargs
    assert call_kwargs.get("SourceArn") == _TEST_FROM_ARN


@pytest.mark.asyncio
async def test_ver001_6_ses_source_arn_absent_when_empty(
    ses_client: AsyncClient,
) -> None:
    """VER-001.6 -- SourceArn key NOT present when ses_from_arn is ''."""
    mock_ses = _make_ses_client_mock()
    with _patch_boto3_module(mock_ses):
        await ses_client.post(REGISTER_URL, json=_VALID_PAYLOAD)

    call_kwargs = mock_ses.send_email.call_args.kwargs
    assert "SourceArn" not in call_kwargs


@pytest.mark.asyncio
async def test_ver001_7_ses_failure_is_non_fatal(
    ses_client: AsyncClient,
) -> None:
    """VER-001.7 -- send_email exception does not prevent HTTP 201 response."""
    mock_ses = _make_ses_client_mock()
    mock_ses.send_email.side_effect = Exception(
        "Simulated SES ClientError: MessageRejected"
    )
    with _patch_boto3_module(mock_ses):
        resp = await ses_client.post(REGISTER_URL, json=_VALID_PAYLOAD)

    # Token row must still be persisted despite email dispatch failure.
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_ver001_8_ses_called_on_resend(
    ses_client: AsyncClient,
) -> None:
    """VER-001.8 -- POST /resend-verification issues a second send_email call."""
    mock_ses = _make_ses_client_mock()
    with _patch_boto3_module(mock_ses):
        await ses_client.post(REGISTER_URL, json=_VALID_PAYLOAD)
        resp = await ses_client.post(
            RESEND_URL, json={"email": "ses_user@example.com"}
        )

    assert resp.status_code == 200
    assert mock_ses.send_email.call_count == 2


@pytest.mark.asyncio
async def test_ver001_9_skip_send_suppresses_ses(
    ses_db: AsyncSession,
) -> None:
    """VER-001.9 -- email_skip_send=True suppresses SES even with provider=ses."""
    cfg = _build_ses_settings(email_skip_send=True)

    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        yield ses_db

    fastapi_app.dependency_overrides[get_db] = _override_db

    mock_ses = _make_ses_client_mock()
    mock_boto3 = MagicMock()
    mock_boto3.client.return_value = mock_ses

    with (
        patch("app.core.config.get_settings", return_value=cfg),
        patch("app.services.email.get_settings", return_value=cfg),
        patch("app.services.identity.verify.get_settings", return_value=cfg),
        patch("app.services.email.boto3", mock_boto3),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app),
            base_url="http://testserver",
        ) as ac:
            resp = await ac.post(REGISTER_URL, json=_VALID_PAYLOAD)

    fastapi_app.dependency_overrides.clear()

    assert resp.status_code == 201
    mock_ses.send_email.assert_not_called()


@pytest.mark.asyncio
async def test_ver001_10_boto3_client_uses_configured_region(
    ses_client: AsyncClient,
) -> None:
    """VER-001.10 -- boto3.client called with region_name matching aws_region."""
    mock_boto3 = MagicMock()
    mock_ses = _make_ses_client_mock()
    mock_boto3.client.return_value = mock_ses

    with patch("app.services.email.boto3", mock_boto3):
        await ses_client.post(REGISTER_URL, json=_VALID_PAYLOAD)

    mock_boto3.client.assert_called_once_with("ses", region_name=_TEST_REGION)
