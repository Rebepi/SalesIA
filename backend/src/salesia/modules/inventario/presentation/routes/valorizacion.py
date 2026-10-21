from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.valorizacion as service_valorizacion
from salesia.modules.inventario.application.contracts.valorizacion import ValuationRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/inventory/valuation")
def get_valuation_setting(
    current_user: AuthenticatedUser = Depends(require_permission("inventory:read")), db: Session = Depends(get_db)
):

    return service_valorizacion.get_valuation_setting(current_user=current_user, db=db)


@router.post("/inventory/valuation")
def set_valuation_setting(
    payload: ValuationRequest,
    current_user: AuthenticatedUser = Depends(require_permission("organization:manage")),
    db: Session = Depends(get_db),
):

    return service_valorizacion.set_valuation_setting(payload=payload, current_user=current_user, db=db)
