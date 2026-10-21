from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class AdjustmentRequest(BaseModel):
    warehouse_id: UUID

    product_id: UUID

    quantity_delta: Decimal = Field(decimal_places=6)

    reason: str = Field(min_length=3, max_length=128)

    unit_cost: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=6)

    evidence_url: Optional[str] = Field(default=None, max_length=500)

    location_id: Optional[UUID] = None

    lot_id: Optional[UUID] = None

    @model_validator(mode="after")
    def nonzero(self):

        if self.quantity_delta == 0:
            raise ValueError("El ajuste no puede ser cero")

        return self
