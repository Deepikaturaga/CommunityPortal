    UserLoginRequest,

def _app_error(e: AppError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=e.detail)

        raise _app_error(e)
async def login(req: UserLoginRequest, db: AsyncSession = Depends(get_db)) -> dict:
        access, refresh = await user_service.authenticate_user(db, req)
        raise _app_error(e)
        raise _app_error(e)
        raise _app_error(e)
        raise _app_error(e)
        raise _app_error(e)
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.exceptions import AppError
from app.models.user import User
from app.schemas.user_schemas import (
    UserRegisterRequest,
    UserResponse,
    TokenResponse,
    RefreshRequest,
    PasswordChangeRequest,
    UserUpdateRequest,
)
from app.services import user_service
router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(req: UserRegisterRequest, db: AsyncSession = Depends(get_db)) -> User:
    try:
        return await user_service.register_user(db, req)
    except AppError as e:

@router.post("/token", response_model=TokenResponse)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> dict:

    try:
        access, refresh = await user_service.authenticate_user(
            db, UserLoginRequest(email=form_data.username, password=form_data.password)
        )
        return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}
    except AppError as e:


@router.post("/login", response_model=TokenResponse)

    try:
        return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}
    except AppError as e:






@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest, db: AsyncSession = Depends(get_db)) -> dict:
    try:
        access, new_refresh = await user_service.refresh_tokens(db, req.refresh_token)
        return {"access_token": access, "refresh_token": new_refresh, "token_type": "bearer"}
    except AppError as e:


@users_router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user


@users_router.put("/me", response_model=UserResponse)
async def update_me(
    req: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        return await user_service.update_user_profile(db, current_user, req)
    except AppError as e:


@users_router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    req: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await user_service.change_password(db, current_user, req)
    except AppError as e:


@users_router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)) -> User:
    try:
        return await user_service.get_user_by_id(db, user_id)
    except AppError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
