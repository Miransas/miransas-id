from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlmodel import Session, select

from src.core.config import settings
from src.models.user import User
from src.models.session import UserSession
from src.schemas.user import UserCreate
from src.core.security import (
    create_access_token,
    create_refresh_token,
    create_token_id,
    get_password_hash,
    hash_token,
    verify_password,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class AuthService:
    @staticmethod
    def register_user(db: Session, user_in: UserCreate):
        # 1. E-posta veya Kullanıcı adı zaten var mı?
        statement = select(User).where(
            (User.email == user_in.email) | (User.username == user_in.username)
        )
        user_exists = db.exec(statement).first()
        
        if user_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists."
            )
        
        # 2. Şifreyi Argon2 ile hashle
        hashed_pw = get_password_hash(user_in.password)
        
        # 3. Yeni kullanıcıyı oluştur (Şifreyi gizli tut!)
        db_user = User(
            username=user_in.username,
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hashed_pw,
            rank=user_in.rank,
            badges=user_in.badges
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def authenticate_user(db: Session, username_or_email: str, password: str):
        # Hem e-posta hem kullanıcı adı ile giriş desteği
        statement = select(User).where(
            (User.email == username_or_email) | (User.username == username_or_email)
        )
        user = db.exec(statement).first()
        
        if not user or not verify_password(password, user.hashed_password):
            return None

        user.last_login = utc_now()
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def create_token_pair(db: Session, user: User) -> dict[str, str]:
        refresh_token_id = create_token_id()
        refresh_token = create_refresh_token(subject=user.id, token_id=refresh_token_id)
        session = UserSession(
            user_id=user.id,
            refresh_token_hash=hash_token(refresh_token),
            refresh_token_id=refresh_token_id,
            expires_at=utc_now()
            + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
        )

        db.add(session)
        db.commit()

        return {
            "access_token": create_access_token(subject=user.id),
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    def rotate_refresh_token(db: Session, user: User, refresh_token: str, token_id: str):
        statement = select(UserSession).where(
            UserSession.user_id == user.id,
            UserSession.refresh_token_hash == hash_token(refresh_token),
            UserSession.refresh_token_id == token_id,
            UserSession.is_active == True,  # noqa: E712
        )
        session = db.exec(statement).first()

        if session is None or as_utc(session.expires_at) <= utc_now():
            return None

        session.is_active = False
        session.revoked_at = utc_now()
        db.add(session)
        db.commit()

        return AuthService.create_token_pair(db, user)

    @staticmethod
    def revoke_refresh_token(db: Session, user: User, refresh_token: str, token_id: str) -> bool:
        statement = select(UserSession).where(
            UserSession.user_id == user.id,
            UserSession.refresh_token_hash == hash_token(refresh_token),
            UserSession.refresh_token_id == token_id,
            UserSession.is_active == True,  # noqa: E712
        )
        session = db.exec(statement).first()

        if session is None:
            return False

        session.is_active = False
        session.revoked_at = utc_now()
        db.add(session)
        db.commit()
        return True
