from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class VolumeTierCreateModel(BaseModel):
    min_quantity: Decimal = Field(..., gt=0)

    unit_price: Optional[Decimal] = Field(default=None, ge=0)

    discount_percentage: Optional[Decimal] = Field(default=None, ge=0, le=1)
