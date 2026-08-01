"""
FastAPI dependency: extract and validate the JWT bearer token,
resolve the current Account, and attach account_id to request.state
so per-account rate-limiting can read it without a second DB round-trip.
"""

from __future__ import annotations

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token
from app.models.account import Account

_bearer = HTTPBearer(auto_error=False)


async def get_current_account(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_async_session),
) -> Account:
    """
    Resolve the authenticated Account from the Authorization header.
    Sets request.state.account_id for downstream rate-limit dependencies.
    Raises UnauthorizedError on missing/invalid token.
    """
    if credentials is None:
        raise UnauthorizedError("Authorization header required")

    payload = decode_token(credentials.credentials)
    account_id: str | None = payload.get("sub")
    if not account_id:
        raise UnauthorizedError("Invalid token payload")

    result = await db.execute(select(Account).where(Account.id == account_id))
    account: Account | None = result.scalar_one_or_none()
    if account is None or not account.is_active:
        raise UnauthorizedError("Account not found or inactive")

    # Make account_id available to rate-limit deps without re-decoding the JWT.
    request.state.account_id = str(account.id)
    return account
