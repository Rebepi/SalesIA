from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class FraudCheckRequest(BaseModel):
    customer_id: UUID
    amount: Decimal = Field(..., gt=0)
    actor_id: UUID
    approver_id: UUID
    recent_transactions: list[Decimal] = Field(default_factory=list)
    single_tx_limit: Decimal = Field(default=Decimal("5000.00"), gt=0)
    aggregate_limit: Decimal = Field(default=Decimal("10000.00"), gt=0)
