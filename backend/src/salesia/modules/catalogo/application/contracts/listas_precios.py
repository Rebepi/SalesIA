from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PriceListCreateModel(BaseModel):
    code: str = Field(..., min_length=2, max_length=64)

    name: str = Field(..., min_length=2, max_length=255)

    currency: str = Field(default="USD", min_length=3, max_length=3)

    priority: int = Field(default=10, ge=1)

    valid_from: Optional[datetime] = None

    valid_to: Optional[datetime] = None

    target_type: str = Field(default="all", max_length=32)

    target_id: Optional[str] = None


class PriceListUpdateModel(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)

    priority: Optional[int] = Field(default=None, ge=1)

    is_active: Optional[bool] = None

    valid_from: Optional[datetime] = None

    valid_to: Optional[datetime] = None

    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)

    target_type: Optional[str] = Field(default=None, max_length=32)

    target_id: Optional[str] = None


class PriceListItemCreateModel(BaseModel):
    product_id: UUID

    variant_id: Optional[UUID] = None

    fixed_price: Optional[Decimal] = Field(default=None, ge=0)

    discount_percentage: Optional[Decimal] = Field(default=None, ge=0, le=1)


class PriceListItemUpdateModel(BaseModel):
    fixed_price: Optional[Decimal] = Field(default=None, ge=0)

    discount_percentage: Optional[Decimal] = Field(default=None, ge=0, le=1)
