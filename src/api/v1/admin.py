from fastapi import APIRouter
from sqlmodel import select

from src.api.deps import CoreDeveloperUser, DbSession
from src.models.user import User
from src.schemas.user import UserOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
def list_all_users(db: DbSession, current_user: CoreDeveloperUser):
    statement = select(User).order_by(User.id)
    return db.exec(statement).all()
