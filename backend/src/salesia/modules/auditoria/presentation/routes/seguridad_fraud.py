from fastapi import APIRouter, Depends

import salesia.modules.auditoria.application.seguridad_fraud as service_seguridad_fraud
from salesia.modules.auditoria.application.contracts.seguridad_fraud import FraudCheckRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user

router = APIRouter(prefix="")


@router.post("/security/fraud/check-transaction")
def check_commercial_fraud(payload: FraudCheckRequest, current_user: AuthenticatedUser = Depends(get_current_user)):
    return service_seguridad_fraud.check_commercial_fraud(payload=payload, current_user=current_user)
