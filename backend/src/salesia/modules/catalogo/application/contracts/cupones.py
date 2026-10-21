from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CouponCreateModel(BaseModel):
    code: str = Field(..., min_length=2, max_length=64)

    discount_type: str = Field(default="PERCENTAGE", pattern="^(PERCENTAGE|FIXED)$")

    discount_value: Decimal = Field(..., gt=0)

    min_purchase_amount: Decimal = Field(default=Decimal("0.000000"), ge=0)

    start_date: datetime

    end_date: datetime

    max_uses: int = Field(default=100, gt=0)


class CouponValidateRequest(BaseModel):
    code: str

    amount: Decimal = Field(..., ge=0)
