from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.reservas as service_reservas
from salesia.modules.inventario.application.contracts.reservas import (
    ReservationCreateRequest,
    ReservationReleaseRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/inventory/reservations", status_code=201)
def create_reservation_endpoint(
    payload: ReservationCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
):

    return service_reservas.create_reservation_endpoint(payload=payload, current_user=current_user, db=db)


@router.post("/inventory/reservations/release")
def release_reservation_endpoint(
    payload: ReservationReleaseRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
):

    return service_reservas.release_reservation_endpoint(payload=payload, current_user=current_user, db=db)
