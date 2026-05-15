from typing import Optional
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class AccessToken(BaseModel):
    access_token: str
    token_type: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    type: Optional[str] = None
    jti: Optional[str] = None
