from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import salesia.modules.catalogo.application.productos_kits as service_productos_kits
from salesia.modules.catalogo.application.contracts.productos_kits import KitItemCreateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/products/{product_id}/kit-items", status_code=status.HTTP_201_CREATED)
def create_kit_item(
    product_id: UUID,
    req: KitItemCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_productos_kits.create_kit_item(product_id=product_id, req=req, current_user=current_user, db=db)
