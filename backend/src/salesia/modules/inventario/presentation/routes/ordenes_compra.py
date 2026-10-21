from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.ordenes_compra as service_ordenes_compra
from salesia.modules.inventario.application.contracts.comunes import (
    PurchaseOrderCreateRequest,
    PurchaseOrderUpdateRequest,
    PurchaseReturnCreateRequest,
    ThreeWayMatchResolveRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/purchase-orders", status_code=201)
def create_purchase_order(
    payload: PurchaseOrderCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("purchases:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_ordenes_compra.create_purchase_order(
        payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.get("/purchase-orders")
def list_purchase_orders(
    supplier_id: Optional[UUID] = Query(None),
    warehouse_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(require_permission("purchases:read")),
    db: Session = Depends(get_db),
):

    return service_ordenes_compra.list_purchase_orders(
        supplier_id=supplier_id,
        warehouse_id=warehouse_id,
        status=status,
        limit=limit,
        offset=offset,
        current_user=current_user,
        db=db,
    )


@router.get("/purchase-orders/{order_id}")
def get_purchase_order(
    order_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("purchases:read")),
    db: Session = Depends(get_db),
):

    return service_ordenes_compra.get_purchase_order(order_id=order_id, current_user=current_user, db=db)


@router.post("/purchase-orders/{order_id}/approve")
def approve_purchase_order(
    order_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("purchases:write")),
    db: Session = Depends(get_db),
):

    return service_ordenes_compra.approve_purchase_order(order_id=order_id, current_user=current_user, db=db)


@router.put("/purchase-orders/{order_id}")
def update_purchase_order(
    order_id: UUID,
    payload: PurchaseOrderUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("purchases:write")),
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_ordenes_compra.update_purchase_order(
        order_id=order_id, payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.get("/purchase-orders/{order_id}/process-timeline")
def get_purchase_order_timeline(
    order_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("purchases:read")),
    db: Session = Depends(get_db),
):

    return service_ordenes_compra.get_purchase_order_timeline(order_id=order_id, current_user=current_user, db=db)


@router.get("/purchase-orders/{order_id}/receiving-context")
def purchase_receiving_context(
    order_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("purchases:read")),
    db: Session = Depends(get_db),
):

    return service_ordenes_compra.purchase_receiving_context(order_id=order_id, current_user=current_user, db=db)


@router.post("/purchases/returns", status_code=201)
def create_purchase_return(
    payload: PurchaseReturnCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("purchases:write")),
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_ordenes_compra.create_purchase_return(
        payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.post("/purchase-orders/{order_id}/three-way-match/resolve")
def resolve_three_way_match(
    order_id: UUID,
    payload: ThreeWayMatchResolveRequest,
    current_user: AuthenticatedUser = Depends(require_permission("purchases:write")),
    db: Session = Depends(get_db),
):

    return service_ordenes_compra.resolve_three_way_match(
        order_id=order_id, payload=payload, current_user=current_user, db=db
    )


from salesia.modules.inventario.application import compras_saldos


@router.post("/purchase-orders/{order_id}/balance-action")
def purchase_balance_action(order_id: UUID, payload: compras_saldos.PurchaseBalanceAction, user: AuthenticatedUser = Depends(require_permission("purchases:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return compras_saldos.balance_action(db, user, order_id, payload, key)


@router.get("/purchase-orders/{order_id}/versions")
def list_purchase_revisions(order_id: UUID, user: AuthenticatedUser = Depends(require_permission("purchases:read")), db: Session = Depends(get_db)):
    return compras_saldos.revisions(db, user, order_id)
