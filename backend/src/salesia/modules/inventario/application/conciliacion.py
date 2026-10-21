from uuid import UUID

from sqlalchemy.orm import Session

from salesia.modules.inventario.application.contracts.conciliacion import ReconcileRepairRequest, ReconcileRequest
from salesia.modules.inventario.service import reconcile_stock, repair_stock_discrepancy
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def run_stock_reconciliation(payload: ReconcileRequest, current_user: AuthenticatedUser, db: Session):
    rec = reconcile_stock(db, current_user.company_id, payload.warehouse_id, payload.product_id)

    db.commit()

    return {
        "id": str(rec.id),
        "warehouse_id": str(rec.warehouse_id),
        "product_id": str(rec.product_id),
        "ledger_balance": str(rec.ledger_balance),
        "cached_stock_balance": str(rec.cached_stock_balance),
        "discrepancy_delta": str(rec.discrepancy_delta),
        "status": rec.status,
    }


def repair_stock_reconciliation(
    reconciliation_id: UUID, payload: ReconcileRepairRequest, current_user: AuthenticatedUser, db: Session
):
    rec = repair_stock_discrepancy(db, current_user, reconciliation_id, payload.reason, payload.evidence)

    db.commit()

    return {
        "id": str(rec.id),
        "status": rec.status,
        "before_balance": str(rec.before_balance),
        "after_balance": str(rec.after_balance),
        "repair_reason": rec.repair_reason,
        "evidence": rec.evidence,
    }
