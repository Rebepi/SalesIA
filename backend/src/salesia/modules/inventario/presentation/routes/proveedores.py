from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.proveedores as service_proveedores
from salesia.modules.inventario.application.contracts.proveedores import SupplierCreateRequest, SupplierUpdateRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/suppliers")
def list_suppliers(
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_proveedores.list_suppliers(
        search=search, is_active=is_active, limit=limit, offset=offset, current_user=current_user, db=db
    )


@router.post("/suppliers", status_code=201)
def create_supplier(
    payload: SupplierCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("purchases:write")),
    db: Session = Depends(get_db),
):

    return service_proveedores.create_supplier(payload=payload, current_user=current_user, db=db)


@router.get("/suppliers/{supplier_id}")
def get_supplier(
    supplier_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_proveedores.get_supplier(supplier_id=supplier_id, current_user=current_user, db=db)


@router.put("/suppliers/{supplier_id}")
def update_supplier(
    supplier_id: UUID,
    payload: SupplierUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("purchases:write")),
    db: Session = Depends(get_db),
):

    return service_proveedores.update_supplier(
        supplier_id=supplier_id, payload=payload, current_user=current_user, db=db
    )


@router.get("/suppliers/{supplier_id}/performance")
def get_supplier_performance(
    supplier_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("purchases:read")),
    db: Session = Depends(get_db),
):

    return service_proveedores.get_supplier_performance(supplier_id=supplier_id, current_user=current_user, db=db)


@router.get("/suppliers/{supplier_id}/price-history")
def supplier_price_history(
    supplier_id: UUID,
    product_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("purchases:read")),
    db: Session = Depends(get_db),
):

    return service_proveedores.supplier_price_history(
        supplier_id=supplier_id, product_id=product_id, current_user=current_user, db=db
    )
