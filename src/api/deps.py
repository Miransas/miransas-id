from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import decode_token
from src.database.session import get_db
from src.models.user import MiransasRank, User

DbSession = Annotated[AsyncSession, Depends(get_db)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token, expected_type="access")
        user_id = int(payload["sub"])
    except (HTTPException, ValueError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if user is None or not user.is_active:
        raise credentials_exception

    return user


async def get_core_developer_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if current_user.rank != MiransasRank.CORE_DEVELOPER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )
    return current_user


CurrentUser = Annotated[User, Depends(get_current_user)]
CoreDeveloperUser = Annotated[User, Depends(get_core_developer_user)]
