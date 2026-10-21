from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CancelItemRequest(BaseModel):
    product_id: UUID

    quantity: Decimal = Field(gt=0)


class FulfilledItem(BaseModel):
    order_line_number: int | None = Field(default=None, ge=1)

    product_id: UUID

    quantity: Decimal = Field(gt=0)
    serial_numbers: list[str] = Field(default_factory=list, max_length=10000)
