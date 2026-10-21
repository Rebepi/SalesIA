from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

import salesia.modules.pedidos.application.pedidos_reservas_faltantes as service_pedidos_reservas_faltantes
from salesia.modules.pedidos.application.contracts.pedidos_reservas_faltantes import OrderShortageResolution
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/orders/{order_id}/release-reservation")
def release_order_reservation(
    order_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_pedidos_reservas_faltantes.release_order_reservation(
        order_id=order_id, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.post("/orders/{order_id}/renew-reservation")
def renew_order_reservation(
    order_id: UUID,
    extension_days: int = Query(default=7, ge=1, le=30),
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
):

    return service_pedidos_reservas_faltantes.renew_order_reservation(
        order_id=order_id, extension_days=extension_days, current_user=current_user, db=db
    )


@router.get("/orders/{order_id}/shortages")
def get_order_shortages(
    order_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("sales:read")),
    db: Session = Depends(get_db),
):

    return service_pedidos_reservas_faltantes.get_order_shortages(order_id=order_id, current_user=current_user, db=db)


@router.post("/orders/{order_id}/resolve-shortage")
def resolve_order_shortage(
    order_id: UUID,
    req: OrderShortageResolution,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
):

    return service_pedidos_reservas_faltantes.resolve_order_shortage(
        order_id=order_id, req=req, current_user=current_user, db=db
    )
