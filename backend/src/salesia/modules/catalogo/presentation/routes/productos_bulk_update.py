from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.catalogo.application.productos_bulk_update as service_productos_bulk_update
from salesia.modules.catalogo.application.contracts.productos_bulk_update import BulkUpdateRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/products/bulk-update")
def bulk_update_products(
    req: BulkUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_productos_bulk_update.bulk_update_products(req=req, current_user=current_user, db=db)
