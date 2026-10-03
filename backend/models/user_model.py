from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full name of user")
    email: str = Field(..., min_length=5, max_length=255, description="User email address")
    password: str = Field(..., min_length=6, max_length=128, description="Password (at least 6 chars)")
    store_name: Optional[str] = Field(
        default=None,
        max_length=150,
        description="Optional business or store name",
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters long")
        return v


class UserLogin(BaseModel):
    email: str = Field(..., min_length=3, max_length=255, description="Email or username")
    password: str = Field(..., min_length=1, max_length=128, description="User password")

    @field_validator("email")
    @classmethod
    def normalize_login_identity(cls, v: str) -> str:
        return v.strip().lower()


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    store_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @property
    def user_id(self) -> str:
        """Alias for id — used by route handlers for data ownership filtering."""
        return self.id


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
