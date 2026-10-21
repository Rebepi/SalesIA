from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ReservationCreateRequest(BaseModel):
    warehouse_id: UUID

    product_id: UUID

    quantity: Decimal = Field(gt=0, decimal_places=6)

    document_type: str = Field(min_length=1, max_length=32)

    document_id: UUID

    allow_backorder: bool = False


class ReservationReleaseRequest(BaseModel):
    document_type: str = Field(min_length=1, max_length=32)

    document_id: UUID

    product_id: Optional[UUID] = None
