from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class OrderShortageResolution(BaseModel):
    action: str = Field(pattern="^(SUBSTITUTE|BACKORDER|PARTIAL_DELIVERY|CHANGE_WAREHOUSE|ESTIMATED_DATE)$")

    product_id: UUID

    substitute_product_id: Optional[UUID] = None

    warehouse_id: Optional[UUID] = None

    estimated_delivery_date: Optional[str] = None
