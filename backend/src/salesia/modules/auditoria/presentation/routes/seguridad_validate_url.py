from fastapi import APIRouter

import salesia.modules.auditoria.application.seguridad_validate_url as service_seguridad_validate_url
from salesia.modules.auditoria.application.contracts.seguridad_validate_url import UrlValidationRequest

router = APIRouter(prefix="")


@router.post("/security/validate-url")
def validate_url_for_ssrf(payload: UrlValidationRequest):
    return service_seguridad_validate_url.validate_url_for_ssrf(payload=payload)
