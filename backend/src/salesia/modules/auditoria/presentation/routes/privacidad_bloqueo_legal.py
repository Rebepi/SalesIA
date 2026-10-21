from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.auditoria.application.privacidad_bloqueo_legal as service_privacidad_bloqueo_legal
from salesia.modules.auditoria.application.contracts.privacidad_bloqueo_legal import LegalHoldRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/privacy/legal-hold")
def manage_legal_hold(
    payload: LegalHoldRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service_privacidad_bloqueo_legal.manage_legal_hold(payload=payload, current_user=current_user, db=db)
