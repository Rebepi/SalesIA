from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class CashSessionCloseRequest(BaseModel):
    counted_balance: Decimal = Field(..., ge=0, max_digits=20, decimal_places=6)

    notes: Optional[str] = None


class BlindCountRequest(BaseModel):
    counted_cash: Decimal = Field(..., ge=0, max_digits=20, decimal_places=6)

    denominations: dict[str, int] = Field(default_factory=dict, max_length=50)

    non_cash_totals: dict[str, Decimal] = Field(default_factory=dict, max_length=20)


class ApproveDifferenceRequest(BaseModel):
    control_version: int = Field(..., ge=1)

    approved: bool

    notes: Optional[str] = None
