"""FastAPI router for authentication endpoints.

Phase 1: POST /api/v1/auth/login
Phase 3: POST /api/v1/auth/mfa/verify
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.identity.login import (
    AccountInactive,
    AccountLocked,
    InvalidCredentials,
    LoginResult,
    login,
)
from app.services.identity.mfa import verify_mfa
from app.services.identity.schemas import (
    LoginErrorDetail,
    LoginRequest,
    LoginSuccess,
    MFAChallengeResponse,
    MFAVerifyRequest,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

DBDep = Annotated[AsyncSession, Depends(get_db)]


def _client_ip(request: Request) -> str | None:
    """Extract real client IP, respecting X-Forwarded-For from a trusted proxy."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post(
    "/login",
    response_model=LoginSuccess | MFAChallengeResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Authenticated — returns access token or MFA challenge.",
            "content": {
                "application/json": {
                    "examples": {
                        "token": {
                            "summary": "Direct token (no MFA)",
                            "value": {
                                "access_token": "<jwt>",
                                "token_type": "bearer",
                                "expires_in": 1800,
                            },
                        },
                        "mfa": {
                            "summary": "MFA required",
                            "value": {
                                "mfa_required": True,
                                "challenge_token": "<opaque>",
                                "mfa_method": "totp",
                                "expires_at": "2024-01-01T00:05:00Z",
                            },
                        },
                    }
                }
            },
        },
        401: {
            "description": (
                "Invalid credentials (generic — does not distinguish email/password)."
            )
        },
        403: {"description": "Account inactive or suspended."},
        423: {"description": "Account temporarily locked."},
        422: {"description": "Request validation error."},
    },
    summary="Authenticate with email and password",
    description=(
        "Validates email + password. Returns either a JWT access token "
        "(when MFA is not configured) or an MFA challenge token that must "
        "be completed at `POST /api/v1/auth/mfa/verify`. "
        "Failure responses are intentionally generic to prevent user enumeration."
    ),
)
async def post_login(
    body: LoginRequest,
    request: Request,
    db: DBDep,
) -> LoginResult:
    ip = _client_ip(request)
    ua = request.headers.get("User-Agent")

    try:
        return await login(body, db, ip_address=ip, user_agent=ua)

    except AccountLocked as exc:
        # Do NOT log email — avoid PII in log streams
        log.info("Login rejected: account locked ip=%s", ip)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=LoginErrorDetail(code=exc.code, message=exc.message).model_dump(),
        ) from exc

    except AccountInactive as exc:
        log.info("Login rejected: account inactive code=%s ip=%s", exc.code, ip)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=LoginErrorDetail(code=exc.code, message=exc.message).model_dump(),
        ) from exc

    except InvalidCredentials as exc:
        log.info("Login rejected: invalid credentials ip=%s", ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=LoginErrorDetail(code=exc.code, message=exc.message).model_dump(),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@router.post(
    "/mfa/verify",
    response_model=LoginSuccess,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "MFA verified — returns access token.",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "<jwt>",
                        "token_type": "bearer",
                        "expires_in": 1800,
                    }
                }
            },
        },
        401: {
            "description": (
                "Invalid or expired challenge token / OTP code. "
                "Generic — does not distinguish which field was wrong."
            )
        },
        422: {"description": "Request validation error."},
    },
    summary="Complete MFA verification",
    description=(
        "Accepts the ``challenge_token`` issued by ``POST /auth/login`` "
        "together with the one-time code from the user's authenticator. "
        "On success returns a JWT access token. "
        "The challenge is single-use; a second submission of the same token "
        "will be rejected even if the OTP is correct."
    ),
)
async def post_mfa_verify(
    body: MFAVerifyRequest,
    request: Request,
    db: DBDep,
) -> LoginSuccess:
    ip = _client_ip(request)
    ua = request.headers.get("User-Agent")

    try:
        return await verify_mfa(
            challenge_token=body.challenge_token,
            otp_code=body.otp_code,
            session=db,
            ip_address=ip,
            user_agent=ua,
        )
    except InvalidCredentials as exc:
        log.info(
            "MFA verify rejected: code=%s ip=%s",
            exc.code,
            ip,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=LoginErrorDetail(code=exc.code, message=exc.message).model_dump(),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
