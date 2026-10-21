from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LineItemRequest(BaseModel):
    product_id: Optional[UUID] = None

    sku: str = Field(..., min_length=1)

    product_name: str = Field(..., min_length=1)

    quantity: Decimal = Field(..., gt=0, le=Decimal("1000000"))

    unit_price: Decimal = Field(..., ge=0)

    tax_rate: Optional[Decimal] = Field(default=None, ge=0)

    discount: Decimal = Field(default=Decimal("0.00"), ge=0)

    cost_snapshot: Decimal = Field(default=Decimal("0.00"), ge=0)

    notes: Optional[str] = Field(default=None, max_length=500)

    serial_numbers: list[str] = Field(default_factory=list)
    order_line_number: Optional[int] = Field(default=None, ge=1)


class CreateSaleDraftRequest(BaseModel):
    company_id: Optional[UUID] = None

    branch_id: Optional[UUID] = None

    customer_id: Optional[UUID] = None

    currency: str = Field(..., min_length=3, max_length=3)

    is_credit: bool = Field(default=False)

    document_type: Literal["INVOICE", "RECEIPT"] = "RECEIPT"

    warehouse_id: Optional[UUID] = None

    notes: Optional[str] = Field(default=None, max_length=1000)

    delivery_address: Optional[str] = Field(default=None, max_length=1000)

    internal_observations: Optional[str] = Field(default=None, max_length=1000)

    coupon_code: Optional[str] = Field(default=None, max_length=64)

    exchange_rate: Decimal = Field(default=Decimal("1"), gt=0)

    sales_rep_id: Optional[UUID] = None

    payment_terms_days: Optional[int] = Field(default=None, ge=0, le=3650)
    order_id: Optional[UUID] = None

    lines: list[LineItemRequest] = Field(min_length=1, max_length=500)


class UpdateSaleDraftRequest(CreateSaleDraftRequest):
    version: int = Field(ge=1)


class ConfirmSaleRequest(BaseModel):
    is_credit_sale: bool = Field(default=False)

    allow_blocked_exception: bool = Field(default=False)

    exception_reason: Optional[str] = None

    version: Optional[int] = Field(default=None, ge=1)


class AnnulSaleRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=255)

    version: Optional[int] = Field(default=None, ge=1)

    approved_by: Optional[str] = Field(default=None)


class CorrectSaleRequest(BaseModel):
    notes: Optional[str] = Field(default=None, max_length=1000)

    reason: str = Field(..., min_length=3, max_length=255)
