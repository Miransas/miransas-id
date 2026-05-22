from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from src.api.deps import CurrentUser, DbSession
from src.core.http import get_client_ip, get_user_agent
from src.core.rate_limit import RateLimitExceeded, check_rate_limit, rate_limit
from src.core.redis_client import get_redis
from src.core.security import create_access_token
from src.models.login_attempt import LoginAttempt
from src.schemas.auth import (
    ForgotPasswordRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    SendVerificationResponse,
    SessionOut,
    TokenPairResponse,
    UserLogin,
    VerifyEmailRequest,
)
from src.schemas.user import UserCreate, UserOut, UserUpdateSelf
from src.services.auth_service import AuthService
from src.services.lockout_service import LockoutService
from src.services.password_reset_service import PasswordResetService
from src.services.session_service import SessionService
from src.services.user_service import UserService
from src.services.verification_service import VerificationService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserOut,
    dependencies=[Depends(rate_limit(5, 600, "auth:register:ip"))],
)
async def register(user_in: UserCreate, db: DbSession) -> UserOut:
    return await AuthService.register_user(db, user_in)


@router.post(
    "/login",
    response_model=TokenPairResponse,
    dependencies=[Depends(rate_limit(10, 60, "auth:login:ip"))],
)
async def login(user_in: UserLogin, request: Request, db: DbSession) -> TokenPairResponse:
    redis = await get_redis()
    ip = get_client_ip(request) or "unknown"
    user_agent = get_user_agent(request)

    await LockoutService.check_locked(redis, user_in.username_or_email, ip)

    user = await AuthService.authenticate_user(db, user_in.username_or_email, user_in.password)

    if not user or not user.is_active:
        failure_reason = "user_inactive" if (user and not user.is_active) else "invalid_credentials"
        await LockoutService.record_failure(redis, user_in.username_or_email, ip)
        attempt = LoginAttempt(
            username_or_email=user_in.username_or_email,
            ip_address=ip,
            user_agent=user_agent,
            success=False,
            failure_reason=failure_reason,
        )
        db.add(attempt)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    await LockoutService.reset_username(redis, user_in.username_or_email)

    attempt = LoginAttempt(
        username_or_email=user_in.username_or_email,
        ip_address=ip,
        user_agent=user_agent,
        success=True,
        failure_reason=None,
    )
    db.add(attempt)

    refresh_token, _ = await SessionService.create_session(
        db,
        user,
        user_agent=user_agent,
        ip_address=ip,
    )
    return TokenPairResponse(
        access_token=create_access_token(subject=user.id),
        refresh_token=refresh_token,
    )


@router.post(
    "/refresh",
    response_model=TokenPairResponse,
    dependencies=[Depends(rate_limit(30, 60, "auth:refresh:ip"))],
)
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


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit(20, 60, "auth:logout:ip"))],
)
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


@router.post(
    "/send-verification",
    response_model=SendVerificationResponse,
    dependencies=[Depends(rate_limit(3, 3600, "auth:send_verification:ip"))],
)
async def send_verification(current_user: CurrentUser, db: DbSession) -> SendVerificationResponse:
    redis = await get_redis()
    # Per-user rate limit (3/hour): prevents spam when attacker holds a valid session
    user_key = f"ratelimit:send_verification:user:{current_user.id}"
    await check_rate_limit(redis, user_key, limit=3, window_seconds=3600)
    await VerificationService.send_verification(db, redis, current_user)
    return SendVerificationResponse()


@router.post(
    "/verify-email",
    response_model=UserOut,
    dependencies=[Depends(rate_limit(10, 60, "auth:verify_email:ip"))],
)
async def verify_email(body: VerifyEmailRequest, db: DbSession) -> UserOut:
    redis = await get_redis()
    return await VerificationService.verify_email(db, redis, body.token)


@router.post(
    "/forgot-password",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limit(5, 3600, "auth:forgot_password:ip"))],
)
async def forgot_password(body: ForgotPasswordRequest, db: DbSession) -> dict:
    redis = await get_redis()
    email_key = f"ratelimit:forgot_password:email:{body.email}"
    try:
        await check_rate_limit(redis, email_key, limit=3, window_seconds=3600)
    except RateLimitExceeded:
        # Silently drop: revealing per-email rate-limit state could leak email existence.
        pass
    else:
        await PasswordResetService.request_reset(db, redis, body.email)

    return {
        "message": "If an account exists with this email, a password reset link has been sent."
    }


@router.post(
    "/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit(10, 60, "auth:reset_password:ip"))],
)
async def reset_password(body: ResetPasswordRequest, db: DbSession) -> Response:
    redis = await get_redis()
    await PasswordResetService.perform_reset(db, redis, body.token, body.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
