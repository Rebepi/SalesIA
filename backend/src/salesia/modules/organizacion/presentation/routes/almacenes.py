from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import salesia.modules.organizacion.application.almacenes as service_almacenes
from salesia.modules.organizacion.application.contracts.almacenes import WarehouseCreateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/warehouses")
def list_warehouses(
    branch_id: Optional[UUID] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service_almacenes.list_warehouses(branch_id=branch_id, is_active=is_active, current_user=current_user, db=db)


@router.post("/warehouses", status_code=201)
def create_warehouse(
    req: WarehouseCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("organization:manage")),
    db: Session = Depends(get_db),
):
    return service_almacenes.create_warehouse(req=req, current_user=current_user, db=db)
