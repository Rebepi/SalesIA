from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.lotes_series as service_lotes_series
from salesia.modules.inventario.application.contracts.lotes_series import (
    LotCreateRequest,
    SerialCreateRequest,
    SerialSellRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/inventory/lots", status_code=201)
def create_lot(
    payload: LotCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
):

    return service_lotes_series.create_lot(payload=payload, current_user=current_user, db=db)


@router.get("/inventory/lots")
def list_lots(
    product_id: Optional[UUID] = None,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:read")),
    db: Session = Depends(get_db),
):

    return service_lotes_series.list_lots(product_id=product_id, current_user=current_user, db=db)


@router.get("/inventory/lots/{lot_id}/trace")
def lot_trace(
    lot_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:read")),
    db: Session = Depends(get_db),
):

    return service_lotes_series.lot_trace(lot_id=lot_id, current_user=current_user, db=db)


@router.get("/inventory/serials/{serial_id}/trace")
def serial_trace(
    serial_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:read")),
    db: Session = Depends(get_db),
):

    return service_lotes_series.serial_trace(serial_id=serial_id, current_user=current_user, db=db)


@router.post("/inventory/lots/{lot_id}/block")
def block_lot(
    lot_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
):

    return service_lotes_series.block_lot(lot_id=lot_id, current_user=current_user, db=db)


@router.post("/inventory/serials", status_code=201)
def create_serial(
    payload: SerialCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
):

    return service_lotes_series.create_serial(payload=payload, current_user=current_user, db=db)


@router.get("/inventory/serials")
def list_serials(
    product_id: Optional[UUID] = None,
    warehouse_id: Optional[UUID] = None,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:read")),
    db: Session = Depends(get_db),
):

    return service_lotes_series.list_serials(
        product_id=product_id, warehouse_id=warehouse_id, current_user=current_user, db=db
    )


@router.post("/inventory/serials/sell")
def sell_serial(
    payload: SerialSellRequest,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
):

    return service_lotes_series.sell_serial(payload=payload, current_user=current_user, db=db)
