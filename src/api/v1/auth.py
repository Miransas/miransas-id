from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError

from src.api.deps import CurrentUser, DbSession
from src.core.security import decode_access_token
from src.models.user import User
from src.schemas.token import RefreshTokenRequest, Token, TokenPayload
from src.schemas.user import UserCreate, UserOut, UserUpdate
from src.services.auth_service import AuthService
from src.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: DbSession):
    return AuthService.register_user(db, user_in)


@router.post("/login", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession):
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthService.create_token_pair(db, user)


@router.post("/refresh", response_model=Token)
def refresh_token(token_in: RefreshTokenRequest, db: DbSession):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token_in.refresh_token)
        token_data = TokenPayload(
            sub=payload.get("sub"),
            type=payload.get("type"),
            jti=payload.get("jti"),
        )
    except JWTError as exc:
        raise credentials_exception from exc

    if token_data.sub is None or token_data.type != "refresh" or token_data.jti is None:
        raise credentials_exception

    try:
        user_id = int(token_data.sub)
    except ValueError as exc:
        raise credentials_exception from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exception

    token_pair = AuthService.rotate_refresh_token(
        db,
        user,
        token_in.refresh_token,
        token_data.jti,
    )
    if token_pair is None:
        raise credentials_exception

    return token_pair


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(token_in: RefreshTokenRequest, db: DbSession):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token_in.refresh_token)
        token_data = TokenPayload(
            sub=payload.get("sub"),
            type=payload.get("type"),
            jti=payload.get("jti"),
        )
    except JWTError as exc:
        raise credentials_exception from exc

    if token_data.sub is None or token_data.type != "refresh" or token_data.jti is None:
        raise credentials_exception

    try:
        user_id = int(token_data.sub)
    except ValueError as exc:
        raise credentials_exception from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exception

    if not AuthService.revoke_refresh_token(db, user, token_in.refresh_token, token_data.jti):
        raise credentials_exception


@router.get("/me", response_model=UserOut)
def get_me(current_user: CurrentUser):
    return current_user


@router.patch("/me", response_model=UserOut)
def update_me(user_in: UserUpdate, db: DbSession, current_user: CurrentUser):
    return UserService.update_profile(db, current_user, user_in)
