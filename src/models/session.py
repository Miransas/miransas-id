from datetime import UTC, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class UserSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    refresh_token_hash: str = Field(index=True, unique=True)
    refresh_token_id: str = Field(index=True, unique=True)
    family_id: str = Field(index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    revocation_reason: Optional[str] = Field(default=None, max_length=50)
    replaced_by_session_id: Optional[int] = Field(default=None)
    user_agent: Optional[str] = Field(default=None, max_length=500)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    last_used_at: Optional[datetime] = None
