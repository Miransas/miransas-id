from datetime import UTC, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class UserSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    refresh_token_hash: str = Field(index=True, unique=True)
    refresh_token_id: str = Field(index=True, unique=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime
    revoked_at: Optional[datetime] = None
