from fastapi import APIRouter, Depends

import salesia.modules.auditoria.application.privacidad_mask_data as service_privacidad_mask_data
from salesia.modules.auditoria.application.contracts.privacidad_mask_data import MaskDataRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user

router = APIRouter(prefix="")


@router.post("/privacy/mask-data")
def mask_personal_data(payload: MaskDataRequest, current_user: AuthenticatedUser = Depends(get_current_user)):
    return service_privacidad_mask_data.mask_personal_data(payload=payload, current_user=current_user)
