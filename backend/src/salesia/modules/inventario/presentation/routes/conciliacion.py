from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.inventario.application.conciliacion as service_conciliacion
from salesia.modules.inventario.application.contracts.conciliacion import ReconcileRepairRequest, ReconcileRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/inventory/reconcile")
def run_stock_reconciliation(
    payload: ReconcileRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:read")),
    db: Session = Depends(get_db),
):

    return service_conciliacion.run_stock_reconciliation(payload=payload, current_user=current_user, db=db)


@router.post("/inventory/reconcile/{reconciliation_id}/repair")
def repair_stock_reconciliation(
    reconciliation_id: UUID,
    payload: ReconcileRepairRequest,
    current_user: AuthenticatedUser = Depends(require_permission("inventory:write")),
    db: Session = Depends(get_db),
):

    return service_conciliacion.repair_stock_reconciliation(
        reconciliation_id=reconciliation_id, payload=payload, current_user=current_user, db=db
    )
