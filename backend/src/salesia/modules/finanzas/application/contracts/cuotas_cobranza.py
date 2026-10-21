from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class InstallmentTarget(BaseModel):
    installment_id: UUID
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
