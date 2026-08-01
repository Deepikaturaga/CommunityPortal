"""Email verification service — issuance, consumption, resend (TASK-016 / COMP-001)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.email_verification import EmailVerificationToken
from app.models.user import User
from app.services.email import send_verification_email

logger = logging.getLogger(__name__)


# ── Custom exceptions ─────────────────────────────────────────────────────────


class TokenNotFoundError(Exception):
    """The supplied token string does not exist in the database."""


class TokenExpiredError(Exception):
    """The token exists but its ``expires_at`` is in the past (HTTP 410)."""


class TokenAlreadyUsedError(Exception):
    """The token has already been consumed (HTTP 410)."""


class TokenSupersededError(Exception):
    """The token was superseded when a newer token was issued (HTTP 410)."""


class UserNotFoundError(Exception):
    """No user row found for the given email when attempting a resend."""


class UserAlreadyVerifiedError(Exception):
    """The user's email is already verified; a new token is not needed."""


# ── Issue ─────────────────────────────────────────────────────────────────────


async def issue_verification_token(
    db: AsyncSession,
    user: User,
    *,
    supersede_existing: bool = True,
) -> EmailVerificationToken:
    """
    Create and persist a fresh single-use verification token for *user*.

    If *supersede_existing* is True (default) all previous non-consumed tokens
    for this user are marked ``superseded=True`` so only the newest token is
    ever valid.

    The token row is **flushed but not committed** — the caller owns the
    transaction boundary.

    The verification email is dispatched after the flush so the token value
    is available; email failure is non-fatal (logged, not re-raised) so that
    the token row is still persisted and can be resent later.
    """
    settings = get_settings()
    ttl = settings.email_verification_token_ttl
    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=ttl)

    # ── Supersede any existing active tokens for this user ────────────────────
    if supersede_existing:
        stmt = (
            update(EmailVerificationToken)
            .where(
                EmailVerificationToken.user_id == user.id,
                EmailVerificationToken.consumed_at.is_(None),
                EmailVerificationToken.superseded.is_(False),
            )
            .values(superseded=True)
            .execution_options(synchronize_session=False)
        )
        await db.execute(stmt)

    # ── Create new token ──────────────────────────────────────────────────────
    token_obj = EmailVerificationToken(
        user_id=user.id,
        expires_at=expires_at,
    )
    db.add(token_obj)
    await db.flush()  # populates token_obj.id and token_obj.token

    # ── Dispatch email (non-fatal) ────────────────────────────────────────────
    try:
        send_verification_email(user.email, token_obj.token)
    except Exception:
        logger.exception(
            "Verification email dispatch failed for user %s — "
            "token persisted; user may request a resend.",
            user.id,
        )

    logger.info(
        "Verification token issued: user_id=%s token_id=%s expires_at=%s",
        user.id,
        token_obj.id,
        expires_at.isoformat(),
    )
    return token_obj


# ── Consume ───────────────────────────────────────────────────────────────────


async def consume_verification_token(
    db: AsyncSession,
    raw_token: str,
) -> User:
    """
    Validate *raw_token* and mark the user's email as verified.

    State-machine transitions
    -------------------------
    * ``TokenNotFoundError``  — token string unknown               → 404
    * ``TokenSupersededError`` — superseded by a newer token       → 410
    * ``TokenExpiredError``   — ``expires_at`` in the past         → 410
    * ``TokenAlreadyUsedError`` — ``consumed_at`` already set      → 410
    * On success: sets ``consumed_at = now()``, ``user.is_verified = True``.

    The session is flushed but not committed; the caller owns the transaction.
    """
    # ── Lookup ────────────────────────────────────────────────────────────────
    stmt = select(EmailVerificationToken).where(
        EmailVerificationToken.token == raw_token
    )
    result = await db.execute(stmt)
    token_obj: EmailVerificationToken | None = result.scalar_one_or_none()

    if token_obj is None:
        raise TokenNotFoundError(raw_token)

    # ── State checks (ordered: superseded → expired → consumed) ──────────────
    if token_obj.superseded:
        raise TokenSupersededError(token_obj.id)

    now = datetime.now(UTC)
    # Make expires_at tz-aware for comparison if stored as naive UTC
    expires_at = token_obj.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if now > expires_at:
        raise TokenExpiredError(token_obj.id)

    if token_obj.consumed_at is not None:
        raise TokenAlreadyUsedError(token_obj.id)

    # ── Fetch the user row ────────────────────────────────────────────────────
    user_stmt = select(User).where(User.id == token_obj.user_id)
    user_result = await db.execute(user_stmt)
    user: User | None = user_result.scalar_one_or_none()

    if user is None:  # defensive — FK cascade should prevent this
        raise TokenNotFoundError(f"user {token_obj.user_id} not found")

    # ── Mark token consumed + user verified ───────────────────────────────────
    token_obj.consumed_at = datetime.now(UTC)
    user.is_verified = True
    db.add(token_obj)
    db.add(user)
    await db.flush()

    logger.info(
        "Email verified: user_id=%s token_id=%s",
        user.id,
        token_obj.id,
    )
    return user


# ── Resend ────────────────────────────────────────────────────────────────────


async def resend_verification_token(
    db: AsyncSession,
    email: str,
) -> EmailVerificationToken:
    """
    Issue a fresh token for *email*, superseding any existing ones.

    Raises
    ------
    ``UserNotFoundError``       — no user row with this email
    ``UserAlreadyVerifiedError`` — user is already verified
    """
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user: User | None = result.scalar_one_or_none()

    if user is None:
        raise UserNotFoundError(email)

    if user.is_verified:
        raise UserAlreadyVerifiedError(email)

    return await issue_verification_token(db, user, supersede_existing=True)
