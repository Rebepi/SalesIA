from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Response
from sqlalchemy.orm import Session

import salesia.modules.pedidos.application.pedidos_registro as service_pedidos_registro
from salesia.modules.pedidos.application.contracts.pedidos_registro import (
    ConfirmOrderRequest,
    OrderCancelRequest,
    OrderCreateModel,
    PickingScanRequest,
    UpdateOrderLinesRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/orders")
def list_orders(
    response: Response,
    status_filter: Optional[str] = Query(None),
    customer_id: Optional[UUID] = Query(None),
    branch_id: Optional[UUID] = Query(None),
    sales_rep_id: Optional[UUID] = Query(None),
    active_only: bool = Query(False),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_pedidos_registro.list_orders(
        response=response,
        status_filter=status_filter,
        customer_id=customer_id,
        branch_id=branch_id,
        sales_rep_id=sales_rep_id,
        active_only=active_only,
        limit=limit,
        offset=offset,
        current_user=current_user,
        db=db,
    )


@router.get("/orders/{order_id}")
def get_order(
    order_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_pedidos_registro.get_order(order_id=order_id, current_user=current_user, db=db)


@router.post("/orders", status_code=201)
def create_order(
    req: OrderCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_pedidos_registro.create_order(
        req=req, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.post("/orders/{order_id}/approve")
def approve_order(
    order_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("organization:manage")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_pedidos_registro.approve_order(
        order_id=order_id, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.post("/orders/{order_id}/confirm")
def confirm_order(
    order_id: UUID,
    req: Optional[ConfirmOrderRequest] = None,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_pedidos_registro.confirm_order(
        order_id=order_id, req=req, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.put("/orders/{order_id}/lines")
def update_order_lines(
    order_id: UUID,
    req: UpdateOrderLinesRequest,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
):

    return service_pedidos_registro.update_order_lines(order_id=order_id, req=req, current_user=current_user, db=db)


@router.post("/orders/{order_id}/cancel")
def cancel_order(
    order_id: UUID,
    req: Optional[OrderCancelRequest] = None,
    current_user: AuthenticatedUser = Depends(require_permission("sales:cancel")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_pedidos_registro.cancel_order(
        order_id=order_id, req=req, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.get("/orders/{order_id}/tracking")
def get_order_tracking(
    order_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_pedidos_registro.get_order_tracking(order_id=order_id, current_user=current_user, db=db)


@router.post("/orders/{order_id}/clone", status_code=201)
def clone_order(
    order_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_pedidos_registro.clone_order(
        order_id=order_id, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.post("/orders/{order_id}/picking/scan")
def scan_order_picking(
    order_id: UUID,
    req: PickingScanRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write", "sales:write")),
    db: Session = Depends(get_db),
):

    return service_pedidos_registro.scan_order_picking(order_id=order_id, req=req, current_user=current_user, db=db)


@router.post("/orders/{order_id}/picking/complete")
def complete_order_picking(
    order_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write", "sales:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_pedidos_registro.complete_order_picking(
        order_id=order_id, current_user=current_user, db=db, idempotency_key=idempotency_key
    )
