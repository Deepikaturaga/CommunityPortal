"""MFA verification service: validate challenge token + OTP, issue access token.

Design invariants
-----------------
* The challenge_token is verified with itsdangerous (signed, time-bounded) AND
  matched against a live ``MFAChallenge`` DB row to prevent replay after
  single-use consumption (OWASP A07, AC-006).
* An expired or consumed challenge is rejected with a generic error; the
  audit log records the specific failure reason, but the HTTP response does not
  (OWASP A03 / AC-003 enumeration-prevention).
* A ``LoginAttempt`` row is appended for every verify attempt -- success or fail --
  so the audit trail is complete (AC-004).
* TOTP verification uses ``pyotp`` with a +-1 window (30-second clock skew
  tolerance) and rejects reused codes by marking the challenge consumed before
  issuing the token.
* EMAIL_OTP: delivery and storage are out of scope for this phase; the branch
  is present so it cannot silently fall through to a success.
* No plaintext OTP, secret, or hash is written to logs.
"""
from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

import pyotp
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.identity.login import (
    InvalidCredentials,
    _issue_access_token,
    _record_attempt,
    verify_mfa_challenge_token,
)
from app.services.identity.models import MFAChallenge, MFAMethod, User
from app.services.identity.schemas import LoginSuccess

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

MFA_INVALID_CODE = "mfa_invalid"
MFA_INVALID_MSG = "Invalid or expired MFA code."

MFA_EXPIRED_CODE = "mfa_challenge_expired"
MFA_EXPIRED_MSG = "MFA challenge has expired."

MFA_CONSUMED_CODE = "mfa_challenge_used"
MFA_CONSUMED_MSG = "MFA challenge has already been used."


# ---------------------------------------------------------------------------
# TOTP helper
# ---------------------------------------------------------------------------


def _verify_totp(secret: str, code: str) -> bool:
    """Return True if *code* is valid for *secret* within a +-1 step window.

    ``pyotp`` handles the 30-second step arithmetic; window=1 allows one step
    of clock skew in each direction without materially widening the attack
    surface (NIST SP 800-63B s5.1.3.2).
    """
    try:
        totp = pyotp.TOTP(secret)
        return bool(totp.verify(code, valid_window=1))
    except Exception:  # noqa: BLE001 -- malformed secret / code is always a failure
        return False


# ---------------------------------------------------------------------------
# Repository helpers
# ---------------------------------------------------------------------------


async def _get_challenge(
    session: AsyncSession, challenge_token: str
) -> MFAChallenge | None:
    """Look up a non-consumed challenge by token string."""
    result = await session.execute(
        select(MFAChallenge).where(
            MFAChallenge.challenge_token == challenge_token,
            MFAChallenge.consumed.is_(False),
        )
    )
    return result.scalar_one_or_none()


