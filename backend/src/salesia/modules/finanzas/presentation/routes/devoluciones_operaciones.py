from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

import salesia.modules.finanzas.application.devoluciones_operaciones as service_devoluciones_operaciones
from salesia.modules.finanzas.application.contracts.devoluciones_operaciones import (
    ReturnAcceptRequest,
    ReturnCancelRequest,
    ReturnCreateRequest,
    ReturnExchangeRequest,
    ReturnRejectRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/credit-notes/{credit_note_id}")
def get_credit_note(
    credit_note_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_devoluciones_operaciones.get_credit_note(
        credit_note_id=credit_note_id, current_user=current_user, db=db
    )


@router.get("/credit-notes")
def list_credit_notes(
    sale_id: Optional[UUID] = Query(None),
    customer_id: Optional[UUID] = Query(None),
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_devoluciones_operaciones.list_credit_notes(
        sale_id=sale_id, customer_id=customer_id, current_user=current_user, db=db
    )


@router.get("/returns/sales/{sale_id}/eligible", operation_id="finance_get_eligible_return_lines")
def get_eligible_return_lines(
    sale_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_devoluciones_operaciones.get_eligible_return_lines(sale_id=sale_id, current_user=current_user, db=db)


@router.post("/returns", status_code=status.HTTP_201_CREATED, operation_id="finance_create_return")
def create_return(
    payload: ReturnCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_devoluciones_operaciones.create_return(payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key)


@router.get("/returns", operation_id="finance_list_returns")
def list_returns(
    sale_id: Optional[UUID] = Query(None),
    customer_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_devoluciones_operaciones.list_returns(
        sale_id=sale_id, customer_id=customer_id, status_filter=status_filter, current_user=current_user, db=db
    )


@router.get("/returns/{return_id}", operation_id="finance_get_return")
def get_return(
    return_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_devoluciones_operaciones.get_return(return_id=return_id, current_user=current_user, db=db)


@router.post("/returns/{return_id}/reject", operation_id="finance_reject_return")
def reject_return(
    return_id: UUID,
    payload: ReturnRejectRequest,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
):

    return service_devoluciones_operaciones.reject_return(
        return_id=return_id, payload=payload, current_user=current_user, db=db
    )


@router.post("/returns/{return_id}/cancel", operation_id="finance_cancel_return")
def cancel_return(
    return_id: UUID,
    payload: ReturnCancelRequest,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
):

    return service_devoluciones_operaciones.cancel_return(
        return_id=return_id, payload=payload, current_user=current_user, db=db
    )


@router.post("/returns/{return_id}/accept", operation_id="finance_accept_return")
def accept_return(
    return_id: UUID,
    payload: ReturnAcceptRequest = ReturnAcceptRequest(),
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_devoluciones_operaciones.accept_return(
        return_id=return_id, payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.post("/returns/{return_id}/exchange", operation_id="finance_exchange_return")
def exchange_return(
    return_id: UUID,
    payload: ReturnExchangeRequest,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_devoluciones_operaciones.exchange_return(
        return_id=return_id, payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )
