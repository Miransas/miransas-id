from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.models.user import User
from src.schemas.user import UserUpdateSelf


class UserService:
    @staticmethod
    async def update_self(db: AsyncSession, user: User, user_in: UserUpdateSelf) -> User:
        if user_in.full_name is not None:
            user.full_name = user_in.full_name
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user

    @staticmethod
    async def list_users(
        db: AsyncSession, offset: int = 0, limit: int = 50
    ) -> list[User]:
        result = await db.execute(
            select(User)
            .where(User.is_active == True)  # noqa: E712
            .offset(offset)
            .limit(min(limit, 100))
            .order_by(User.username)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(
            select(User).where(
                User.id == user_id,
                User.is_active == True,  # noqa: E712
            )
        )
        return result.scalars().first()

    @staticmethod
    async def admin_list_users(
        db: AsyncSession, offset: int = 0, limit: int = 50
    ) -> list[User]:
        result = await db.execute(
            select(User)
            .offset(offset)
            .limit(min(limit, 100))
            .order_by(User.id)
        )
        return list(result.scalars().all())
