from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.ubicaciones as service_ubicaciones
from salesia.modules.inventario.application.contracts.ubicaciones import (
    LocationCreateRequest,
    LocationTransferRequest,
    LocationUpdateRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/inventory/locations", status_code=201)
def create_location(
    payload: LocationCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
):

    return service_ubicaciones.create_location(payload=payload, current_user=current_user, db=db)


@router.get("/inventory/locations")
def list_locations(
    warehouse_id: Optional[UUID] = None,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:read")),
    db: Session = Depends(get_db),
):

    return service_ubicaciones.list_locations(warehouse_id=warehouse_id, current_user=current_user, db=db)


@router.put("/inventory/locations/{location_id}")
def update_location(
    location_id: UUID,
    payload: LocationUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
):

    return service_ubicaciones.update_location(
        location_id=location_id, payload=payload, current_user=current_user, db=db
    )


@router.post("/inventory/locations/transfer")
def transfer_location_stock(
    payload: LocationTransferRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
):

    return service_ubicaciones.transfer_location_stock(payload=payload, current_user=current_user, db=db)
