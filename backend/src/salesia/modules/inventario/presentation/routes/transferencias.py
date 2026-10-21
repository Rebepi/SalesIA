from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.transferencias as service_transferencias
from salesia.modules.inventario.application.contracts.transferencias import (
    TransferCreateRequest,
    TransferReceiveRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/inventory/transfers")
def list_transfers(
    warehouse_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(require_permission("inventory:read")),
    db: Session = Depends(get_db),
):

    return service_transferencias.list_transfers(
        warehouse_id=warehouse_id, status=status, limit=limit, offset=offset, current_user=current_user, db=db
    )


@router.post("/inventory/transfers", status_code=201)
def create_transfer(
    payload: TransferCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_transferencias.create_transfer(
        payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.post("/inventory/transfers/{transfer_id}/dispatch")
def dispatch_transfer(
    transfer_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_transferencias.dispatch_transfer(
        transfer_id=transfer_id, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.post("/inventory/transfers/{transfer_id}/receive")
def receive_transfer(
    transfer_id: UUID,
    payload: Optional[TransferReceiveRequest] = None,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_transferencias.receive_transfer(
        transfer_id=transfer_id, payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.post("/inventory/transfers/{transfer_id}/cancel")
def cancel_transfer(
    transfer_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_transferencias.cancel_transfer(
        transfer_id=transfer_id, current_user=current_user, db=db, idempotency_key=idempotency_key
    )
