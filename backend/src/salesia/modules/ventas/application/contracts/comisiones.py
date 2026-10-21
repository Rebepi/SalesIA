from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CommissionCalculateRequest(BaseModel):
    rep_id: UUID
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    recalculate: bool = False
    expected_version: int | None = Field(default=None, ge=1)
    reason: str | None = Field(default=None, min_length=5, max_length=2000)

    period: str = Field(..., pattern=r"^\d{4}-\d{2}$")

    gross_sales: Optional[Decimal] = Field(default=None, ge=0)

    returns_amount: Optional[Decimal] = Field(default=None, ge=0)

    target_quota: Optional[Decimal] = Field(default=None, gt=0)


class CommissionActionRequest(BaseModel):
    expected_version: int = Field(ge=1)
    reason: str = Field(min_length=5, max_length=2000)
    payout_reference: str | None = Field(default=None, min_length=3, max_length=128)


class CommissionObservationRequest(BaseModel):
    expected_version: int = Field(ge=1)
    sale_id: UUID | None = None
    reason: str = Field(min_length=5, max_length=2000)


class CommissionObservationResolution(BaseModel):
    expected_version: int = Field(ge=1)
    resolution: str = Field(min_length=5, max_length=2000)
    action: Literal["resolved", "rejected"] = "resolved"
