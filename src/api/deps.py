from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlmodel import Session

from src.core.security import decode_access_token
from src.database.session import get_session
from src.models.user import MiransasRank, User
from src.schemas.token import TokenPayload

DbSession = Annotated[Session, Depends(get_session)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        token_data = TokenPayload(sub=payload.get("sub"), type=payload.get("type"))
    except JWTError as exc:
        raise credentials_exception from exc

    if token_data.sub is None or token_data.type != "access":
        raise credentials_exception

    try:
        user_id = int(token_data.sub)
    except ValueError as exc:
        raise credentials_exception from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exception

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_core_developer(current_user: CurrentUser) -> User:
    if current_user.rank != MiransasRank.CORE_DEV:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Core Developer rank required.",
        )

    return current_user


CoreDeveloperUser = Annotated[User, Depends(require_core_developer)]
