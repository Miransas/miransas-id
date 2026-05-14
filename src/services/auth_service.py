from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.models.user import User
from src.schemas.user import UserCreate
from src.core.security import get_password_hash, verify_password, create_access_token

class AuthService:
    @staticmethod
    def register_user(db: Session, user_in: UserCreate):
        # 1. E-posta veya Kullanıcı adı zaten var mı?
        user_exists = db.query(User).filter(
            (User.email == user_in.email) | (User.username == user_in.username)
        ).first()
        
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
        user = db.query(User).filter(
            (User.email == username_or_email) | (User.username == username_or_email)
        ).first()
        
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user