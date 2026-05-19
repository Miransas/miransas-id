from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import decode_token
from src.database.session import get_db
from src.models.user import User

# Asenkron veritabanı oturumu bağımlılığı
DbSession = Annotated[AsyncSession, Depends(get_db)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    """
    Geçerli token'ı doğrular ve veritabanından asenkron olarak kullanıcıyı döner.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Token decode edilerek 'sub' (user_id) alınır
        user_id_str = decode_token(token)
        user_id = int(user_id_str)
    except (HTTPException, ValueError):
        raise credentials_exception

    # Asenkron veritabanı sorgusu ile kullanıcıyı çekme
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if user is None or not user.is_active:
        raise credentials_exception

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
