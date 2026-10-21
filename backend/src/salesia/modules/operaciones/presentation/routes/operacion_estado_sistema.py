from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.operacion_estado_sistema as service_operacion_estado_sistema
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/operations/system-status")
def get_system_operational_status(
    current_user: AuthenticatedUser = Depends(require_permission("operations:manage")), db: Session = Depends(get_db)
):

    return service_operacion_estado_sistema.get_system_operational_status(current_user=current_user, db=db)
