from fastapi import APIRouter, Depends

import salesia.modules.auditoria.application.seguridad_outgoing_fetch as service_seguridad_outgoing_fetch
from salesia.modules.auditoria.application.contracts.seguridad_outgoing_fetch import OutgoingFetchRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user

router = APIRouter(prefix="")


@router.post("/security/outgoing-fetch")
def outgoing_fetch_safe(payload: OutgoingFetchRequest, current_user: AuthenticatedUser = Depends(get_current_user)):
    return service_seguridad_outgoing_fetch.outgoing_fetch_safe(payload=payload, current_user=current_user)
