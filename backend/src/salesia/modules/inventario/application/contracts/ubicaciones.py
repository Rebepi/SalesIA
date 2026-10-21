from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class LocationCreateRequest(BaseModel):
    warehouse_id: UUID

    code: str = Field(min_length=1, max_length=64)

    aisle: str = Field(default="A", max_length=32)

    rack: str = Field(default="1", max_length=32)

    shelf: str = Field(default="1", max_length=32)

    bin: str = Field(default="1", max_length=32)

    capacity_units: Decimal = Field(default=Decimal("1000.000000"), gt=0)


class LocationTransferRequest(BaseModel):
    warehouse_id: UUID

    product_id: UUID

    from_location_id: UUID

    to_location_id: UUID

    quantity: Decimal = Field(gt=0, decimal_places=6)


class LocationUpdateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=64)

    aisle: str = Field(max_length=32)

    rack: str = Field(max_length=32)

    shelf: str = Field(max_length=32)

    bin: str = Field(max_length=32)

    capacity_units: Decimal = Field(gt=0)

    is_active: bool = True
