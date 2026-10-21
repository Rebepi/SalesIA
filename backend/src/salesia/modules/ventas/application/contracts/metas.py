from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class SalesTargetCreateRequest(BaseModel):
    representative_id: UUID

    period: str = Field(..., pattern=r"^\d{4}-\d{2}$")

    target_type: str = Field(default="amount", pattern="^(amount|margin|units|clients)$")

    target_value: Decimal = Field(..., gt=0)

    currency: str = Field(..., pattern="^[A-Z]{3}$")

    scope: str = Field(default="individual", pattern="^(individual|team)$")
