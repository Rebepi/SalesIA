from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.requisiciones_reposicion as service_requisiciones_reposicion
from salesia.modules.inventario.application.contracts.requisiciones_reposicion import PurchaseRequisitionCreateRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/purchases/requisitions", status_code=201)
def create_purchase_requisition(
    payload: PurchaseRequisitionCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("purchases:write")),
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_requisiciones_reposicion.create_purchase_requisition(
        payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.get("/purchases/requisitions")
def list_purchase_requisitions(
    current_user: AuthenticatedUser = Depends(require_permission("purchases:read")), db: Session = Depends(get_db)
):

    return service_requisiciones_reposicion.list_purchase_requisitions(current_user=current_user, db=db)


@router.post("/purchases/requisitions/{id}/approve")
def approve_purchase_requisition(
    id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("purchases:write")),
    db: Session = Depends(get_db),
):

    return service_requisiciones_reposicion.approve_purchase_requisition(id=id, current_user=current_user, db=db)


@router.post("/purchases/requisitions/suggest-from-stock")
def suggest_requisition_from_stock(
    warehouse_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("purchases:read")),
    db: Session = Depends(get_db),
):

    return service_requisiciones_reposicion.suggest_requisition_from_stock(
        warehouse_id=warehouse_id, current_user=current_user, db=db
    )


@router.get("/purchases/replenishment-suggestions")
def get_replenishment_suggestions(
    warehouse_id: Optional[UUID] = Query(None),
    current_user: AuthenticatedUser = Depends(require_permission("purchases:read")),
    db: Session = Depends(get_db),
):

    return service_requisiciones_reposicion.get_replenishment_suggestions(
        warehouse_id=warehouse_id, current_user=current_user, db=db
    )
