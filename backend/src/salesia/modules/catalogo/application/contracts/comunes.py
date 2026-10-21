from decimal import Decimal
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class VariantUpdateModel(BaseModel):
    sku: Optional[str] = None

    attributes: Optional[Dict[str, Any]] = None

    price_delta: Optional[Decimal] = None

    is_active: Optional[bool] = None


class BulkUpdateOperation(BaseModel):
    type: str = Field(..., pattern="^(PERCENTAGE_PRICE_ADJUSTMENT|FIXED_PRICE_ADJUSTMENT|SET_STATUS)$")

    value: str


class ImportItemModel(BaseModel):
    sku: str = Field(..., min_length=2, max_length=64)

    name: str = Field(..., min_length=2, max_length=255)

    category: str = Field(..., min_length=2, max_length=128)

    unit_of_measure: str = Field(default="NIU")

    unit_price: Decimal = Field(..., ge=0)

    unit_cost: Decimal = Field(default=Decimal("0.000000"), ge=0)

    tax_rate: Decimal = Field(default=Decimal("0.1800"), ge=0)

    product_type: str = Field(default="product", pattern="^(product|service)$")

    track_inventory: bool = True

    barcode: Optional[str] = None

    warranty_period_months: int = Field(default=0, ge=0)
