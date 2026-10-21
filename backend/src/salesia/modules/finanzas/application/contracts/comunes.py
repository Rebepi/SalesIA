from decimal import Decimal
from uuid import UUID
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ReconciliationLine(BaseModel):
    reference_code: str

    amount: Decimal


class ReturnItemRequest(BaseModel):
    condition: Optional[Literal["unused", "used", "damaged", "not_applicable"]] = None
    packaging: Optional[Literal["sealed", "opened", "missing", "not_applicable"]] = None
    evidence_note: str = Field(default="", max_length=2000)

    product_id: UUID

    quantity: Decimal = Field(..., gt=0, max_digits=20, decimal_places=6)

    disposition: str = Field(default="RESTOCK")
    sale_line_id: Optional[UUID] = None
    serial_numbers: list[str] = Field(default_factory=list, max_length=10000)

    @field_validator("disposition")
    @classmethod
    def validate_disposition(cls, v):

        if v not in ("RESTOCK", "QUARANTINE", "DISPOSE"):
            raise ValueError("disposition must be RESTOCK, QUARANTINE or DISPOSE")

        return v


class ReturnInspectionItem(BaseModel):
    product_id: UUID

    disposition: str = Field(default="RESTOCK")
    sale_line_id: Optional[UUID] = None


class ReturnExchangeItem(BaseModel):
    product_id: UUID

    quantity: Decimal = Field(..., gt=0, max_digits=20, decimal_places=6)
