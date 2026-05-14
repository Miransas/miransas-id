from typing import Optional, List
from pydantic import BaseModel, EmailStr
from src.models.user import MiransasRank

# Ortak alanlar
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    rank: MiransasRank = MiransasRank.NOVICE
    badges: List[str] = []

# Kayıt olurken (Input)
class UserCreate(UserBase):
    password: str

# API'den kullanıcı dönerken (Output) - Şifre YOK!
class UserOut(UserBase):
    id: int
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True # SQLModel objesini otomatik Pydantic'e çevirir