from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LotCreateRequest(BaseModel):
    product_id: UUID

    lot_code: str = Field(min_length=1, max_length=64)

    supplier_id: Optional[UUID] = None

    manufacture_date: Optional[str] = None

    expiration_date: Optional[str] = None

    notes: Optional[str] = None


class SerialCreateRequest(BaseModel):
    product_id: UUID

    warehouse_id: UUID

    serial_number: str = Field(min_length=1, max_length=128)

    location_id: Optional[UUID] = None

    lot_id: Optional[UUID] = None


class SerialSellRequest(BaseModel):
    product_id: UUID

    serial_number: str

    sale_id: UUID
