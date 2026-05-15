from fastapi import APIRouter, HTTPException, status

from src.api.deps import DbSession
from src.models.user import User
from src.schemas.user import UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: DbSession):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user
