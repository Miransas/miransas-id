from fastapi import APIRouter, HTTPException, Request, Response, status

from src.api.deps import CurrentUser, DbSession
from src.core.http import get_client_ip, get_user_agent
from src.core.security import create_access_token
from src.schemas.auth import RefreshTokenRequest, SessionOut, TokenPairResponse, UserLogin
from src.schemas.user import UserCreate, UserOut, UserUpdateSelf
from src.services.auth_service import AuthService
from src.services.session_service import SessionService
from src.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserOut)
async def register(user_in: UserCreate, db: DbSession) -> UserOut:
    return await AuthService.register_user(db, user_in)


@router.post("/login", response_model=TokenPairResponse)
async def login(user_in: UserLogin, request: Request, db: DbSession) -> TokenPairResponse:
    user = await AuthService.authenticate_user(db, user_in.username_or_email, user_in.password)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    refresh_token, _ = await SessionService.create_session(
        db,
        user,
        user_agent=get_user_agent(request),
        ip_address=get_client_ip(request),
    )
    return TokenPairResponse(
        access_token=create_access_token(subject=user.id),
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh(body: RefreshTokenRequest, request: Request, db: DbSession) -> TokenPairResponse:
    access_token, new_refresh_token = await SessionService.rotate_session(
        db,
        body.refresh_token,
        user_agent=get_user_agent(request),
        ip_address=get_client_ip(request),
    )
    return TokenPairResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshTokenRequest, db: DbSession) -> Response:
    await SessionService.revoke_session(db, body.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(current_user: CurrentUser, db: DbSession) -> Response:
    await SessionService.revoke_all_user_sessions(db, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/sessions", response_model=list[SessionOut])
async def list_my_sessions(current_user: CurrentUser, db: DbSession) -> list[SessionOut]:
    return await SessionService.list_user_sessions(db, current_user.id)


@router.patch("/me", response_model=UserOut)
async def update_me(user_in: UserUpdateSelf, current_user: CurrentUser, db: DbSession) -> UserOut:
    return await UserService.update_self(db, current_user, user_in)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: CurrentUser) -> UserOut:
    return current_user
