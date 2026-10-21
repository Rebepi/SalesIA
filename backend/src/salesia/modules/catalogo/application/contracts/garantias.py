from typing import Optional
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class WarrantyClaimCreateModel(BaseModel):
    sale_id: UUID

    product_id: UUID

    serial_number: Optional[str] = None

    issue_description: str = Field(..., min_length=5, max_length=4000)
    sale_line_id: Optional[UUID] = None
    quantity: Decimal = Field(default=Decimal("1"), gt=0, max_digits=20, decimal_places=6)


class WarrantyActionRequest(BaseModel):
    version: int = Field(ge=1)
    action: Literal["assign", "diagnose", "await_parts", "repair", "ready", "deliver", "reject", "cancel"]
    notes: str = Field(min_length=3, max_length=4000)
    assigned_to: Optional[UUID] = None
