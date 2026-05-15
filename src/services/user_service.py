from sqlmodel import Session

from src.models.user import User
from src.schemas.user import UserUpdate


class UserService:
    @staticmethod
    def update_profile(db: Session, user: User, user_in: UserUpdate) -> User:
        update_data = user_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(user, field, value)

        db.add(user)
        db.commit()
        db.refresh(user)
        return user
