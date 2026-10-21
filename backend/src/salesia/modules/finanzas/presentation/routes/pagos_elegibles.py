from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

import salesia.modules.finanzas.application.pagos_elegibles as service_pagos_elegibles
from salesia.modules.finanzas.application.contracts.pagos_elegibles import StoreCreditApplyRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/sales/{sale_id}/apply-store-credit")
def apply_store_credit(
    sale_id: UUID,
    payload: StoreCreditApplyRequest,
    current_user: AuthenticatedUser = Depends(require_permission("sales:write")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_pagos_elegibles.apply_store_credit(
        sale_id=sale_id, payload=payload, current_user=current_user, db=db, idempotency_key=idempotency_key
    )
