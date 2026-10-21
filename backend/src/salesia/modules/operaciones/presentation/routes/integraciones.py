from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.integraciones as service_integraciones
from salesia.modules.operaciones.application.contracts.integraciones import (
    IntegrationCreateRequest,
    IntegrationCredentialRequest,
    IntegrationModeRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/integrations")
def list_integrations(
    current_user: AuthenticatedUser = Depends(require_permission("operations:manage")), db: Session = Depends(get_db)
):

    return service_integraciones.list_integrations(current_user=current_user, db=db)


@router.post("/integrations", status_code=201)
def create_integration(
    payload: IntegrationCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("operations:manage")),
    db: Session = Depends(get_db),
):

    return service_integraciones.create_integration(payload=payload, current_user=current_user, db=db)


@router.patch("/integrations/{connection_id}/credential")
def rotate_integration_credential(
    connection_id: UUID,
    payload: IntegrationCredentialRequest,
    current_user: AuthenticatedUser = Depends(require_permission("operations:manage")),
    db: Session = Depends(get_db),
):

    return service_integraciones.rotate_integration_credential(
        connection_id=connection_id, payload=payload, current_user=current_user, db=db
    )


@router.patch("/integrations/{connection_id}/mode")
def update_integration_mode(
    connection_id: UUID,
    payload: IntegrationModeRequest,
    current_user: AuthenticatedUser = Depends(require_permission("operations:manage")),
    db: Session = Depends(get_db),
):

    return service_integraciones.update_integration_mode(
        connection_id=connection_id, payload=payload, current_user=current_user, db=db
    )


@router.post("/integrations/{connection_id}/diagnose")
def diagnose_integration(
    connection_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("operations:manage")),
    db: Session = Depends(get_db),
):

    return service_integraciones.diagnose_integration(connection_id=connection_id, current_user=current_user, db=db)
