from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

import salesia.modules.pedidos.application.pedidos_despacho as service_pedidos_despacho
from salesia.modules.pedidos.application.contracts.pedidos_despacho import OrderFulfillPartialModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/orders/{order_id}/fulfill-partial")
def fulfill_partial_order(
    order_id: UUID,
    req: OrderFulfillPartialModel,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_pedidos_despacho.fulfill_partial_order(
        order_id=order_id, req=req, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.post("/orders/{order_id}/picking", status_code=201)
def create_order_picking(
    order_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write", "sales:write")),
    db: Session = Depends(get_db),
):

    return service_pedidos_despacho.create_order_picking(order_id=order_id, current_user=current_user, db=db)
