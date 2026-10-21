from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.preparacion as service_preparacion
from salesia.modules.inventario.application.contracts.preparacion import PickingCreateRequest, PickingVerifyRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/inventory/picking-lists", status_code=201)
def create_picking_list(
    payload: PickingCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
):

    return service_preparacion.create_picking_list(payload=payload, current_user=current_user, db=db)


@router.post("/inventory/picking-lists/{picking_id}/verify-item")
def verify_picking_item(
    picking_id: UUID,
    payload: PickingVerifyRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
):

    return service_preparacion.verify_picking_item(
        picking_id=picking_id, payload=payload, current_user=current_user, db=db
    )


@router.post("/inventory/picking-lists/{picking_id}/complete")
def complete_picking_list(
    picking_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
):

    return service_preparacion.complete_picking_list(picking_id=picking_id, current_user=current_user, db=db)
