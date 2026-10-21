from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from salesia.modules.pedidos.application.contracts.comunes import CancelItemRequest


class DocumentLine(BaseModel):
    product_id: UUID

    quantity: Decimal = Field(gt=0)

    discount_pct: Decimal = Field(default=Decimal("0"), ge=0, le=100)


class OrderCreateModel(BaseModel):
    customer_id: UUID

    branch_id: UUID

    warehouse_id: UUID

    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")

    payment_terms_days: int = Field(default=30, ge=0, le=3650)

    delivery_terms: Optional[str] = None

    customer_po_number: Optional[str] = None

    attachments: Optional[list[dict]] = None

    allow_backorder: bool = Field(default=False)

    lines: list[DocumentLine] = Field(min_length=1, max_length=500)


class ConfirmOrderRequest(BaseModel):
    allow_backorder: bool = Field(default=False)

    reservation_days: int = Field(default=7, ge=1, le=90)


class UpdateOrderLinesRequest(BaseModel):
    lines: list[DocumentLine] = Field(min_length=1, max_length=500)


class OrderCancelRequest(BaseModel):
    reason: Optional[str] = "Cancelación solicitada"

    version: Optional[int] = None

    cancelled_items: Optional[list[CancelItemRequest]] = None


class PickingScanRequest(BaseModel):
    order_line_number: Optional[int] = Field(default=None, ge=1)

    product_id: Optional[UUID] = None

    scanned_code: str = Field(min_length=1, max_length=128)

    quantity: Decimal = Field(gt=0)
