from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.security import get_password_hash, verify_password
from src.models.user import User
from src.schemas.user import UserCreate


def _utc_now() -> datetime:
    return datetime.now(UTC)


class AuthService:
    @staticmethod
    async def register_user(db: AsyncSession, user_in: UserCreate) -> User:
        result = await db.execute(
            select(User).where(
                (User.email == user_in.email) | (User.username == user_in.username)
            )
        )
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered.",
            )

        db_user = User(
            username=user_in.username,
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=get_password_hash(user_in.password),
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def authenticate_user(
        db: AsyncSession, username_or_email: str, password: str
    ) -> User | None:
        result = await db.execute(
            select(User).where(
                (User.email == username_or_email) | (User.username == username_or_email)
            )
        )
        user = result.scalars().first()

        if not user or not verify_password(password, user.hashed_password):
            return None

        user.last_login = _utc_now()
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
