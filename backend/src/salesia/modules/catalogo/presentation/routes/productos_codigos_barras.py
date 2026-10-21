from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import salesia.modules.catalogo.application.productos_codigos_barras as service_productos_codigos_barras
from salesia.modules.catalogo.application.contracts.productos_codigos_barras import BarcodeCreateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/products/{product_id}/barcodes", status_code=status.HTTP_201_CREATED)
def create_product_barcode(
    product_id: UUID,
    req: BarcodeCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("products:write")),
    db: Session = Depends(get_db),
):

    return service_productos_codigos_barras.create_product_barcode(
        product_id=product_id, req=req, current_user=current_user, db=db
    )
