from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.catalogo.application.productos_perfil as service_productos_perfil
from salesia.modules.catalogo.application.contracts.productos_perfil import ProductCommercialProfileUpdate
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/products/{product_id}/profile")
def get_product_commercial_profile(
    product_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_productos_perfil.get_product_commercial_profile(
        product_id=product_id, current_user=current_user, db=db
    )


@router.post("/products/{product_id}/profile")
def update_product_commercial_profile(
    product_id: UUID,
    req: ProductCommercialProfileUpdate,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_productos_perfil.update_product_commercial_profile(
        product_id=product_id, req=req, current_user=current_user, db=db
    )
