from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from salesia.modules.inventario.application.contracts.comunes import StockLine


class PurchaseRequisitionCreateRequest(BaseModel):
    warehouse_id: UUID

    items: list[StockLine] = Field(min_length=1, max_length=500)

    priority: Literal["LOW", "MEDIUM", "HIGH", "URGENT"] = "MEDIUM"

    justification: str = Field(min_length=3, max_length=500)

    suggested_supplier_id: Optional[UUID] = None
