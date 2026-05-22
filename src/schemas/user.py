import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from src.core.password_policy import validate_password_strength
from src.models.user import MiransasRank

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")

_RESERVED_USERNAMES = frozenset([
    "admin", "root", "system", "miransas", "api", "auth",
    "support", "null", "undefined", "anonymous",
])


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    rank: MiransasRank = MiransasRank.NOVICE
    badges: list[str] = Field(default_factory=list)


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(min_length=12)
    full_name: Optional[str] = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return str(v).lower()

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not _USERNAME_RE.match(v):
            raise ValueError(
                "Username may only contain letters, digits, underscores, and hyphens (3–20 chars)."
            )
        if v.lower() in _RESERVED_USERNAMES:
            raise ValueError(f"'{v}' is a reserved username and cannot be registered.")
        return v.lower()

    @field_validator("password")
    @classmethod
    def _validate_password(cls, v: str) -> str:
        return validate_password_strength(v)

    @model_validator(mode="after")
    def validate_password_no_personal_info(self) -> "UserCreate":
        pw = getattr(self, "password", "") or ""
        username = getattr(self, "username", "") or ""
        email = str(getattr(self, "email", "") or "")

        if len(username) >= 3 and username.lower() in pw.lower():
            raise ValueError("Password must not contain your username.")

        email_local = email.split("@")[0].lower()
        if len(email_local) >= 3 and email_local in pw.lower():
            raise ValueError("Password must not contain part of your email address.")

        return self


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

    @field_validator("badges", mode="before")
    @classmethod
    def coerce_badges(cls, v: object) -> list:
        return v if v is not None else []


class PublicUserOut(BaseModel):
    """User profile visible to all authenticated users — no PII."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: Optional[str]
    rank: MiransasRank
    badges: list[str]

    @field_validator("badges", mode="before")
    @classmethod
    def coerce_badges(cls, v: object) -> list:
        return v if v is not None else []


class AdminUserOut(BaseModel):
    """Full user profile visible only to Core Developers."""
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

    @field_validator("badges", mode="before")
    @classmethod
    def coerce_badges(cls, v: object) -> list:
        return v if v is not None else []


class UserUpdateSelf(BaseModel):
    """Fields a user may change on their own profile."""
    full_name: Optional[str] = None


class AdminUserUpdate(BaseModel):
    """Fields a Core Developer may change on another user's profile."""
    rank: Optional[MiransasRank] = None
    badges: Optional[list[str]] = None
    is_active: Optional[bool] = None
