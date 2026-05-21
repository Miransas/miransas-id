from fastapi import APIRouter, Request

from src.api.deps import CoreDeveloperUser, DbSession
from src.core.http import get_client_ip
from src.schemas.audit import AuditLogOut
from src.schemas.user import AdminUserOut, AdminUserUpdate
from src.services.admin_service import AdminService
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
