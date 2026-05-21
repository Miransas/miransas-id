from fastapi import APIRouter, HTTPException, status

from src.api.deps import CurrentUser, DbSession
from src.core.security import create_access_token
from src.schemas.auth import TokenResponse, UserLogin
from src.schemas.user import UserCreate, UserOut
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserOut)
async def register(user_in: UserCreate, db: DbSession) -> UserOut:
    return await AuthService.register_user(db, user_in)


@router.post("/login", response_model=TokenResponse)
async def login(user_in: UserLogin, db: DbSession) -> TokenResponse:
    user = await AuthService.authenticate_user(db, user_in.username_or_email, user_in.password)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return TokenResponse(access_token=create_access_token(subject=user.id))


@router.get("/me", response_model=UserOut)
async def get_me(current_user: CurrentUser) -> UserOut:
    return current_user
