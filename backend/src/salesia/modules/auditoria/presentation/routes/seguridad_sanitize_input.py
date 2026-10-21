from fastapi import APIRouter

import salesia.modules.auditoria.application.seguridad_sanitize_input as service_seguridad_sanitize_input
from salesia.modules.auditoria.application.contracts.seguridad_sanitize_input import SanitizeInputRequest

router = APIRouter(prefix="")


@router.post("/security/sanitize-input")
def sanitize_input_text(payload: SanitizeInputRequest):
    return service_seguridad_sanitize_input.sanitize_input_text(payload=payload)
