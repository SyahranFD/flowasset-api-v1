from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..config.database import get_db
from ..model.user import User
from ..schemas.user import RegisterRequest, LoginRequest, RefreshRequest, TokenResponse, AccessTokenResponse, UserOut
from ..service.auth import get_current_user
from ..service.user_service import register_user, login_user, refresh_access_token

router_user = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router_user.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    return register_user(db, payload)


@router_user.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return login_user(db, payload)


@router_user.post("/refresh", response_model=AccessTokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    return refresh_access_token(db, payload.refresh_token)


@router_user.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
