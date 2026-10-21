from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.entregas_operaciones as service_entregas_operaciones
from salesia.modules.inventario.application.contracts.entregas_operaciones import (
    DeliveryCompleteRequest,
    DeliveryCreateRequest,
    DeliveryInterceptRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/deliveries", status_code=201)
def create_delivery(
    payload: DeliveryCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):

    return service_entregas_operaciones.create_delivery(
        payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.get("/deliveries")
def list_deliveries(
    status: Optional[str] = Query(None),
    warehouse_id: Optional[UUID] = Query(None),
    carrier: Optional[str] = Query(None),
    delayed_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_entregas_operaciones.list_deliveries(
        status=status,
        warehouse_id=warehouse_id,
        carrier=carrier,
        delayed_only=delayed_only,
        limit=limit,
        offset=offset,
        current_user=current_user,
        db=db,
    )


@router.get("/deliveries/{delivery_id}")
def get_delivery(
    delivery_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_entregas_operaciones.get_delivery(delivery_id=delivery_id, current_user=current_user, db=db)


@router.post("/deliveries/{delivery_id}/dispatch")
def dispatch_delivery(
    delivery_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):

    return service_entregas_operaciones.dispatch_delivery(
        delivery_id=delivery_id, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.post("/deliveries/{delivery_id}/cancel")
def cancel_delivery(
    delivery_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
):

    return service_entregas_operaciones.cancel_delivery(delivery_id=delivery_id, current_user=current_user, db=db)


@router.post("/deliveries/{delivery_id}/intercept")
def intercept_delivery(
    delivery_id: UUID,
    payload: DeliveryInterceptRequest,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
):

    return service_entregas_operaciones.intercept_delivery(
        delivery_id=delivery_id, payload=payload, current_user=current_user, db=db
    )


@router.post("/deliveries/{delivery_id}/deliver")
def complete_delivery(
    delivery_id: UUID,
    payload: DeliveryCompleteRequest,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
):

    return service_entregas_operaciones.complete_delivery(
        delivery_id=delivery_id, payload=payload, current_user=current_user, db=db
    )
