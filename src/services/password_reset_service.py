from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.config import settings
from src.core.constants import (
    AuditAction,
    SessionRevocationReason,
    TOKEN_TYPE_EMAIL_VERIFY,
    TOKEN_TYPE_PASSWORD_RESET,
)
from src.core.security import get_password_hash
from src.models.audit_log import AuditLog
from src.models.user import User
from src.services.email_service import EmailService
from src.services.session_service import SessionService
from src.services.token_service import TokenService

_BAD_TOKEN = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid or expired reset token.",
)


class PasswordResetService:
    @staticmethod
    async def request_reset(
        db: AsyncSession,
        redis: Redis,
        email: str,
    ) -> None:
        """User-enumeration-safe: always returns without error.
        If email exists and account is active, sends a reset email and writes an audit entry.
        If not, silently does nothing.
        """
        result = await db.execute(select(User).where(User.email == email.lower()))
        user = result.scalars().first()

        if not user or not user.is_active:
            return

        token = TokenService.generate_token()
        await TokenService.store_token(
            redis,
            token_type=TOKEN_TYPE_PASSWORD_RESET,
            token=token,
            payload={"user_id": user.id, "email": user.email},
            ttl_seconds=settings.PASSWORD_RESET_TTL_SECONDS,
        )

        audit = AuditLog(
            actor_id=user.id,
            target_user_id=user.id,
            action=AuditAction.PASSWORD_RESET_REQUESTED,
            detail="{}",
            ip_address=None,
        )
        db.add(audit)
        await db.commit()

        await EmailService.send_password_reset_email(
            to=user.email,
            username=user.username,
            token=token,
        )

    @staticmethod
    async def perform_reset(
        db: AsyncSession,
        redis: Redis,
        token: str,
        new_password: str,
    ) -> User:
        """Atomically consume token, update password, revoke all sessions, write audit."""
        payload = await TokenService.consume_token(redis, TOKEN_TYPE_PASSWORD_RESET, token)
        if not payload:
            raise _BAD_TOKEN

        user_id = payload.get("user_id")
        email_at_request = payload.get("email")

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()

        if not user or not user.is_active:
            raise _BAD_TOKEN

        # Defense: if email changed since token creation, reject
        if user.email != email_at_request:
            raise _BAD_TOKEN

        user.hashed_password = get_password_hash(new_password)
        db.add(user)

        audit = AuditLog(
            actor_id=user.id,
            target_user_id=user.id,
            action=AuditAction.PASSWORD_RESET_COMPLETED,
            detail="{}",
            ip_address=None,
        )
        db.add(audit)

        # Revoke all sessions in the same transaction (atomicity)
        await SessionService.revoke_all_user_sessions(
            db,
            user.id,
            reason=SessionRevocationReason.PASSWORD_RESET,
            auto_commit=False,
        )

        await db.commit()
        await db.refresh(user)

        # Revoke any other outstanding reset/verification tokens for this user
        await TokenService.revoke_all_user_tokens(redis, TOKEN_TYPE_PASSWORD_RESET, user.id)
        await TokenService.revoke_all_user_tokens(redis, TOKEN_TYPE_EMAIL_VERIFY, user.id)

        return user
