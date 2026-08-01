"""Auth router: register, login, logout, refresh, TOTP setup/verify."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response, status
from jose import jwt as _jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    generate_totp_secret,
    get_totp_uri,
    hash_password,
    verify_password,
    verify_totp,
)
from app.core.session import (
    clear_auth_cookies,
    extract_access_token,
    set_auth_cookies,
    validate_csrf,
)
from app.db.base import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RefreshResponse,
    RegisterRequest,
    TOTPSetupRequest,
    TOTPSetupResponse,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# ── Internal helpers ──────────────────────────────────────────────────────────


async def _get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


def _check_lockout(user: User) -> None:
    if user.is_locked():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked due to too many failed attempts",
        )


async def _record_failed_attempt(
    db: AsyncSession, user: User, settings: Settings
) -> None:
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= settings.max_failed_login_attempts:
        from datetime import timedelta

        user.locked_until = datetime.now(tz=timezone.utc) + timedelta(
            seconds=settings.lockout_duration_seconds
        )
    await db.flush()


async def _reset_failed_attempts(db: AsyncSession, user: User) -> None:
    user.failed_login_attempts = 0
    user.locked_until = None
    await db.flush()


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserOut:
    existing = await _get_user_by_email(db, body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    user = await _get_user_by_email(db, body.email)

    if not user or not verify_password(body.password, user.hashed_password):
        if user:
            await _record_failed_attempt(db, user, settings)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    _check_lockout(user)

    if user.totp_enabled:
        if not body.totp_code:
            return LoginResponse(
                message="MFA required",
                csrf_token="",
                user=UserOut.model_validate(user),
                mfa_required=True,
            )
        if not verify_totp(user.totp_secret or "", body.totp_code, settings=settings):
            await _record_failed_attempt(db, user, settings)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid TOTP code",
            )

    await _reset_failed_attempts(db, user)

    access = create_access_token(user.email, settings=settings)
    refresh = create_refresh_token(user.email, settings=settings)

    refresh_payload = _jwt.get_unverified_claims(refresh)
    user.refresh_token_jti = refresh_payload.get("jti")
    await db.flush()

    csrf = set_auth_cookies(
        response, access_token=access, refresh_token=refresh, settings=settings
    )
    return LoginResponse(csrf_token=csrf, user=UserOut.model_validate(user))


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
    csrf_cookie: Annotated[str | None, Cookie(alias="csrf_token")] = None,
    x_csrf_token: Annotated[str | None, Header()] = None,
) -> MessageResponse:
    if not validate_csrf(csrf_cookie, x_csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed",
        )
    clear_auth_cookies(response, settings=settings)
    return MessageResponse(message="Logged out successfully")


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token_endpoint(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    refresh_cookie: Annotated[str | None, Cookie(alias="refresh_token")] = None,
    csrf_cookie: Annotated[str | None, Cookie(alias="csrf_token")] = None,
    x_csrf_token: Annotated[str | None, Header()] = None,
) -> RefreshResponse:
    if not validate_csrf(csrf_cookie, x_csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed",
        )
    if not refresh_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )
    try:
        payload = decode_refresh_token(refresh_cookie, settings=settings)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    incoming_jti: str | None = payload.get("jti")
    user = await _get_user_by_email(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if user.refresh_token_jti != incoming_jti:
        user.refresh_token_jti = None
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected — all sessions revoked",
        )

    _check_lockout(user)

    new_access = create_access_token(user.email, settings=settings)
    new_refresh = create_refresh_token(user.email, settings=settings)

    new_refresh_payload = _jwt.get_unverified_claims(new_refresh)
    user.refresh_token_jti = new_refresh_payload.get("jti")
    await db.flush()

    csrf = set_auth_cookies(
        response, access_token=new_access, refresh_token=new_refresh, settings=settings
    )
    return RefreshResponse(csrf_token=csrf)


@router.post("/totp/setup", response_model=TOTPSetupResponse)
async def totp_setup(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    access_cookie: Annotated[str | None, Cookie(alias="access_token")] = None,
) -> TOTPSetupResponse:
    if not access_cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        raw = extract_access_token(access_cookie, settings=settings)
        token_payload = decode_access_token(raw, settings=settings)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    user = await _get_user_by_email(db, token_payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    secret = generate_totp_secret()
    user.totp_secret = secret
    await db.flush()

    uri = get_totp_uri(secret, user.email, settings=settings)
    return TOTPSetupResponse(secret=secret, uri=uri)


@router.post("/totp/confirm", response_model=MessageResponse)
async def totp_confirm(
    body: TOTPSetupRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    access_cookie: Annotated[str | None, Cookie(alias="access_token")] = None,
) -> MessageResponse:
    if not access_cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        raw = extract_access_token(access_cookie, settings=settings)
        token_payload = decode_access_token(raw, settings=settings)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    user = await _get_user_by_email(db, token_payload["sub"])
    if not user or not user.totp_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TOTP not initialized")

    if not verify_totp(user.totp_secret, body.code, settings=settings):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code")

    user.totp_enabled = True
    await db.flush()
    return MessageResponse(message="TOTP enabled successfully")


@router.get("/me", response_model=UserOut)
async def get_me(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    access_cookie: Annotated[str | None, Cookie(alias="access_token")] = None,
) -> UserOut:
    if not access_cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        raw = extract_access_token(access_cookie, settings=settings)
        token_payload = decode_access_token(raw, settings=settings)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    user = await _get_user_by_email(db, token_payload["sub"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return UserOut.model_validate(user)
