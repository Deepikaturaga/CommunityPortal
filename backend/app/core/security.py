"""Password hashing utilities using bcrypt directly (bcrypt>=4.x API)."""

from __future__ import annotations

import bcrypt

from app.core.config import get_settings


def hash_password(plain: str) -> str:
    """Return the bcrypt hash of *plain* as a UTF-8 string."""
    rounds = get_settings().password_hash_rounds
    salt = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
