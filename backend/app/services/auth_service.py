"""
Auth service: account registration, login, and JWT token issuance.
All DB operations use async SQLAlchemy 2.0 style.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.account import Account
from app.schemas.account_schema import RegisterRequest, TokenResponse


async def register_account(db: AsyncSession, req: RegisterRequest) -> Account:
    """Create a new account.  Raises ConflictError if email/username taken."""
    # Check uniqueness
    existing = await db.execute(
        select(Account).where(
            (Account.email == req.email) | (Account.username == req.username)
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError("Email or username already registered")

    account = Account(
        email=req.email,
        username=req.username,
        hashed_password=hash_password(req.password),
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def login_account(db: AsyncSession, email: str, password: str) -> TokenResponse:
    """
    Validate credentials and issue access + refresh tokens.
    Raises UnauthorizedError on bad credentials (generic message – no oracle).
    """
    result = await db.execute(select(Account).where(Account.email == email))
    account: Account | None = result.scalar_one_or_none()

    # Constant-time-ish: always call verify_password even on missing account
    # to prevent user-enumeration via timing.
    dummy_hash = "$2b$12$aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    hashed = account.hashed_password if account else dummy_hash
    password_ok = verify_password(password, hashed)

    if not account or not password_ok or not account.is_active:
        raise UnauthorizedError("Invalid credentials")

    access_token = create_access_token(str(account.id))
    refresh_token = create_refresh_token(str(account.id))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)
