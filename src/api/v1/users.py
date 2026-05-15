from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from src.api.deps import CurrentUser, DbSession
from src.models.user import User
from src.schemas.user import UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(db: DbSession, current_user: CurrentUser, offset: int = 0, limit: int = 50):
    statement = select(User).offset(offset).limit(min(limit, 100))
    return db.exec(statement).all()


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: DbSession, current_user: CurrentUser):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user
