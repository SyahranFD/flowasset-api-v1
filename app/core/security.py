from datetime import datetime, timedelta
from typing import Optional

import pytz
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

WIB = pytz.timezone("Asia/Jakarta")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def wib_now() -> datetime:
    """Return current time in WIB (UTC+7), timezone-naive for DB storage."""
    return datetime.now(WIB).replace(tzinfo=None)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    expire_delta = expires_minutes or settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.utcnow() + timedelta(minutes=expire_delta)
    payload = {"sub": subject, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and return payload. Raises JWTError on failure."""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
