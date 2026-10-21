from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CashSessionOpenRequest(BaseModel):
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")

    branch_id: UUID

    terminal_code: str = Field(..., min_length=2, max_length=32)

    opening_balance: Decimal = Field(..., ge=0, max_digits=20, decimal_places=6)


class CashSessionMovementRequest(BaseModel):
    movement_type: str = Field(..., pattern="^(DEPOSIT|WITHDRAWAL)$")

    amount: Decimal = Field(..., gt=0, max_digits=20, decimal_places=6)

    reason: str = Field(..., min_length=3, max_length=255)
