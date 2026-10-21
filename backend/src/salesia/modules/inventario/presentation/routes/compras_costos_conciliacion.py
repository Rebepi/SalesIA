from uuid import UUID

from typing import Optional
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.compras_costos_conciliacion as service_compras_costos_conciliacion
from salesia.modules.inventario.application.contracts.compras_costos_conciliacion import ThreeWayMatchRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/purchase-orders/{order_id}/three-way-match", status_code=201)
def process_three_way_match(
    order_id: UUID,
    payload: ThreeWayMatchRequest,
    current_user: AuthenticatedUser = Depends(require_permission("purchases:write")),
    db: Session = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_compras_costos_conciliacion.process_three_way_match(
        order_id=order_id, payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )


@router.get("/purchase-orders/{order_id}/invoice-context")
def purchase_invoice_context(order_id: UUID, user: AuthenticatedUser = Depends(require_permission("purchases:read")), db: Session = Depends(get_db)):
    return service_compras_costos_conciliacion.invoice_context(db, user, order_id)


@router.post("/purchase-invoice-matches/{match_id}/approve")
def approve_purchase_invoice_match(match_id: UUID, payload: service_compras_costos_conciliacion.MatchActionRequest, user: AuthenticatedUser = Depends(require_permission("purchases:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service_compras_costos_conciliacion.match_action(db, user, match_id, payload, "approve", key)


@router.post("/purchase-invoice-matches/{match_id}/void")
def void_purchase_invoice_match(match_id: UUID, payload: service_compras_costos_conciliacion.MatchActionRequest, user: AuthenticatedUser = Depends(require_permission("purchases:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service_compras_costos_conciliacion.match_action(db, user, match_id, payload, "void", key)
