from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from salesia.modules.inventario.application.contracts.comunes import ReturnAcceptInspectionItem, ReturnLine, StockLine


class ReturnCreateRequest(BaseModel):
    __module__ = "salesia.modules.inventory.presentation.router"
    sale_id: UUID
    warehouse_id: UUID
    reason: str = Field(min_length=3, max_length=128)
    items: list[ReturnLine] = Field(min_length=1, max_length=500)
    reason_code: Optional[str] = Field(default="CUSTOMER_RETURN", max_length=32)
    authorized_exception: bool = False
    exception_reason: Optional[str] = None
    evidence_urls: list[str] = Field(default_factory=list)


class ReturnRejectRequest(BaseModel):
    __module__ = "salesia.modules.inventory.presentation.router"
    reason: str = Field(min_length=3, max_length=255)
    criterion: Optional[str] = Field(default="POLICY_VIOLATION", max_length=64)


class ReturnCancelRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=255)


class ReturnAcceptRequest(BaseModel):
    __module__ = "salesia.modules.inventory.presentation.router"
    inspections: Optional[list[ReturnAcceptInspectionItem]] = None
    create_credit_note: bool = True
    credit_action: Literal["CREDIT_NOTE", "STORE_CREDIT", "REFUND"] = "CREDIT_NOTE"
    reason_code: Optional[str] = None


class ExchangeCreateRequest(BaseModel):
    branch_id: Optional[UUID] = None

    warehouse_id: Optional[UUID] = None

    replacement_items: list[StockLine] = Field(min_length=1, max_length=50)


class ReturnWithoutReceiptRequest(BaseModel):
    __module__ = "salesia.modules.inventory.presentation.router"
    customer_id: UUID
    warehouse_id: UUID
    reason: str = Field(min_length=3, max_length=255)
    items: list[ReturnLine] = Field(min_length=1, max_length=50)
    manual_valuation_total: Decimal = Field(gt=0, decimal_places=6)
    manager_approval_code: Optional[str] = None
