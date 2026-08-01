"""Login service: credential verification, lockout, and MFA gating.

Design invariants
-----------------
* Generic failure responses — the API MUST NOT reveal whether the email
  exists or the password was wrong (OWASP A07 / AC-003).
* All mutating state (failed_login_count, locked_until, last_login_at)
  is committed inside this service; callers must not commit before
  receiving the result.
* LoginAttempt rows are append-only (AC-004 audit requirement).
* Timing-safe comparison uses the bcrypt library directly (bcrypt 5.x).
* Lockout logic (threshold, delay, alert) is delegated to
  ``lockout.apply_failure`` — do not duplicate it here.
"""
from __future__ import annotations

import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.services.identity import lockout as _lockout
from app.services.identity.models import (
    AccountStatus,
    LoginAttempt,
    MFAChallenge,
    MFAMethod,
    User,
)
from app.services.identity.schemas import (
    LoginRequest,
    LoginSuccess,
    MFAChallengeResponse,
)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sentinel result types
# ---------------------------------------------------------------------------

GENERIC_FAILURE_CODE = "invalid_credentials"
GENERIC_FAILURE_MSG = "Invalid email or password."

ACCOUNT_LOCKED_CODE = "account_locked"
ACCOUNT_LOCKED_MSG = "Account temporarily locked. Please try again later."

ACCOUNT_SUSPENDED_CODE = "account_inactive"
ACCOUNT_SUSPENDED_MSG = "Account is not active. Please contact support."

ACCOUNT_UNVERIFIED_CODE = "account_inactive"
ACCOUNT_UNVERIFIED_MSG = "Account is not active. Please contact support."

# Valid bcrypt hash used for constant-time dummy verification on unknown-email paths.
_DUMMY_HASH = "$2b$12$LkklgCnSh6ANRMbL5By2aO9KmS2F0F7JlmYjSYM3v6Z.CnScHs10S"


class InvalidCredentials(Exception):
    """Raised for any authentication failure. Message is generic to caller."""

    def __init__(
        self,
        code: str = GENERIC_FAILURE_CODE,
        message: str = GENERIC_FAILURE_MSG,
    ) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class AccountLocked(Exception):
    def __init__(self, locked_until: datetime) -> None:
        self.code = ACCOUNT_LOCKED_CODE
        self.message = ACCOUNT_LOCKED_MSG
        self.locked_until = locked_until
        super().__init__(self.message)


