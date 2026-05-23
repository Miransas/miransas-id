from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class LoginAttempt(SQLModel, table=True):
    __tablename__ = "loginattempt"

    id: Optional[int] = Field(default=None, primary_key=True)
    username_or_email: str = Field(index=True, max_length=255)
    ip_address: Optional[str] = Field(default=None, max_length=45, index=True)
    user_agent: Optional[str] = Field(default=None, max_length=500)
    success: bool = Field(default=False, index=True)
    # "invalid_credentials", "locked_out", "user_inactive"
    failure_reason: Optional[str] = Field(default=None, max_length=50)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
