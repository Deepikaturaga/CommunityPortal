"""Registration service — COMP-001 / IF-001 (TASK-015)."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.schemas.identity import RegisterRequest
from app.services.identity.verify import issue_verification_token

logger = logging.getLogger(__name__)


class EmailAlreadyRegisteredError(Exception):
    """Raised when the supplied email is already in use."""


async def register_user(
    db: AsyncSession,
    payload: RegisterRequest,
) -> User:
    """
    Create a new, unverified user account.

    Steps:
    1. Uniqueness check — raises ``EmailAlreadyRegisteredError`` on conflict.
    2. Hash the plain-text password (bcrypt, cost from settings).
    3. Persist the ``User`` row with ``is_verified=False``.
    4. Issue a single-use DB-backed verification token and dispatch the email.

    The caller (router) owns the DB transaction boundary; this function
    does not call ``commit()`` directly so it can be composed safely.
    """
    # ── 1. Uniqueness check ──────────────────────────────────────────────────
    stmt = select(User).where(User.email == payload.email)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise EmailAlreadyRegisteredError(payload.email)

    # ── 2. Hash password ─────────────────────────────────────────────────────
    pw_hash = hash_password(payload.password)

    # ── 3. Persist user ──────────────────────────────────────────────────────
    user = User(
        email=payload.email,
        password_hash=pw_hash,
        full_name=payload.full_name,
        is_verified=False,
        is_active=True,
    )
    db.add(user)
    await db.flush()  # populate user.id without committing

    # ── 4. Issue single-use token + send email ───────────────────────────────
    await issue_verification_token(db, user)

    logger.info("New user registered: id=%s", user.id)
    return user
