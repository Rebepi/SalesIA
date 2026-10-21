from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import salesia.modules.catalogo.application.productos_gestion as service_productos_gestion
from salesia.modules.catalogo.application.contracts.productos_gestion import (
    ProductCreateModel,
    ProductDuplicateModel,
    ProductUpdateModel,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(
    req: ProductCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_productos_gestion.create_product(req=req, current_user=current_user, db=db)


@router.patch("/products/{product_id}")
def update_product(
    product_id: UUID,
    req: ProductUpdateModel,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_productos_gestion.update_product(product_id=product_id, req=req, current_user=current_user, db=db)


@router.post("/products/{product_id}/archive")
def archive_product(
    product_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_productos_gestion.archive_product(product_id=product_id, current_user=current_user, db=db)


@router.post("/products/{product_id}/restore")
def restore_product(
    product_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_productos_gestion.restore_product(product_id=product_id, current_user=current_user, db=db)


@router.post("/products/{product_id}/duplicate", status_code=status.HTTP_201_CREATED)
def duplicate_product(
    product_id: UUID,
    req: ProductDuplicateModel,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_productos_gestion.duplicate_product(product_id=product_id, req=req, current_user=current_user, db=db)
