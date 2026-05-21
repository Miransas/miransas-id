import json

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.constants import AuditAction, SessionRevocationReason
from src.models.audit_log import AuditLog
from src.models.user import MiransasRank, User
from src.schemas.user import AdminUserUpdate
from src.services.session_service import SessionService


class AdminService:
    @staticmethod
    async def _count_active_core_devs(
        db: AsyncSession, exclude_id: int | None = None
    ) -> int:
        q = select(func.count()).select_from(User).where(
            User.rank == MiransasRank.CORE_DEVELOPER,
            User.is_active == True,  # noqa: E712
        )
        if exclude_id is not None:
            q = q.where(User.id != exclude_id)
        result = await db.execute(q)
        return result.scalar() or 0

    @staticmethod
    async def update_user(
        db: AsyncSession,
        actor: User,
        target_user_id: int,
        update: AdminUserUpdate,
        ip_address: str | None = None,
    ) -> User:
        if actor.id == target_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Self-modification via admin endpoints is not permitted.",
            )

        result = await db.execute(select(User).where(User.id == target_user_id))
        target = result.scalars().first()
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        # Enforce "at least one active Core Developer" invariant.
        target_is_active_core_dev = (
            target.rank == MiransasRank.CORE_DEVELOPER and target.is_active
        )
        if target_is_active_core_dev:
            will_be_disabled = update.is_active is False
            will_be_demoted = (
                update.rank is not None and update.rank != MiransasRank.CORE_DEVELOPER
            )
            if will_be_disabled or will_be_demoted:
                remaining = await AdminService._count_active_core_devs(
                    db, exclude_id=target_user_id
                )
                if remaining == 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot remove the last active Core Developer.",
                    )

        audit_entries: list[AuditLog] = []
        was_disabled = False

        if update.rank is not None and update.rank != target.rank:
            audit_entries.append(AuditLog(
                actor_id=actor.id,
                target_user_id=target.id,
                action=AuditAction.RANK_CHANGED,
                detail=json.dumps({"from": target.rank.value, "to": update.rank.value}),
                ip_address=ip_address,
            ))
            target.rank = update.rank

        if update.badges is not None:
            audit_entries.append(AuditLog(
                actor_id=actor.id,
                target_user_id=target.id,
                action=AuditAction.BADGES_UPDATED,
                detail=json.dumps({"badges": update.badges}),
                ip_address=ip_address,
            ))
            target.badges = update.badges

        if update.is_active is not None and update.is_active != target.is_active:
            action = AuditAction.USER_ENABLED if update.is_active else AuditAction.USER_DISABLED
            if not update.is_active:
                was_disabled = True
            audit_entries.append(AuditLog(
                actor_id=actor.id,
                target_user_id=target.id,
                action=action,
                detail=json.dumps({}),
                ip_address=ip_address,
            ))
            target.is_active = update.is_active

        if not audit_entries:
            return target  # nothing to do

        db.add(target)
        for entry in audit_entries:
            db.add(entry)
        await db.commit()
        await db.refresh(target)

        # Revoke all sessions immediately when a user is disabled.
        if was_disabled:
            await SessionService.revoke_all_user_sessions(
                db, target.id, reason=SessionRevocationReason.ADMIN_DISABLE
            )

        return target

    @staticmethod
    async def list_audit_log(
        db: AsyncSession, offset: int = 0, limit: int = 50
    ) -> list[AuditLog]:
        result = await db.execute(
            select(AuditLog)
            .offset(offset)
            .limit(min(limit, 100))
            .order_by(AuditLog.created_at.desc())
        )
        return list(result.scalars().all())
