from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserLogin(BaseModel):
    username_or_email: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_agent: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    last_used_at: Optional[datetime]
