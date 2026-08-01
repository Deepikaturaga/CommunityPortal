"""Lockout policy: threshold enforcement, progressive delay, and owner alert.

Design contract
---------------
* ``apply_failure`` is the single entry-point after a bad-credential event.
  It increments the counter, decides whether to lock, applies a
  per-attempt back-off delay (to slow online brute-force even below the
  lock threshold), and emits a structured alert when the account locks.
* ``emit_lockout_alert`` is intentionally side-effect-isolated so tests
  can assert it was called without triggering real I/O.
* No plaintext passwords, secrets, or internal hashes ever appear in
  alert payloads or log records.
* Progressive delay is applied *inside* the service call (before the
  response is returned) so it is not easily bypassed by calling the
  endpoint in parallel within a single lockout window.  The delay is
  bounded by ``LOCKOUT_DELAY_MAX_SECONDS`` to avoid starving the
  ASGI worker pool.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Protocol

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.services.identity.models import AccountStatus, User

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Alert protocol — injectable for testing
# ---------------------------------------------------------------------------


class LockoutAlerter(Protocol):
    """Callable that sends / queues an owner alert.  Must be non-blocking."""

    async def __call__(
        self,
        user_id: uuid.UUID,
        email: str,
        locked_until: datetime,
        ip_address: str | None,
    ) -> None: ...


# ---------------------------------------------------------------------------
# Default (structured-log) alerter
# ---------------------------------------------------------------------------


async def _default_alerter(
    user_id: uuid.UUID,
    email: str,
    locked_until: datetime,
    ip_address: str | None,
) -> None:
    """Emit a WARN-level structured log record as the alert event.

    In production this record is forwarded by the log shipper (e.g.
    CloudWatch → SNS → email/PagerDuty).  The email field is included
    because it is *necessary* for the alert to be actionable; no
    password, hash, or credential is present.
    """
    log.warning(
        "LOCKOUT_ALERT",
        extra={
            "event": "account_locked",
            "user_id": str(user_id),
            # email is present only for the alert; never log passwords/hashes
            "email_domain": email.split("@")[-1],
            "locked_until": locked_until.isoformat(),
            "ip_address": ip_address,
        },
    )


# Module-level alerter — swap out in tests via ``set_alerter``.
_alerter: LockoutAlerter = _default_alerter


def set_alerter(alerter: LockoutAlerter) -> None:
    """Replace the module-level alerter (test / DI hook)."""
    global _alerter  # noqa: PLW0603
    _alerter = alerter


def get_alerter() -> LockoutAlerter:
    """Return the current alerter (useful for assertions in tests)."""
    return _alerter


# ---------------------------------------------------------------------------
# Progressive delay schedule
# ---------------------------------------------------------------------------

# Maps (1-based) attempt index → seconds to sleep before returning.
# Attempts beyond the table length use the last entry.
# Capped at LOCKOUT_DELAY_MAX_SECONDS from settings regardless.
_DELAY_SCHEDULE: list[float] = [
    0.0,   # attempt 1 — no delay
    0.5,   # attempt 2
    1.0,   # attempt 3
    2.0,   # attempt 4
    4.0,   # attempt 5+
]


def _delay_for_attempt(attempt_number: int, max_seconds: float) -> float:
    """Return the capped delay (seconds) for the given 1-based attempt number."""
    idx = max(0, min(attempt_number - 1, len(_DELAY_SCHEDULE) - 1))
    return min(_DELAY_SCHEDULE[idx], max_seconds)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def apply_failure(
    session: AsyncSession,
    user: User,
    ip_address: str | None = None,
    *,
    alerter: LockoutAlerter | None = None,
) -> datetime | None:
    """Record a failed credential attempt, lock if threshold reached.

    Parameters
    ----------
    session:
        The active async DB session.  The caller is responsible for
        committing after this coroutine returns.
    user:
        The ORM ``User`` row (already loaded by the login service).
    ip_address:
        Client IP for the alert payload (PII-minimal).
    alerter:
        Optional override for the module-level alerter (used in tests).

    Returns
    -------
    datetime | None
        ``locked_until`` if the account was just locked; ``None`` otherwise.
    """
    settings = get_settings()
    _alert = alerter or _alerter

    new_count = user.failed_login_count + 1
    locked_until: datetime | None = None
    new_status: AccountStatus = user.status

    if new_count >= settings.max_login_attempts:
        locked_until = datetime.now(UTC) + timedelta(
            seconds=settings.lockout_duration_seconds
        )
        new_status = AccountStatus.LOCKED
        log.info(
            "Account lock triggered: user_id=%s count=%d locked_until=%s",
            user.id,
            new_count,
            locked_until.isoformat(),
        )
        # Fire alert (non-blocking; errors must not propagate to the login path)
        try:
            await _alert(
                user_id=user.id,
                email=user.email,
                locked_until=locked_until,
                ip_address=ip_address,
            )
        except Exception:  # noqa: BLE001
            log.exception(
                "Lockout alert failed for user_id=%s — continuing safely", user.id
            )

    await session.execute(
        update(User)
        .where(User.id == user.id)
        .values(
            failed_login_count=new_count,
            locked_until=locked_until,
            status=new_status,
            updated_at=datetime.now(UTC),
        )
    )

    # Progressive delay — applied after DB write so caller can still commit
    max_delay = float(getattr(settings, "lockout_delay_max_seconds", 5))
    delay = _delay_for_attempt(new_count, max_delay)
    if delay > 0:
        await asyncio.sleep(delay)

    return locked_until


async def emit_lockout_alert(
    user_id: uuid.UUID,
    email: str,
    locked_until: datetime,
    ip_address: str | None,
) -> None:
    """Public convenience wrapper — delegates to the active alerter.

    Useful for callers that need to re-emit an alert (e.g. admin tooling)
    without duplicating the fallback/error-handling logic.
    """
    try:
        await _alerter(
            user_id=user_id,
            email=email,
            locked_until=locked_until,
            ip_address=ip_address,
        )
    except Exception:  # noqa: BLE001
        log.exception("emit_lockout_alert failed for user_id=%s", user_id)
