from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class StockLine(BaseModel):
    product_id: UUID

    quantity: Decimal = Field(gt=0, decimal_places=6)

    unit_cost: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=6)


class TransferReceiveItem(BaseModel):
    product_id: UUID

    quantity_received: Decimal = Field(ge=0, decimal_places=6)

    quantity_damaged: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=6)


class PurchaseStockLine(StockLine):
    discount_percentage: Decimal = Field(default=Decimal("0"), ge=0, le=100, decimal_places=6)

    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=1, decimal_places=6)


class PurchaseOrderCreateRequest(BaseModel):
    supplier_id: UUID

    warehouse_id: UUID

    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")

    payment_terms_days: int = Field(default=30, ge=0, le=365)

    delivery_date: Optional[datetime] = None

    items: list[PurchaseStockLine] = Field(min_length=1, max_length=500)

    notes: Optional[str] = Field(default=None, max_length=1000)

    source_requisition_id: Optional[UUID] = None

    source_version: Optional[int] = Field(default=None, ge=1)


class PurchaseOrderUpdateRequest(BaseModel):
    version: int = Field(ge=1)

    reason: str = Field(min_length=5, max_length=2000)

    currency: Optional[str] = Field(default=None, pattern="^[A-Z]{3}$")

    payment_terms_days: Optional[int] = Field(default=None, ge=0, le=365)

    delivery_date: Optional[datetime] = None

    items: Optional[list[PurchaseStockLine]] = Field(default=None, min_length=1, max_length=500)

    notes: Optional[str] = Field(default=None, max_length=1000)


class LandedChargeItem(BaseModel):
    charge_type: Literal["FREIGHT", "CUSTOMS", "INSURANCE", "HANDLING", "OTHER"]

    amount: Decimal = Field(gt=0, decimal_places=6)

    allocation_method: Literal["VALUE", "QUANTITY"] = "VALUE"

    notes: Optional[str] = Field(default=None, max_length=255)


class PurchaseReturnItem(BaseModel):
    product_id: UUID

    quantity: Decimal = Field(gt=0, decimal_places=6)

    unit_cost: Optional[Decimal] = None

    lot_id: Optional[UUID] = None

    serial_numbers: list[str] = Field(default_factory=list, max_length=5000)

    reason: Optional[str] = Field(default=None, max_length=255)


class PurchaseReturnCreateRequest(BaseModel):
    goods_receipt_id: UUID

    warehouse_id: UUID

    items: list[PurchaseReturnItem] = Field(min_length=1, max_length=500)

    reason: str = Field(min_length=3, max_length=255)

    override_reason: Optional[str] = Field(default=None, max_length=500)


class InvoiceMatchLine(BaseModel):
    product_id: UUID

    quantity: Decimal = Field(gt=0, decimal_places=6, max_digits=20)

    unit_price: Decimal = Field(ge=0, decimal_places=6, max_digits=20)
    tax_rate: Optional[Decimal] = Field(default=None, ge=0, le=1, decimal_places=6)


class ThreeWayMatchResolveRequest(BaseModel):
    resolution_notes: str = Field(min_length=5, max_length=500)
    match_id: Optional[UUID] = None
    version: Optional[int] = Field(default=None, ge=1)


class ReturnLine(BaseModel):
    product_id: UUID

    quantity: Decimal = Field(gt=0, decimal_places=6)

    disposition: Literal["RESTOCK", "QUARANTINE", "DISCARD", "SCRAP"] = "QUARANTINE"

    lot_id: Optional[UUID] = None

    serial_number: Optional[str] = None

    condition_notes: Optional[str] = None


class ReturnAcceptInspectionItem(BaseModel):
    product_id: UUID

    disposition: Literal["RESTOCK", "QUARANTINE", "SCRAP", "DISCARD"]

    lot_id: Optional[UUID] = None

    serial_number: Optional[str] = None

    condition_notes: Optional[str] = None


class CountEntry(BaseModel):
    product_id: UUID

    quantity: Decimal = Field(ge=0, decimal_places=6)
