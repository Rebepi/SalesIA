from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from salesia.modules.inventario.application import ventanas_entrega as service
from salesia.modules.inventario.service import document
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(tags=["Franjas de entrega y retiro"])


@router.get("/delivery-window-options")
def delivery_window_options(user: AuthenticatedUser = Depends(require_permission("inventory:read", "sales:read")), db: Session = Depends(get_db)):
    return service.options(db, user)


@router.get("/delivery-windows")
def delivery_windows(branch_id: UUID | None = None, mode: Literal["delivery", "pickup"] | None = None, on_date: date | None = None, limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0), user: AuthenticatedUser = Depends(require_permission("inventory:read", "sales:read")), db: Session = Depends(get_db)):
    return service.list_windows(db, user, branch_id, mode, on_date, limit, offset)


@router.post("/delivery-windows", status_code=201)
def create_delivery_window(payload: service.WindowRequest, user: AuthenticatedUser = Depends(require_permission("inventory:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.save_window(db, user, None, payload, key)


@router.put("/delivery-windows/{window_id}")
def update_delivery_window(window_id: UUID, payload: service.WindowRequest, user: AuthenticatedUser = Depends(require_permission("inventory:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.save_window(db, user, window_id, payload, key)


@router.get("/deliveries/{delivery_id}/window-reservation")
def delivery_window_reservation(delivery_id: UUID, user: AuthenticatedUser = Depends(require_permission("inventory:read", "sales:read")), db: Session = Depends(get_db)):
    document(db, user, "DELIVERY", delivery_id, lock=False)
    return service.reservation_data(db, user, service.reservation_for_delivery(db, user, delivery_id))


@router.post("/deliveries/{delivery_id}/window-reservation")
def reserve_delivery_window(delivery_id: UUID, payload: service.ReservationRequest, user: AuthenticatedUser = Depends(require_permission("inventory:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.reserve(db, user, delivery_id, payload, key)


@router.post("/deliveries/{delivery_id}/window-reservation/actions")
def act_on_delivery_window(delivery_id: UUID, payload: service.ReservationAction, user: AuthenticatedUser = Depends(require_permission("inventory:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.act_on_reservation(db, user, delivery_id, payload, key)
