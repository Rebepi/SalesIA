from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProductCreateModel(BaseModel):
    sku: str = Field(..., min_length=2, max_length=64)

    name: str = Field(..., min_length=2, max_length=255)

    category: Optional[str] = Field(default=None, min_length=2, max_length=128)

    category_id: Optional[UUID] = None

    unit_of_measure: str = Field(default="NIU", min_length=1, max_length=16)

    unit_price: Decimal = Field(..., ge=0)

    unit_cost: Decimal = Field(default=Decimal("0.000000"), ge=0)

    tax_rate: Decimal = Field(default=Decimal("0.1800"), ge=0)

    description: Optional[str] = None

    product_type: str = Field(default="product", pattern="^(product|service)$")

    track_inventory: bool = True

    barcode: Optional[str] = None

    warranty_period_months: int = Field(default=0, ge=0)

    warranty_policy: Optional[str] = None

    price_includes_tax: bool = False

    is_kit: bool = False

    supplier_id: Optional[UUID] = None

    brand: Optional[str] = Field(default=None, max_length=128)

    image_url: Optional[str] = Field(default=None, max_length=512)

    length_cm: Optional[Decimal] = Field(default=None, ge=0)

    width_cm: Optional[Decimal] = Field(default=None, ge=0)

    height_cm: Optional[Decimal] = Field(default=None, ge=0)

    weight_kg: Optional[Decimal] = Field(default=None, ge=0)

    tracking_mode: str = Field(default="NONE", pattern="^(NONE|LOT|SERIAL)$")

    initial_stock_quantity: Decimal = Field(default=Decimal("0"), ge=0)

    warehouse_id: Optional[UUID] = None

    reorder_point: Decimal = Field(default=Decimal("0"), ge=0)

    reorder_quantity: Decimal = Field(default=Decimal("0"), ge=0)


class ProductUpdateModel(BaseModel):
    name: Optional[str] = None

    category: Optional[str] = None

    unit_price: Optional[Decimal] = Field(default=None, ge=0)

    unit_cost: Optional[Decimal] = Field(default=None, ge=0)

    tax_rate: Optional[Decimal] = Field(default=None, ge=0)

    unit_of_measure: Optional[str] = None

    is_active: Optional[bool] = None

    description: Optional[str] = None

    product_type: Optional[str] = Field(default=None, pattern="^(product|service)$")

    track_inventory: Optional[bool] = None

    barcode: Optional[str] = None

    status: Optional[str] = Field(default=None, pattern="^(active|discontinued|suspended|archived)$")

    warranty_period_months: Optional[int] = Field(default=None, ge=0)

    warranty_policy: Optional[str] = None

    price_includes_tax: Optional[bool] = None

    is_kit: Optional[bool] = None

    category_id: Optional[UUID] = None

    supplier_id: Optional[UUID] = None

    brand: Optional[str] = Field(default=None, max_length=128)

    image_url: Optional[str] = Field(default=None, max_length=512)

    length_cm: Optional[Decimal] = Field(default=None, ge=0)

    width_cm: Optional[Decimal] = Field(default=None, ge=0)

    height_cm: Optional[Decimal] = Field(default=None, ge=0)

    weight_kg: Optional[Decimal] = Field(default=None, ge=0)

    tracking_mode: Optional[str] = Field(default=None, pattern="^(NONE|LOT|SERIAL)$")


class ProductDuplicateModel(BaseModel):
    sku: str = Field(..., min_length=2, max_length=64)

    name: Optional[str] = Field(default=None, min_length=2, max_length=255)

    barcode: Optional[str] = Field(default=None, min_length=3, max_length=64)
