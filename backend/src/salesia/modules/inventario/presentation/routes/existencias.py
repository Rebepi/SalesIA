from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.existencias as service_existencias
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/inventory")
def list_inventory(
    warehouse_id: Optional[UUID] = None,
    product_id: Optional[UUID] = None,
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(require_permission("inventory:read")),
    db: Session = Depends(get_db),
):

    return service_existencias.list_inventory(
        warehouse_id=warehouse_id,
        product_id=product_id,
        search=search,
        limit=limit,
        offset=offset,
        current_user=current_user,
        db=db,
    )
