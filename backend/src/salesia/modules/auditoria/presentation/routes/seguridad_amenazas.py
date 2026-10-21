from fastapi import APIRouter, Depends

import salesia.modules.auditoria.application.seguridad_amenazas as service_seguridad_amenazas
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user

router = APIRouter(prefix="")


@router.get("/security/threat-model")
def get_threat_model(current_user: AuthenticatedUser = Depends(get_current_user)):
    return service_seguridad_amenazas.get_threat_model(current_user=current_user)
