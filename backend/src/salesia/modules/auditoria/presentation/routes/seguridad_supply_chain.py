from fastapi import APIRouter, Depends

import salesia.modules.auditoria.application.seguridad_supply_chain as service_seguridad_supply_chain
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user

router = APIRouter(prefix="")


@router.get("/security/supply-chain/status")
def get_supply_chain_security_status(current_user: AuthenticatedUser = Depends(get_current_user)):
    return service_seguridad_supply_chain.get_supply_chain_security_status(current_user=current_user)
