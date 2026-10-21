from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import salesia.modules.catalogo.application.productos_busqueda as service_productos_busqueda
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/products/lookup/barcode")
def lookup_product_by_barcode(
    code: str = Query(..., min_length=1),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_productos_busqueda.lookup_product_by_barcode(code=code, current_user=current_user, db=db)
