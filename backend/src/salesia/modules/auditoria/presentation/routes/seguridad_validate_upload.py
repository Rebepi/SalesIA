from fastapi import APIRouter, Depends

import salesia.modules.auditoria.application.seguridad_validate_upload as service_seguridad_validate_upload
from salesia.modules.auditoria.application.contracts.seguridad_validate_upload import FileUploadValidationRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user

router = APIRouter(prefix="")


@router.post("/security/validate-upload")
def validate_file_upload(
    payload: FileUploadValidationRequest, current_user: AuthenticatedUser = Depends(get_current_user)
):
    return service_seguridad_validate_upload.validate_file_upload(payload=payload, current_user=current_user)
