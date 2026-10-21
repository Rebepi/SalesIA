from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import salesia.modules.catalogo.application.productos_variantes as service_productos_variantes
from salesia.modules.catalogo.application.contracts.productos_variantes import VariantCreateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/products/{product_id}/variants")
def list_product_variants(
    product_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_productos_variantes.list_product_variants(product_id=product_id, current_user=current_user, db=db)


@router.post("/products/{product_id}/variants", status_code=status.HTTP_201_CREATED)
def create_product_variant(
    product_id: UUID,
    req: VariantCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_productos_variantes.create_product_variant(
        product_id=product_id, req=req, current_user=current_user, db=db
    )
