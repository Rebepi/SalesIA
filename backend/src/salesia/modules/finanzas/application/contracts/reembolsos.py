from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RefundCreateRequest(BaseModel):
    payment_id: UUID
    unapplied_only: bool = False
    return_id: Optional[UUID] = None
    cash_session_id: Optional[UUID] = None
    payout_reference: str = Field(min_length=3, max_length=128)

    reason: str = Field(..., min_length=3, max_length=255)

    amount: Optional[Decimal] = Field(default=None, gt=0, max_digits=20, decimal_places=6)


class RefundStatusUpdateRequest(BaseModel):
    status: Literal[
        "solicitado",
        "aprobado",
        "enviado",
        "pendiente",
        "confirmado",
        "fallido",
        "requiere_conciliacion",
        "requested",
        "approved",
        "sent",
        "pending",
        "confirmed",
        "failed",
        "requires_reconciliation",
        "cancelled",
    ]

    failure_reason: Optional[str] = None

    provider_reference: Optional[str] = None
