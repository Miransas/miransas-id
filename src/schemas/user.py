from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.models.user import MiransasRank


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    rank: MiransasRank = MiransasRank.NOVICE
    badges: list[str] = Field(default_factory=list)


class UserCreate(BaseModel):
    username: str = Field(max_length=20)
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    full_name: Optional[str]
    rank: MiransasRank
    badges: list[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
