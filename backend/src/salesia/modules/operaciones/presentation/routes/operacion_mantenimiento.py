from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.operacion_mantenimiento as service_operacion_mantenimiento
from salesia.modules.operaciones.application.contracts.operacion_mantenimiento import OperationalModeRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/operations/maintenance/set")
def set_maintenance(
    payload: OperationalModeRequest,
    current_user: AuthenticatedUser = Depends(require_permission("operations:manage")),
    db: Session = Depends(get_db),
):

    return service_operacion_mantenimiento.set_maintenance(payload=payload, current_user=current_user, db=db)
