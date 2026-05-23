from fastapi import APIRouter, HTTPException, status

from src.api.deps import CurrentUser, DbSession
from src.schemas.user import PublicUserOut, UserOut
from src.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_current_user_me(user: CurrentUser) -> UserOut:
    """Get current authenticated user's full profile."""
    return user


@router.get("", response_model=list[PublicUserOut])
async def list_users(
    db: DbSession,
    _: CurrentUser,
    offset: int = 0,
    limit: int = 50,
) -> list[PublicUserOut]:
    return await UserService.list_users(db, offset, limit)


@router.get("/{user_id}", response_model=PublicUserOut)
async def get_user(
    user_id: int,
    db: DbSession,
    _: CurrentUser,
) -> PublicUserOut:
    user = await UserService.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user
