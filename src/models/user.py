from datetime import UTC, datetime
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class MiransasRank(str, Enum):
    NOVICE = "Novice"
    ARCHITECT = "Architect"
    ELITE = "Elite"
    CORE_DEVELOPER = "Core Developer"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=20, unique=True, index=True)
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    hashed_password: str
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    rank: MiransasRank = Field(default=MiransasRank.NOVICE)
    badges: list = Field(default_factory=list, sa_column=Column(JSON, nullable=True))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_login: Optional[datetime] = None
