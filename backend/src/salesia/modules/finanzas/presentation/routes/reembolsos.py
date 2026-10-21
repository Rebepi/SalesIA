from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

import salesia.modules.finanzas.application.reembolsos as service_reembolsos
from salesia.modules.finanzas.application.contracts.reembolsos import RefundCreateRequest, RefundStatusUpdateRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/refunds", status_code=status.HTTP_201_CREATED)
def create_refund(
    payload: RefundCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("payments:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_reembolsos.create_refund(
        payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.post("/refunds/{refund_id}/status")
def update_refund_status(
    refund_id: UUID,
    payload: RefundStatusUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("payments:write")),
    db: Session = Depends(get_db),
):

    return service_reembolsos.update_refund_status(
        refund_id=refund_id, payload=payload, current_user=current_user, db=db
    )


@router.get("/refunds")
def list_refunds(
    status: Optional[str] = Query(None),
    payment_id: Optional[UUID] = Query(None),
    search: str | None = Query(None, max_length=128),
    currency: str | None = Query(None, pattern="^[A-Z]{3}$"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    linked_return: bool | None = Query(None),
    current_user: AuthenticatedUser = Depends(require_permission("payments:read")),
    db: Session = Depends(get_db),
):
    return service_reembolsos.list_refunds(status=status, payment_id=payment_id, current_user=current_user, db=db, search=search, currency=currency, date_from=date_from, date_to=date_to, linked_return=linked_return)


@router.get("/refunds/{refund_id}")
def get_refund(
    refund_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("payments:read")),
    db: Session = Depends(get_db),
):

    return service_reembolsos.get_refund(refund_id=refund_id, current_user=current_user, db=db)
