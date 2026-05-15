from typing import Optional, List

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.models.user import MiransasRank


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    rank: MiransasRank = MiransasRank.NOVICE
    badges: List[str] = Field(default_factory=list)


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    badges: Optional[List[str]] = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    is_verified: bool
