from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import salesia.modules.catalogo.application.productos_consulta as service_productos_consulta
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/products")
def list_products(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    product_type: Optional[str] = Query(None),
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_productos_consulta.list_products(
        category=category,
        search=search,
        status_filter=status_filter,
        product_type=product_type,
        min_price=min_price,
        max_price=max_price,
        limit=limit,
        offset=offset,
        current_user=current_user,
        db=db,
    )


@router.get("/products/search-availability")
def search_products_with_availability(
    warehouse_id: UUID,
    search: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_productos_consulta.search_products_with_availability(
        warehouse_id=warehouse_id, search=search, limit=limit, offset=offset, current_user=current_user, db=db
    )


@router.get("/products/{product_id}")
def get_product(
    product_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_productos_consulta.get_product(product_id=product_id, current_user=current_user, db=db)
