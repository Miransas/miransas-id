from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, JSON
import enum

class MiransasRank(str, enum.Enum):
    NOVICE = "Novice"
    ARCHITECT = "Architect"
    ELITE = "Elite"
    CORE_DEV = "Core Developer"

class UserBase(SQLModel):
    username: str = Field(index=True, unique=True, min_length=3, max_length=20)
    email: str = Field(index=True, unique=True)
    full_name: Optional[str] = None
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    
    # Miransas Ecosystem Data
    rank: MiransasRank = Field(default=MiransasRank.NOVICE)
    # JSON tipinde badge listesi: ["pull_shark", "early_adopter"]
    badges: List[str] = Field(default=[], sa_column=Column(JSON))

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    # İleride binboi tünelleri veya chess maçları için link ekleyebiliriz