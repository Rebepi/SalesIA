from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PickingCreateRequest(BaseModel):
    warehouse_id: UUID

    sale_id: UUID


class PickingVerifyRequest(BaseModel):
    product_id: UUID

    scanned_code: str

    quantity: Decimal = Field(gt=0, decimal_places=6)
