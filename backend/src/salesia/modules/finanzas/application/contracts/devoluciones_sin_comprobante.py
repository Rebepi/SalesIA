from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from salesia.modules.finanzas.application.contracts.comunes import ReturnItemRequest


class ReturnWithoutReceiptRequest(BaseModel):
    __module__ = "salesia.modules.finance.presentation.router"
    customer_id: UUID
    warehouse_id: UUID
    reason: str = Field(..., min_length=3, max_length=255)
    manual_valuation_total: Decimal = Field(..., gt=0)
    items: list[ReturnItemRequest] = Field(..., min_length=1)
