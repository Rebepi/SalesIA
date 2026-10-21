from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PromotionCreateModel(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)

    code: str = Field(..., min_length=2, max_length=64)

    priority: int = Field(default=10, ge=1)

    is_exclusive: bool = False

    start_date: datetime

    end_date: datetime

    product_id: Optional[UUID] = None

    min_quantity: Decimal = Field(default=Decimal("1.000000"), gt=0)

    discount_percentage: Decimal = Field(..., gt=0, le=1)

    max_quota: int = Field(default=1000, gt=0)


class PromotionUpdateModel(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)

    priority: Optional[int] = Field(default=None, ge=1)

    is_exclusive: Optional[bool] = None

    is_active: Optional[bool] = None

    max_quota: Optional[int] = Field(default=None, gt=0)

    end_date: Optional[datetime] = None
