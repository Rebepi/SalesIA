from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.operacion_configuracion as service_operacion_configuracion
from salesia.modules.operaciones.application.contracts.operacion_configuracion import SettingRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/operations/settings")
def get_operation_settings(
    current_user: AuthenticatedUser = Depends(require_permission("operations:manage")), db: Session = Depends(get_db)
):

    return service_operacion_configuracion.get_operation_settings(current_user=current_user, db=db)


@router.put("/operations/settings")
def set_operation_setting(
    payload: SettingRequest,
    current_user: AuthenticatedUser = Depends(require_permission("operations:manage")),
    db: Session = Depends(get_db),
):

    return service_operacion_configuracion.set_operation_setting(payload=payload, current_user=current_user, db=db)
