"""Auth/identity router — TASK-015 (register) + TASK-016 (verify/resend)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import _err
from app.schemas.identity import (
    RegisterRequest,
    RegisterResponse,
    ResendVerificationRequest,
    ResendVerificationResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from app.services.identity.register import EmailAlreadyRegisteredError, register_user
from app.services.identity.verify import (
    TokenAlreadyUsedError,
    TokenExpiredError,
    TokenNotFoundError,
    TokenSupersededError,
    UserAlreadyVerifiedError,
    UserNotFoundError,
    consume_verification_token,
    resend_verification_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# ── POST /register ────────────────────────────────────────────────────────────


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    responses={
        409: {"description": "Email already registered"},
        422: {"description": "Validation error"},
    },
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> RegisterResponse | JSONResponse:
    """
    **AC-001 / AC-002** — Register a new user account.

    - Email is normalised (lower-cased, trimmed) before uniqueness check.
    - Password policy is enforced by the request schema (Pydantic v2).
    - On success, a single-use verification token is persisted and the
      verification email is dispatched (HTTP 201).
    - On duplicate email → HTTP 409 (no field disclosure).
    - On policy violation → HTTP 422.
    """
    try:
        user = await register_user(db, payload)
    except EmailAlreadyRegisteredError:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=_err(
                "email_already_registered",
                "An account with this email address already exists.",
                field="email",
            ),
        )

    return RegisterResponse(
        message="Registration successful. Please check your email to verify your account.",
        email=user.email,
    )


# ── POST /verify-email ────────────────────────────────────────────────────────


@router.post(
    "/verify-email",
    response_model=VerifyEmailResponse,
    status_code=status.HTTP_200_OK,
    summary="Consume an email verification token",
    responses={
        200: {"description": "Email successfully verified"},
        404: {"description": "Token not found"},
        410: {"description": "Token expired, already used, or superseded"},
        422: {"description": "Validation error"},
    },
)
async def verify_email(
    payload: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> VerifyEmailResponse | JSONResponse:
    """
    **COMP-001** — Consume a single-use email verification token.

    - Expired tokens → HTTP 410 Gone.
    - Already-consumed tokens → HTTP 410 Gone.
    - Superseded tokens (user requested a resend) → HTTP 410 Gone.
    - Unknown token → HTTP 404.
    """
    try:
        user = await consume_verification_token(db, payload.token)
    except TokenNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=_err("token_not_found", "Verification token not found."),
        )
    except (TokenExpiredError, TokenAlreadyUsedError, TokenSupersededError):
        return JSONResponse(
            status_code=status.HTTP_410_GONE,
            content=_err(
                "token_invalid",
                "This verification link has expired or has already been used. "
                "Please request a new one.",
            ),
        )

    return VerifyEmailResponse(
        message="Email address verified successfully.",
        email=user.email,
    )


# ── POST /resend-verification ─────────────────────────────────────────────────


@router.post(
    "/resend-verification",
    response_model=ResendVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend the email verification link",
    responses={
        200: {"description": "Verification email sent (or silently accepted)"},
        422: {"description": "Validation error"},
    },
)
async def resend_verification(
    payload: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ResendVerificationResponse:
    """
    **COMP-001** — Issue a fresh verification token and dispatch the email.

    The response is always HTTP 200 regardless of whether the email exists or
    is already verified, to prevent account enumeration (VER-012).
    Old (unconsumed) tokens for this user are superseded atomically.
    """
    try:
        await resend_verification_token(db, payload.email)
    except (UserNotFoundError, UserAlreadyVerifiedError):
        # Intentionally indistinguishable from success — anti-enumeration.
        pass

    return ResendVerificationResponse(
        message=(
            "If that address is registered and unverified, "
            "a new verification email has been sent."
        )
    )
