from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from salesia.modules.finanzas.application.contracts.comunes import (
    ReturnExchangeItem,
    ReturnInspectionItem,
    ReturnItemRequest,
)


class ReturnCreateRequest(BaseModel):
    __module__ = "salesia.modules.finance.presentation.router"
    sale_id: UUID
    warehouse_id: UUID
    reason: str = Field(..., min_length=3, max_length=255)
    items: list[ReturnItemRequest] = Field(..., min_length=1, max_length=500)
    waive_retention: bool = False
    authorized_exception: bool = False
    exception_reason: Optional[str] = Field(default=None, max_length=255)
    evidence_urls: Optional[list[str]] = Field(default=None, max_length=50)


class ReturnAcceptRequest(BaseModel):
    __module__ = "salesia.modules.finance.presentation.router"
    create_credit_note: bool = False
    credit_action: Optional[Literal["CREDIT_NOTE", "STORE_CREDIT", "REFUND"]] = None
    inspections: Optional[list[ReturnInspectionItem]] = None


class ReturnRejectRequest(BaseModel):
    __module__ = "salesia.modules.finance.presentation.router"
    reason: str = Field(..., min_length=3, max_length=255)
    criterion: str = Field(..., min_length=1, max_length=64)


class ReturnCancelRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=255)


class ReturnExchangeRequest(BaseModel):
    warehouse_id: UUID

    replacement_items: list[ReturnExchangeItem] = Field(..., min_length=1)
