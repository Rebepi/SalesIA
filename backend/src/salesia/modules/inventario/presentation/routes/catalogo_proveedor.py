from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from salesia.modules.inventario.application import catalogo_proveedor as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(tags=["Catálogo de proveedores"])


@router.get("/supplier-products")
def list_supplier_products(supplier_id: Optional[UUID] = None, product_id: Optional[UUID] = None, currency: Optional[str] = Query(None, pattern="^[A-Z]{3}$"), current_only: bool = False, limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0), user: AuthenticatedUser = Depends(require_permission("purchases:read")), db: Session = Depends(get_db)):
    return service.list_catalog(db, user, supplier_id, product_id, currency, current_only, limit, offset)


@router.put("/supplier-products")
def save_supplier_product(payload: service.SupplierProductRequest, user: AuthenticatedUser = Depends(require_permission("purchases:write")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.save_catalog(db, user, payload, key)
