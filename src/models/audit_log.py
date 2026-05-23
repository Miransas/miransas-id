from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    actor_id: int = Field(foreign_key="user.id", index=True)
    target_user_id: int = Field(foreign_key="user.id", index=True)
    action: str = Field(max_length=50, index=True)
    detail: Optional[str] = None  # JSON string: before/after values
    ip_address: Optional[str] = Field(default=None, max_length=45)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
