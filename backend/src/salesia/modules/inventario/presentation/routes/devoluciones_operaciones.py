from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.devoluciones_operaciones as service_devoluciones_operaciones
from salesia.modules.inventario.application.contracts.devoluciones_operaciones import (
    ExchangeCreateRequest,
    ReturnAcceptRequest,
    ReturnCancelRequest,
    ReturnCreateRequest,
    ReturnRejectRequest,
    ReturnWithoutReceiptRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/returns", status_code=201, operation_id="inventory_create_return")
def create_return(
    payload: ReturnCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
):

    return service_devoluciones_operaciones.create_return(payload=payload, current_user=current_user, db=db)


@router.post("/returns/{return_id}/accept", operation_id="inventory_accept_return")
def accept_return(
    return_id: UUID,
    payload: Optional[ReturnAcceptRequest] = None,
    current_user: AuthenticatedUser = Depends(require_permission("sales:cancel")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_devoluciones_operaciones.accept_return(
        return_id=return_id, payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.post("/returns/{return_id}/reject", operation_id="inventory_reject_return")
def reject_return(
    return_id: UUID,
    payload: ReturnRejectRequest,
    current_user: AuthenticatedUser = Depends(require_permission("sales:cancel")),
    db: Session = Depends(get_db),
):

    return service_devoluciones_operaciones.reject_return(
        return_id=return_id, payload=payload, current_user=current_user, db=db
    )


@router.post("/returns/{return_id}/cancel", operation_id="inventory_cancel_return")
def cancel_return(
    return_id: UUID,
    payload: ReturnCancelRequest,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
):

    return service_devoluciones_operaciones.cancel_return(
        return_id=return_id, payload=payload, current_user=current_user, db=db
    )


@router.post("/returns/{return_id}/exchange", operation_id="inventory_exchange_return")
def exchange_return(
    return_id: UUID,
    payload: ExchangeCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_devoluciones_operaciones.exchange_return(
        return_id=return_id, payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.post("/returns/without-receipt", status_code=201, operation_id="inventory_create_return_without_receipt")
def create_return_without_receipt(
    payload: ReturnWithoutReceiptRequest,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_devoluciones_operaciones.create_return_without_receipt(
        payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )
