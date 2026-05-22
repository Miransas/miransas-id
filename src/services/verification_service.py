from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.config import settings
from src.core.constants import AuditAction, TOKEN_TYPE_EMAIL_VERIFY
from src.models.audit_log import AuditLog
from src.models.user import User
from src.services.email_service import EmailService
from src.services.token_service import TokenService

_BAD_TOKEN = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid or expired verification token.",
)


class VerificationService:
    @staticmethod
    async def send_verification(
        db: AsyncSession,
        redis: Redis,
        user: User,
    ) -> None:
        """Generate token, store in Redis, send email.
        Raises 400 if user is already verified (their own account, safe to reveal).
        """
        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified.",
            )

        token = TokenService.generate_token()
        await TokenService.store_token(
            redis,
            token_type=TOKEN_TYPE_EMAIL_VERIFY,
            token=token,
            payload={"user_id": user.id, "email": user.email},
            ttl_seconds=settings.EMAIL_VERIFICATION_TTL_SECONDS,
        )
        await EmailService.send_verification_email(
            to=user.email,
            username=user.username,
            token=token,
        )

    @staticmethod
    async def verify_email(
        db: AsyncSession,
        redis: Redis,
        token: str,
    ) -> User:
        """Atomically consume token and mark user verified."""
        payload = await TokenService.consume_token(redis, TOKEN_TYPE_EMAIL_VERIFY, token)
        if not payload:
            raise _BAD_TOKEN

        user_id = payload.get("user_id")
        email_at_request = payload.get("email")

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()

        if not user or not user.is_active:
            raise _BAD_TOKEN

        # Guard: if email changed between token creation and use, reject.
        if user.email != email_at_request:
            raise _BAD_TOKEN

        if user.is_verified:
            return user  # idempotent

        user.is_verified = True
        audit = AuditLog(
            actor_id=user.id,
            target_user_id=user.id,
            action=AuditAction.EMAIL_VERIFIED,
            detail="{}",
            ip_address=None,
        )
        db.add(user)
        db.add(audit)
        await db.commit()
        await db.refresh(user)
        return user
