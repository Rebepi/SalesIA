from fastapi import APIRouter, Depends

import salesia.modules.auditoria.application.privacidad_inventario_datos as service_privacidad_inventario_datos
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user

router = APIRouter(prefix="")


@router.get("/privacy/data-inventory")
def get_privacy_data_inventory(current_user: AuthenticatedUser = Depends(get_current_user)):
    return service_privacidad_inventario_datos.get_privacy_data_inventory(current_user=current_user)
