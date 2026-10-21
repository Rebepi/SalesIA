from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UnitCreateModel(BaseModel):
    code: str = Field(..., min_length=1, max_length=16)

    name: str = Field(..., min_length=2, max_length=64)

    allow_fractions: bool = False

    precision_digits: int = Field(default=0, ge=0, le=6)


class UnitConversionCreateModel(BaseModel):
    from_unit: str = Field(..., min_length=1, max_length=16)

    to_unit: str = Field(..., min_length=1, max_length=16)

    factor: Decimal = Field(..., gt=0)

    product_id: Optional[UUID] = None


class UnitConvertRequest(BaseModel):
    from_unit: str

    to_unit: str

    quantity: Decimal = Field(..., gt=0)

    product_id: Optional[UUID] = None
