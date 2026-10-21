from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

import salesia.modules.finanzas.application.pagos as service_pagos
from salesia.modules.finanzas.application.contracts.pagos import (
    PaymentAllocationRequest,
    PaymentCreateRequest,
    PaymentDisputeRequest,
    PaymentReversalRequest,
    ProofOfTransferRequest,
    ProofOfTransferVerifyRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/payments", status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("payments:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_pagos.create_payment(
        payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.get("/payments")
def list_payments(
    search: Optional[str] = Query(None),
    refundable: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(require_permission("payments:read")),
    db: Session = Depends(get_db),
):

    return service_pagos.list_payments(
        search=search, refundable=refundable, limit=limit, offset=offset, current_user=current_user, db=db
    )


@router.get("/payments/{payment_id}")
def get_payment(
    payment_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("payments:read")),
    db: Session = Depends(get_db),
):

    return service_pagos.get_payment(payment_id=payment_id, current_user=current_user, db=db)


@router.post("/payments/{payment_id}/allocations")
def allocate_payment(
    payment_id: UUID,
    payload: PaymentAllocationRequest,
    current_user: AuthenticatedUser = Depends(require_permission("payments:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_pagos.allocate_payment(payment_id=payment_id, payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key)


@router.post("/payments/proof-of-transfer", status_code=status.HTTP_201_CREATED)
def submit_proof_of_transfer(
    payload: ProofOfTransferRequest,
    current_user: AuthenticatedUser = Depends(require_permission("payments:write")),
    db: Session = Depends(get_db),
):

    return service_pagos.submit_proof_of_transfer(payload=payload, current_user=current_user, db=db)


@router.post("/payments/{payment_id}/verify-proof")
def verify_proof_of_transfer(
    payment_id: UUID,
    payload: ProofOfTransferVerifyRequest,
    current_user: AuthenticatedUser = Depends(require_permission("payments:write")),
    db: Session = Depends(get_db),
):

    return service_pagos.verify_proof_of_transfer(
        payment_id=payment_id, payload=payload, current_user=current_user, db=db
    )


@router.post("/payments/{payment_id}/reversals", status_code=status.HTTP_201_CREATED)
def reverse_payment(
    payment_id: UUID,
    payload: PaymentReversalRequest,
    current_user: AuthenticatedUser = Depends(require_permission("payments:write")),
    db: Session = Depends(get_db),
):

    return service_pagos.reverse_payment(payment_id=payment_id, payload=payload, current_user=current_user, db=db)


@router.post("/payments/{payment_id}/disputes", status_code=status.HTTP_201_CREATED)
def create_payment_dispute(
    payment_id: UUID,
    payload: PaymentDisputeRequest,
    current_user: AuthenticatedUser = Depends(require_permission("payments:write")),
    db: Session = Depends(get_db),
):

    return service_pagos.create_payment_dispute(
        payment_id=payment_id, payload=payload, current_user=current_user, db=db
    )
