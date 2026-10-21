from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.operacion_degraded_mode as service_operacion_degraded_mode
from salesia.modules.operaciones.application.contracts.operacion_mantenimiento import OperationalModeRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/operations/degraded-mode/toggle")
def set_degraded_mode(
    payload: OperationalModeRequest,
    current_user: AuthenticatedUser = Depends(require_permission("operations:manage")),
    db: Session = Depends(get_db),
):

    return service_operacion_degraded_mode.set_degraded_mode(payload=payload, current_user=current_user, db=db)
