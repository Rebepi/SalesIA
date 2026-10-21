from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.cuarentena as service_cuarentena
from salesia.modules.inventario.application.contracts.cuarentena import QuarantineClassifyRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/inventory/quarantine")
def list_quarantine_items(
    current_user: AuthenticatedUser = Depends(require_permission("inventory:read")), db: Session = Depends(get_db)
):

    return service_cuarentena.list_quarantine_items(current_user=current_user, db=db)


@router.post("/inventory/quarantine/{quarantine_id}/classify")
def classify_quarantine_item(
    quarantine_id: UUID,
    payload: QuarantineClassifyRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
):

    return service_cuarentena.classify_quarantine_item(
        quarantine_id=quarantine_id, payload=payload, current_user=current_user, db=db
    )
