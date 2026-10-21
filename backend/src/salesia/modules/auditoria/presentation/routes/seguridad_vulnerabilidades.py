from fastapi import APIRouter, Depends

import salesia.modules.auditoria.application.seguridad_vulnerabilidades as service_seguridad_vulnerabilidades
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user

router = APIRouter(prefix="")


@router.get("/security/vulnerabilities/status")
def get_vulnerabilities_status(current_user: AuthenticatedUser = Depends(get_current_user)):
    return service_seguridad_vulnerabilidades.get_vulnerabilities_status(current_user=current_user)


@router.post("/security/vulnerabilities/verify-release")
def verify_vulnerability_release_gate(current_user: AuthenticatedUser = Depends(get_current_user)):
    return service_seguridad_vulnerabilidades.verify_vulnerability_release_gate(current_user=current_user)
