from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import salesia.modules.catalogo.application.productos_importacion as service_productos_importacion
from salesia.modules.catalogo.application.contracts.productos_importacion import ImportBatchRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/products/import", status_code=status.HTTP_201_CREATED)
def import_products(
    req: ImportBatchRequest,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_productos_importacion.import_products(req=req, current_user=current_user, db=db)
