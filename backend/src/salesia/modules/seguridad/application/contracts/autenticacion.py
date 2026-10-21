from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)
    mfa_code: Optional[str] = Field(default=None, max_length=128)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: UUID
    email: str
    company_id: UUID
    role: str
    permissions: list[str]


class RefreshTokenRequest(BaseModel):
    refresh_token: str