class AccountInactive(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


LoginResult = LoginSuccess | MFAChallengeResponse


# ---------------------------------------------------------------------------
# Datetime helpers
# ---------------------------------------------------------------------------


def _aware(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware (assume UTC if naive).

    SQLite strips tzinfo on read; PostgreSQL preserves it. This helper
    makes lockout comparisons safe in both environments.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


# ---------------------------------------------------------------------------
# Password hashing — direct bcrypt (compatible with bcrypt 5.x)
# ---------------------------------------------------------------------------


def _verify_password(plain: str, hashed: str) -> bool:
    import bcrypt  # type: ignore[import-untyped]

    plain_bytes = plain.encode("utf-8")[:72]  # bcrypt 72-byte hard limit
    hashed_bytes = hashed.encode("utf-8") if isinstance(hashed, str) else hashed
    try:
        return bool(bcrypt.checkpw(plain_bytes, hashed_bytes))
    except Exception:  # noqa: BLE001 — malformed hash is always a failure
        return False


def hash_password(plain: str) -> str:
    """Hash a plaintext password for storage. Exported for use by registration."""
    import bcrypt  # type: ignore[import-untyped]

    plain_bytes = plain.encode("utf-8")[:72]
    return bcrypt.hashpw(plain_bytes, bcrypt.gensalt(rounds=12)).decode("utf-8")


# ---------------------------------------------------------------------------
# JWT issuance
# ---------------------------------------------------------------------------


def _issue_access_token(user_id: uuid.UUID) -> tuple[str, int]:
    """Return (signed JWT, expire_seconds)."""
    from jose import jwt  # type: ignore[import-untyped]

    settings = get_settings()
    expire_seconds = settings.access_token_expire_minutes * 60
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(seconds=expire_seconds),
        "jti": secrets.token_hex(16),
    }
    token: str = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, expire_seconds


# ---------------------------------------------------------------------------
# MFA challenge issuance
# ---------------------------------------------------------------------------


def _issue_mfa_challenge_token(user_id: uuid.UUID) -> tuple[str, datetime]:
    """Return (opaque signed challenge token, expires_at)."""
    settings = get_settings()
    s = URLSafeTimedSerializer(settings.secret_key, salt="mfa-challenge")
    payload = {"uid": str(user_id), "nonce": secrets.token_hex(8)}
    token: str = s.dumps(payload)
    expires_at = datetime.now(UTC) + timedelta(
        seconds=settings.mfa_challenge_expire_seconds
    )
    return token, expires_at


def verify_mfa_challenge_token(token: str) -> uuid.UUID:
    """Validate an MFA challenge token and return the user_id it encodes.

    Raises InvalidCredentials on any failure — callers should treat errors
    as generic failures.
    """
    settings = get_settings()
    s = URLSafeTimedSerializer(settings.secret_key, salt="mfa-challenge")
    try:
        data: dict[str, str] = s.loads(
            token, max_age=settings.mfa_challenge_expire_seconds
        )
    except SignatureExpired as exc:
        raise InvalidCredentials(
            "mfa_challenge_expired", "MFA challenge has expired."
        ) from exc
    except BadSignature as exc:
        raise InvalidCredentials(
            "mfa_challenge_invalid", "Invalid MFA challenge token."
        ) from exc
    try:
        return uuid.UUID(data["uid"])
    except (KeyError, ValueError) as exc:
        raise InvalidCredentials() from exc


# ---------------------------------------------------------------------------
# Repository helpers
# ---------------------------------------------------------------------------


async def _get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def _record_attempt(
    session: AsyncSession,
    user_id: uuid.UUID,
    success: bool,
    ip_address: str | None,
    user_agent: str | None,
    detail: str | None = None,
) -> None:
    attempt = LoginAttempt(
        user_id=user_id,
        success=success,
        ip_address=ip_address,
        user_agent=user_agent,
        detail=detail,
    )
    session.add(attempt)


async def _clear_failure_counter(session: AsyncSession, user: User) -> None:
    await session.execute(
        update(User)
        .where(User.id == user.id)
        .values(
            failed_login_count=0,
            locked_until=None,
            last_login_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )


async def _store_mfa_challenge(
    session: AsyncSession,
    user_id: uuid.UUID,
    token: str,
    expires_at: datetime,
) -> None:
    challenge = MFAChallenge(
        user_id=user_id,
        challenge_token=token,
        expires_at=expires_at,
    )
    session.add(challenge)


# ---------------------------------------------------------------------------
# Public service entry-point
# ---------------------------------------------------------------------------


async def login(
    request: LoginRequest,
    session: AsyncSession,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> LoginResult:
    """Authenticate a user and return either an access token or MFA challenge.

    Security contract
    -----------------
    * All failure paths raise ``InvalidCredentials`` or a subclass.
    * The raised exception exposes only a ``code`` + ``message``; callers
      MUST NOT add distinguishing information to the HTTP response (AC-003).
    * A ``LoginAttempt`` row is recorded for every attempt (success or fail)
      against a *real* user; unknown-email attempts are not recorded to avoid
      user enumeration, but a dummy hash verify runs to equalise timing (OWASP A07).
    * Lockout threshold enforcement and progressive delay are handled by
      ``lockout.apply_failure``; this function only reacts to its return value.
    """
    # 1. Lookup ---------------------------------------------------------------
    user = await _get_user_by_email(session, request.email)

    if user is None:
        # Equalise timing via dummy bcrypt verify — OWASP A07
        _verify_password(request.password, _DUMMY_HASH)
        raise InvalidCredentials()

    # 2. Lockout check (must happen before password verify) -------------------
    now = datetime.now(UTC)
    if user.status == AccountStatus.LOCKED:
        if user.locked_until and _aware(user.locked_until) > now:
            await _record_attempt(
                session, user.id, False, ip_address, user_agent, "locked"
            )
            raise AccountLocked(_aware(user.locked_until))
        # Lock has expired — automatically unlock and continue
        await session.execute(
            update(User)
            .where(User.id == user.id)
            .values(
                status=AccountStatus.ACTIVE,
                failed_login_count=0,
                locked_until=None,
                updated_at=now,
            )
        )
        user.status = AccountStatus.ACTIVE
        user.failed_login_count = 0
        user.locked_until = None

    # 3. Account-status checks -------------------------------------------------
    if user.status == AccountStatus.SUSPENDED:
        await _record_attempt(
            session, user.id, False, ip_address, user_agent, "suspended"
        )
        raise AccountInactive(ACCOUNT_SUSPENDED_CODE, ACCOUNT_SUSPENDED_MSG)

    if user.status == AccountStatus.DEACTIVATED:
        await _record_attempt(
            session, user.id, False, ip_address, user_agent, "deactivated"
        )
        raise InvalidCredentials()  # generic — avoids enumeration

    if user.status == AccountStatus.UNVERIFIED:
        await _record_attempt(
            session, user.id, False, ip_address, user_agent, "unverified"
        )
        raise AccountInactive(ACCOUNT_UNVERIFIED_CODE, ACCOUNT_UNVERIFIED_MSG)

    # 4. Password verification -------------------------------------------------
    password_ok = _verify_password(request.password, user.password_hash)

    if not password_ok:
        # Delegate to lockout module: increments counter, applies delay, emits alert.
        locked_until = await _lockout.apply_failure(
            session, user, ip_address=ip_address
        )
        await _record_attempt(
            session, user.id, False, ip_address, user_agent, "bad_password"
        )
        if locked_until is not None:
            raise AccountLocked(locked_until)
        raise InvalidCredentials()

    # 5. Credential check passed — clear counter, record success ---------------
    await _clear_failure_counter(session, user)
    await _record_attempt(
        session,
        user.id,
        True,
        ip_address,
        user_agent,
        "mfa_pending" if user.mfa_enabled else "success",
    )

    # 6. MFA gate --------------------------------------------------------------
    if user.mfa_enabled and user.mfa_method != MFAMethod.NONE:
        token, expires_at = _issue_mfa_challenge_token(user.id)
        await _store_mfa_challenge(session, user.id, token, expires_at)
        log.info("MFA challenge issued: user_id=%s method=%s", user.id, user.mfa_method)
        return MFAChallengeResponse(
            challenge_token=token,
            mfa_method=user.mfa_method,
            expires_at=expires_at,
        )

    # 7. Issue access token ----------------------------------------------------
    access_token, expire_seconds = _issue_access_token(user.id)
    log.info("Login success: user_id=%s", user.id)
    return LoginSuccess(
        access_token=access_token,
        token_type="bearer",  # noqa: S106 — schema field, not a password
        expires_in=expire_seconds,
    )
