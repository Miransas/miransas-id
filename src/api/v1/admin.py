import json

from fastapi import APIRouter, HTTPException, Query, Request, status
from sqlmodel import select

from src.api.deps import CoreDeveloperUser, DbSession
from src.core.constants import AuditAction
from src.core.http import get_client_ip
from src.core.redis_client import get_redis
from src.models.audit_log import AuditLog
from src.models.login_attempt import LoginAttempt
from src.schemas.audit import AuditLogOut
from src.schemas.auth import AdminClearLockoutRequest, LoginAttemptOut
from src.schemas.user import AdminUserOut, AdminUserUpdate
from src.services.admin_service import AdminService
from src.services.lockout_service import LockoutService
from src.services.user_service import UserService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[AdminUserOut])
async def admin_list_users(
    db: DbSession,
    _: CoreDeveloperUser,
    offset: int = 0,
    limit: int = 50,
) -> list[AdminUserOut]:
    return await UserService.admin_list_users(db, offset, limit)


@router.patch("/users/{user_id}", response_model=AdminUserOut)
async def admin_update_user(
    user_id: int,
    body: AdminUserUpdate,
    request: Request,
    db: DbSession,
    current_user: CoreDeveloperUser,
) -> AdminUserOut:
    return await AdminService.update_user(
        db, current_user, user_id, body, get_client_ip(request)
    )


@router.get("/audit-log", response_model=list[AuditLogOut])
async def admin_audit_log(
    db: DbSession,
    _: CoreDeveloperUser,
    offset: int = 0,
    limit: int = 50,
) -> list[AuditLogOut]:
    return await AdminService.list_audit_log(db, offset, limit)


@router.post("/lockouts/clear")
async def admin_clear_lockout(
    body: AdminClearLockoutRequest,
    request: Request,
    db: DbSession,
    current_user: CoreDeveloperUser,
) -> dict:
    if not body.username_or_email and not body.ip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either username_or_email or ip is required.",
        )

    redis = await get_redis()
    await LockoutService.admin_clear_lockout(
        redis,
        username_or_email=body.username_or_email,
        ip=body.ip,
    )

    detail: dict = {}
    if body.username_or_email:
        detail["username_or_email"] = body.username_or_email
    if body.ip:
        detail["ip"] = body.ip

    audit = AuditLog(
        actor_id=current_user.id,
        target_user_id=current_user.id,
        action=AuditAction.LOCKOUT_CLEARED,
        detail=json.dumps(detail),
        ip_address=get_client_ip(request),
    )
    db.add(audit)
    await db.commit()

    return {"status": "cleared"}


@router.get("/login-attempts", response_model=list[LoginAttemptOut])
async def admin_list_login_attempts(
    db: DbSession,
    _: CoreDeveloperUser,
    username: str | None = None,
    ip: str | None = None,
    success: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> list[LoginAttemptOut]:
    q = select(LoginAttempt).order_by(LoginAttempt.created_at.desc())
    if username is not None:
        q = q.where(LoginAttempt.username_or_email == username)
    if ip is not None:
        q = q.where(LoginAttempt.ip_address == ip)
    if success is not None:
        q = q.where(LoginAttempt.success == success)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return list(result.scalars().all())
