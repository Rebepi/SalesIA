from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.operacion_restauracion as service_operacion_restauracion
from salesia.modules.operaciones.application.contracts.operacion_restauracion import RestoreVerifyRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/operations/restore/verify")
def verify_restore_readiness(
    payload: RestoreVerifyRequest,
    current_user: AuthenticatedUser = Depends(require_permission("platform:manage")),
    db: Session = Depends(get_db),
):

    return service_operacion_restauracion.verify_restore_readiness(payload=payload, current_user=current_user, db=db)
