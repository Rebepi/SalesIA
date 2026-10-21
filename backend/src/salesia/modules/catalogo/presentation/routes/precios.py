from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.catalogo.application.precios as service_precios
from salesia.modules.catalogo.application.contracts.precios import PricePreviewRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/prices/preview")
@router.post("/products/price-preview")
def preview_price(
    req: PricePreviewRequest, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_precios.preview_price(req=req, current_user=current_user, db=db)
