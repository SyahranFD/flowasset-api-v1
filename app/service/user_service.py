import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..model.user import User
from ..schemas.user import RegisterRequest, LoginRequest, TokenResponse, AccessTokenResponse
from ..utils.time import wib_now
from .auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    get_user_by_token,
)


def register_user(db: Session, payload: RegisterRequest) -> User:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        id=uuid.uuid4(),
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        created_at=wib_now(),
    )
    db.add(user)
    db.flush()
    return user


def login_user(db: Session, payload: LoginRequest) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=create_access_token(subject=str(user.id)),
        refresh_token=create_refresh_token(subject=str(user.id)),
    )


def refresh_access_token(db: Session, refresh_token: str) -> AccessTokenResponse:
    user = get_user_by_token(db, refresh_token, "refresh")
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AccessTokenResponse(
        access_token=create_access_token(subject=str(user.id)),
    )
