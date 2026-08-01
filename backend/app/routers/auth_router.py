"""
Auth router: registration and login endpoints.

Both routes are guarded by per-action rate-limit dependencies (TASK-058):
  POST /auth/register  → rate_limit_register  (IP bucket)
  POST /auth/login     → rate_limit_login     (IP bucket)

On threshold breach each dependency raises RateLimitError → 429 with a
generic message (AC-031.2).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.middleware.ratelimit_deps import rate_limit_login, rate_limit_register
from app.schemas.account_schema import (
    AccountResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import login_account, register_account

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
    dependencies=[Depends(rate_limit_register)],
)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_async_session),
) -> AccountResponse:
    account = await register_account(db, body)
    return AccountResponse.model_validate(account)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and receive tokens",
    dependencies=[Depends(rate_limit_login)],
)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_async_session),
) -> TokenResponse:
    return await login_account(db, body.email, body.password)