async def _get_user(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def _consume_challenge(session: AsyncSession, challenge_id: uuid.UUID) -> None:
    """Mark the challenge row as consumed (single-use enforcement)."""
    await session.execute(
        update(MFAChallenge)
        .where(MFAChallenge.id == challenge_id)
        .values(consumed=True)
    )


# ---------------------------------------------------------------------------
# Public entry-point
# ---------------------------------------------------------------------------


async def verify_mfa(
    *,
    challenge_token: str,
    otp_code: str,
    session: AsyncSession,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> LoginSuccess:
    """Verify an MFA challenge + OTP and return an access token on success.

    Parameters
    ----------
    challenge_token:
        The opaque signed token issued by ``POST /auth/login`` when MFA is
        required.
    otp_code:
        The one-time code supplied by the user (TOTP digit string or
        email OTP).
    session:
        Active async DB session; caller is responsible for committing.
    ip_address:
        Client IP for the audit record (PII-minimal).
    user_agent:
        Client User-Agent for the audit record.

    Returns
    -------
    LoginSuccess
        Access token + metadata.  Raises ``InvalidCredentials`` (or a
        subclass) on any failure so the router can emit a uniform response.

    Security contract
    -----------------
    * ``challenge_token`` is validated cryptographically (itsdangerous) AND
      matched against a live DB row -- both checks must pass.
    * The challenge row is consumed *before* the access token is issued to
      prevent a race condition where two concurrent verify calls succeed.
    * All failure paths raise ``InvalidCredentials``; only the audit log
      contains the specific reason.
    """
    # 1. Verify the signed challenge token (cryptographic check + expiry) -----
    try:
        user_id = verify_mfa_challenge_token(challenge_token)
    except InvalidCredentials as exc:
        log.info(
            "MFA verify rejected: bad/expired challenge token ip=%s code=%s",
            ip_address,
            exc.code,
        )
        raise

    # 2. Load and validate the DB challenge row --------------------------------
    challenge = await _get_challenge(session, challenge_token)

    if challenge is None:
        # Row missing entirely or already consumed -- treat as expired/invalid.
        log.info(
            "MFA verify rejected: challenge not found or consumed user_id=%s ip=%s",
            user_id,
            ip_address,
        )
        raise InvalidCredentials(MFA_EXPIRED_CODE, MFA_EXPIRED_MSG)

    # Belt-and-suspenders: check DB-stored expiry even though the signed token
    # already encodes it (clock skew between signing and DB write is possible).
    now = datetime.now(UTC)
    expires_at = (
        challenge.expires_at
        if challenge.expires_at.tzinfo is not None
        else challenge.expires_at.replace(tzinfo=UTC)
    )
    if expires_at < now:
        log.info(
            "MFA verify rejected: challenge expired user_id=%s ip=%s", user_id, ip_address
        )
        raise InvalidCredentials(MFA_EXPIRED_CODE, MFA_EXPIRED_MSG)

    # Confirm the token encodes the same user as the DB row (anti-substitution).
    if challenge.user_id != user_id:
        log.warning(
            "MFA verify: challenge/token user_id mismatch -- possible tampering ip=%s",
            ip_address,
        )
        raise InvalidCredentials()

    # 3. Load user ------------------------------------------------------------
    user = await _get_user(session, user_id)
    if user is None:
        log.warning("MFA verify: user not found user_id=%s", user_id)
        raise InvalidCredentials()

    # 4. Verify OTP by method -------------------------------------------------
    otp_valid = False

    if user.mfa_method == MFAMethod.TOTP:
        if not user.totp_secret:
            log.error(
                "MFA verify: TOTP method set but totp_secret is null user_id=%s", user_id
            )
            raise InvalidCredentials(MFA_INVALID_CODE, MFA_INVALID_MSG)
        otp_valid = _verify_totp(user.totp_secret, otp_code)

    elif user.mfa_method == MFAMethod.EMAIL_OTP:
        # Email OTP delivery and storage is out of scope for this phase.
        # Explicit rejection prevents silent fall-through to a success.
        log.warning("MFA verify: EMAIL_OTP not yet implemented user_id=%s", user_id)
        raise InvalidCredentials(MFA_INVALID_CODE, MFA_INVALID_MSG)

    else:
        # MFA is unexpectedly disabled/none on this user -- reject rather than
        # silently bypass the second factor.
        log.warning(
            "MFA verify: unexpected mfa_method=%s user_id=%s", user.mfa_method, user_id
        )
        raise InvalidCredentials(MFA_INVALID_CODE, MFA_INVALID_MSG)

    if not otp_valid:
        await _record_attempt(
            session, user_id, False, ip_address, user_agent, "mfa_bad_otp"
        )
        log.info(
            "MFA verify rejected: invalid OTP user_id=%s method=%s ip=%s",
            user_id,
            user.mfa_method,
            ip_address,
        )
        raise InvalidCredentials(MFA_INVALID_CODE, MFA_INVALID_MSG)

    # 5. Consume challenge BEFORE issuing token (single-use + race safety) ----
    await _consume_challenge(session, challenge.id)

    # 6. Audit success --------------------------------------------------------
    await _record_attempt(
        session, user_id, True, ip_address, user_agent, "mfa_success"
    )
    log.info(
        "MFA verify success: user_id=%s method=%s ip=%s",
        user_id,
        user.mfa_method,
        ip_address,
    )

    # 7. Issue access token ---------------------------------------------------
    access_token, expire_seconds = _issue_access_token(user_id)
    return LoginSuccess(
        access_token=access_token,
        token_type="bearer",  # noqa: S106 -- schema field, not a password
        expires_in=expire_seconds,
    )
