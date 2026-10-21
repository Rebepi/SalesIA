from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SalesRepCreateRequest(BaseModel):
    user_id: Optional[UUID] = None

    code: Optional[str] = None

    full_name: str = Field(..., min_length=2, max_length=255)

    territory: Optional[str] = Field(default="Principal", min_length=1, max_length=128)

    branch_id: Optional[UUID] = None

    team: Optional[str] = None

    supervisor_id: Optional[UUID] = None

    monthly_quota: Optional[Decimal] = Field(default=None, ge=0)


class SalesRepUpdateRequest(BaseModel):
    code: Optional[str] = None

    full_name: Optional[str] = None

    branch_id: Optional[UUID] = None

    team: Optional[str] = None

    supervisor_id: Optional[UUID] = None

    territory: Optional[str] = None

    monthly_quota: Optional[Decimal] = None

    is_active: Optional[bool] = None


class ReassignPortfolioRequest(BaseModel):
    target_rep_id: UUID

    reason: str = Field(..., min_length=3)
