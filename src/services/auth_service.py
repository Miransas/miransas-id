from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.security import get_password_hash, verify_password
from src.models.user import User
from src.schemas.user import UserCreate

# Computed once at startup; used to normalize response timing when a user is not found
# so an attacker cannot distinguish "user does not exist" from "wrong password" via timing.
_TIMING_DUMMY_HASH: str = get_password_hash("!!timing_normalization_sentinel!!")


def _utc_now() -> datetime:
    return datetime.now(UTC)


class AuthService:
    @staticmethod
    async def register_user(db: AsyncSession, user_in: UserCreate) -> User:
        result = await db.execute(
            select(User).where(
                (User.email == str(user_in.email)) | (User.username == user_in.username)
            )
        )
        if result.scalars().first():
            # Hash even on failure so timing is identical to a successful registration.
            get_password_hash(user_in.password)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration could not be completed.",
            )

        db_user = User(
            username=user_in.username,
            email=str(user_in.email),
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

        if user is None:
            # Run verify against a dummy hash to normalise timing.
            verify_password(password, _TIMING_DUMMY_HASH)
            return None

        if not verify_password(password, user.hashed_password):
            return None

        # Only write last_login on successful authentication — no DB write on failure.
        user.last_login = _utc_now()
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
