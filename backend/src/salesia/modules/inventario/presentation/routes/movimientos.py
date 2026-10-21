from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.movimientos as service_movimientos
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/inventory/movements")
def list_movements(
    warehouse_id: Optional[UUID] = None,
    product_id: Optional[UUID] = None,
    movement_type: Optional[str] = None,
    cursor: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(require_permission("inventory:read")),
    db: Session = Depends(get_db),
):

    return service_movimientos.list_movements(
        warehouse_id=warehouse_id,
        product_id=product_id,
        movement_type=movement_type,
        cursor=cursor,
        limit=limit,
        offset=offset,
        current_user=current_user,
        db=db,
    )
