from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application.auxiliares.now import now
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import InventoryStockModel, SaleModel


def check_business_invariants(current_user: AuthenticatedUser, db: Session):
    negative = db.scalars(
        select(InventoryStockModel.id).where(
            InventoryStockModel.company_id == current_user.company_id,
            InventoryStockModel.physical_quantity < InventoryStockModel.reserved_quantity,
        )
    ).all()

    payments = db.scalars(
        select(SaleModel.id).where(
            SaleModel.company_id == current_user.company_id,
            (SaleModel.paid_amount > SaleModel.total_amount)
            | ((SaleModel.status == "paid") & (SaleModel.paid_amount != SaleModel.total_amount)),
        )
    ).all()

    count = len(negative) + len(payments)

    return {
        "healthy": count == 0,
        "status": "clean" if count == 0 else "violations",
        "invariants_checked": 3,
        "negative_stock_count": len(negative),
        "discrepant_sales_count": len(payments),
        "stock_violations": [str(value) for value in negative],
        "payment_violations": [str(value) for value in payments],
        "checked_at": now().isoformat(),
    }
