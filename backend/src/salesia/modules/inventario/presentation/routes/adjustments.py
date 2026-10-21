from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.adjustments as service_adjustments
from salesia.modules.inventario.application.contracts.adjustments import AdjustmentRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/inventory/adjustments", status_code=201)
def create_adjustment(
    payload: AdjustmentRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_adjustments.create_adjustment(
        payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )
