from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import salesia.modules.finanzas.application.conciliaciones as service_conciliaciones
from salesia.modules.finanzas.application.contracts.conciliaciones import (
    ReconciliationCreateRequest,
    ReconciliationResolveRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/finance/reconciliations", status_code=status.HTTP_201_CREATED)
def create_reconciliation(
    payload: ReconciliationCreateRequest,
    current_user: AuthenticatedUser = Depends(require_permission("payments:write")),
    db: Session = Depends(get_db),
):

    return service_conciliaciones.create_reconciliation(payload=payload, current_user=current_user, db=db)


@router.get("/finance/reconciliations/{reconciliation_id}")
def get_reconciliation(
    reconciliation_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("payments:read")),
    db: Session = Depends(get_db),
):

    return service_conciliaciones.get_reconciliation(
        reconciliation_id=reconciliation_id, current_user=current_user, db=db
    )


@router.post("/finance/reconciliations/{reconciliation_id}/items/{item_id}/resolve")
def resolve_reconciliation_item(
    reconciliation_id: UUID,
    item_id: UUID,
    payload: ReconciliationResolveRequest,
    current_user: AuthenticatedUser = Depends(require_permission("payments:write")),
    db: Session = Depends(get_db),
):

    return service_conciliaciones.resolve_reconciliation_item(
        reconciliation_id=reconciliation_id, item_id=item_id, payload=payload, current_user=current_user, db=db
    )
