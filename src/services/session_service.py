from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.core.config import settings
from src.core.constants import SessionRevocationReason
from src.core.security import (
    create_access_token,
    create_refresh_token,
    create_token_id,
    decode_token,
    hash_token,
    safe_compare,
)
from src.models.session import UserSession
from src.models.user import User

_INVALID = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class SessionService:
    @staticmethod
    def _build_session_record(
        db: AsyncSession,
        user_id: int,
        family_id: str,
        user_agent: str | None,
        ip_address: str | None,
    ) -> tuple[str, UserSession]:
        """Adds a new session record to the db unit-of-work without committing."""
        token_id = create_token_id()
        expire_delta = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        refresh_token = create_refresh_token(
            subject=user_id,
            token_id=token_id,
            expires_delta=expire_delta,
        )
        session = UserSession(
            user_id=user_id,
            refresh_token_hash=hash_token(refresh_token),
            refresh_token_id=token_id,
            family_id=family_id,
            is_active=True,
            expires_at=_utc_now() + expire_delta,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        db.add(session)
        return refresh_token, session

    @staticmethod
    async def create_session(
        db: AsyncSession,
        user: User,
        family_id: str | None = None,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[str, UserSession]:
        """Creates a new session and returns (refresh_token_string, session)."""
        if family_id is None:
            family_id = create_token_id()  # new token family for this login

        refresh_token, session = SessionService._build_session_record(
            db, user.id, family_id, user_agent, ip_address
        )
        await db.commit()
        await db.refresh(session)
        return refresh_token, session

    @staticmethod
    async def rotate_session(
        db: AsyncSession,
        presented_refresh_token: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[str, str]:
        """Validates, rotates a refresh token, and returns (new_access_token, new_refresh_token).

        Reuse detection: if the presented token belongs to an already-inactive session,
        the entire token family is invalidated immediately.
        """
        # 1. Decode to get the jti claim
        try:
            payload = decode_token(presented_refresh_token, expected_type="refresh")
        except HTTPException:
            raise _INVALID

        jti = payload.get("jti")
        if not jti:
            raise _INVALID

        # 2. Find the session by its token_id (indexed, fast)
        result = await db.execute(
            select(UserSession).where(UserSession.refresh_token_id == jti)
        )
        session = result.scalars().first()

        if session is None:
            raise _INVALID

        # 3. Constant-time hash comparison
        if not safe_compare(session.refresh_token_hash, hash_token(presented_refresh_token)):
            raise _INVALID

        # 4. REUSE DETECTION — session was already rotated/revoked
        if not session.is_active:
            now = _utc_now()
            await db.execute(
                update(UserSession)
                .where(
                    UserSession.user_id == session.user_id,
                    UserSession.family_id == session.family_id,
                    UserSession.is_active == True,  # noqa: E712
                )
                .values(
                    is_active=False,
                    revoked_at=now,
                    revocation_reason=SessionRevocationReason.REUSE_DETECTED,
                )
            )
            await db.commit()
            raise _INVALID

        # 5. Expiry check
        if _as_utc(session.expires_at) <= _utc_now():
            session.is_active = False
            session.revoked_at = _utc_now()
            session.revocation_reason = SessionRevocationReason.EXPIRED
            db.add(session)
            await db.commit()
            raise _INVALID

        # 6. Load user
        user_result = await db.execute(select(User).where(User.id == session.user_id))
        user = user_result.scalars().first()
        if user is None or not user.is_active:
            raise _INVALID

        # 7. Mark old session as rotated
        now = _utc_now()
        session.is_active = False
        session.revoked_at = now
        session.revocation_reason = SessionRevocationReason.ROTATED
        session.last_used_at = now
        db.add(session)

        # 8. Build new session (same family)
        new_refresh_token, new_session = SessionService._build_session_record(
            db, user.id, session.family_id, user_agent, ip_address
        )

        # 9. Flush to get new_session.id, then update back-pointer
        await db.flush()
        session.replaced_by_session_id = new_session.id
        await db.commit()

        return create_access_token(subject=user.id, rank=user.rank.value), new_refresh_token

    @staticmethod
    async def revoke_session(
        db: AsyncSession,
        presented_refresh_token: str,
        reason: str = SessionRevocationReason.LOGOUT,
    ) -> None:
        """Revokes a single refresh token. Always succeeds — no information leaked."""
        try:
            payload = decode_token(presented_refresh_token, expected_type="refresh")
            jti = payload.get("jti")
        except HTTPException:
            return  # invalid token → idempotent success

        if not jti:
            return

        result = await db.execute(
            select(UserSession).where(
                UserSession.refresh_token_id == jti,
                UserSession.is_active == True,  # noqa: E712
            )
        )
        session = result.scalars().first()

        if session is None:
            return  # already gone

        # Verify hash to prevent someone with only the jti from revoking another's session
        if not safe_compare(session.refresh_token_hash, hash_token(presented_refresh_token)):
            return

        session.is_active = False
        session.revoked_at = _utc_now()
        session.revocation_reason = reason
        db.add(session)
        await db.commit()

    @staticmethod
    async def revoke_all_user_sessions(
        db: AsyncSession,
        user_id: int,
        reason: str = SessionRevocationReason.LOGOUT_ALL,
        auto_commit: bool = True,
    ) -> int:
        """Revokes all active sessions for a user. Returns the number of sessions revoked.

        Pass auto_commit=False when the caller manages its own transaction
        (e.g. AdminService needs session revoke + audit log in one atomic commit).
        """
        result = await db.execute(
            update(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.is_active == True,  # noqa: E712
            )
            .values(
                is_active=False,
                revoked_at=_utc_now(),
                revocation_reason=reason,
            )
        )
        if auto_commit:
            await db.commit()
        return result.rowcount

    @staticmethod
    async def list_user_sessions(
        db: AsyncSession,
        user_id: int,
    ) -> list[UserSession]:
        """Returns all active sessions for a user, newest first."""
        result = await db.execute(
            select(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.is_active == True,  # noqa: E712
            )
            .order_by(UserSession.created_at.desc())
        )
        return list(result.scalars().all())
