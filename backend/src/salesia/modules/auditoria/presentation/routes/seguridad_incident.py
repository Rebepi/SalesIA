from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.auditoria.application.seguridad_incident as service_seguridad_incident
from salesia.modules.auditoria.application.contracts.seguridad_incident import UserQuarantineRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/security/incident/quarantine-user")
def quarantine_compromised_user(
    payload: UserQuarantineRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service_seguridad_incident.quarantine_compromised_user(payload=payload, current_user=current_user, db=db)
