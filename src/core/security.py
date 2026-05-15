from datetime import datetime, timedelta, timezone
from typing import Any, Union

from jose import jwt
from argon2 import PasswordHasher

from src.core.config import settings

ph = PasswordHasher()


def create_token(
    subject: Union[str, Any],
    token_type: str,
    expires_delta: timedelta,
) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject), "type": token_type}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: Union[str, Any], expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        token_expires_delta = expires_delta
    else:
        token_expires_delta = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    return create_token(subject, "access", token_expires_delta)


def create_refresh_token(subject: Union[str, Any]) -> str:
    return create_token(
        subject,
        "refresh",
        timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
    )


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def get_password_hash(password: str) -> str:
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except Exception:
        return False
