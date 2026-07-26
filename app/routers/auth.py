from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    AccessTokenResponse,
    UserResponse,
)
from app.services.auth_service import register_user, login_user, refresh_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await register_user(db, payload)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await login_user(db, payload)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await refresh_access_token(db, payload.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
