from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field
from salesia.modules.finanzas.application.contracts.cuotas_cobranza import InstallmentTarget


class PaymentCreateRequest(BaseModel):
    installment_targets: list[InstallmentTarget] = Field(default_factory=list, max_length=120)
    schedule_version: Optional[int] = Field(default=None, ge=1)

    sale_id: UUID

    payment_method: str = Field(..., min_length=2, max_length=32)

    amount: Decimal = Field(..., gt=0)

    currency: str = Field(default="USD", min_length=3, max_length=3)

    reference_code: Optional[str] = None

    cash_tendered: Optional[Decimal] = Field(default=None, ge=0)

    cash_session_id: Optional[UUID] = None

    require_cash_session: bool = False

    is_advance: bool = False

    exchange_rate: Optional[Decimal] = Field(default=None, gt=0)


class PaymentAllocationRequest(BaseModel):
    reservation_id: Optional[UUID] = None
    installment_targets: list[InstallmentTarget] = Field(default_factory=list, max_length=120)
    schedule_version: Optional[int] = Field(default=None, ge=1)

    sale_id: UUID

    allocated_amount: Decimal = Field(..., gt=0, max_digits=20, decimal_places=6)


class ProofOfTransferRequest(BaseModel):
    sale_id: UUID

    amount: Decimal = Field(..., gt=0)

    currency: str = Field(default="USD", min_length=3, max_length=3)

    reference_code: str = Field(..., min_length=1, max_length=128)

    document_url: str = Field(..., min_length=3, max_length=255)


class ProofOfTransferVerifyRequest(BaseModel):
    approved: bool

    notes: Optional[str] = None


class PaymentReversalRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=255)

    reference_code: Optional[str] = None


class PaymentDisputeRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)

    reason: str = Field(..., min_length=3, max_length=255)

    evidence_url: Optional[str] = None

    deadline_at: Optional[datetime] = None
