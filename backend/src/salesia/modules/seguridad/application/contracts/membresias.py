from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class InvitationRequest(BaseModel):
    email: EmailStr
    role: str
    branch_id: Optional[UUID] = None


class MembershipUpdateModel(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    reason: Optional[str] = Field(default=None, max_length=2000)
    access_hash: Optional[str] = Field(default=None, min_length=64, max_length=64)
    acknowledge_responsibilities: bool = False
