from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class StoreCreditApplyRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, max_digits=20, decimal_places=6)
    source_ids: list[UUID] = Field(default_factory=list, max_length=100)
    reservation_id: UUID | None = None
