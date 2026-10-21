from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.inventario.infrastructure_models import InventoryAlert, StockRule
from salesia.modules.inventario.service import recalculate_alerts
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import InventoryStockModel


def list_alerts(current_user: AuthenticatedUser, db: Session):
    rows = db.scalars(
        select(InventoryAlert)
        .where(InventoryAlert.company_id == current_user.company_id, InventoryAlert.resolved_at.is_(None))
        .order_by(InventoryAlert.computed_at.desc())
    ).all()

    return {
        "items": [
            {
                "id": str(r.id),
                "warehouse_id": str(r.warehouse_id),
                "product_id": str(r.product_id) if r.product_id else None,
                "alert_type": r.alert_type,
                "severity": r.severity,
                "message": r.message,
                "computed_at": r.computed_at.isoformat(),
            }
            for r in rows
        ]
    }


def trigger_alert_recalculation(current_user: AuthenticatedUser, db: Session):
    alerts = recalculate_alerts(db, current_user.company_id)

    db.commit()

    return {
        "active_alerts_count": len(alerts),
        "items": [{"id": str(a.id), "alert_type": a.alert_type, "message": a.message} for a in alerts],
    }


def resolve_alert_endpoint(alert_id: UUID, current_user: AuthenticatedUser, db: Session):
    alert = db.scalar(
        select(InventoryAlert).where(
            InventoryAlert.id == alert_id, InventoryAlert.company_id == current_user.company_id
        )
    )

    if not alert:
        raise HTTPException(404, "Alerta no encontrada.")

    if alert.alert_type == "MIN_STOCK":
        rule = db.scalar(
            select(StockRule).where(
                StockRule.company_id == current_user.company_id,
                StockRule.warehouse_id == alert.warehouse_id,
                StockRule.product_id == alert.product_id,
            )
        )

        stock = db.scalar(
            select(InventoryStockModel).where(
                InventoryStockModel.company_id == current_user.company_id,
                InventoryStockModel.warehouse_id == alert.warehouse_id,
                InventoryStockModel.product_id == alert.product_id,
            )
        )

        avail = (stock.physical_quantity - stock.reserved_quantity) if stock else Decimal("0")

        min_q = rule.min_quantity if rule else Decimal("0")

        if avail < min_q:
            raise HTTPException(422, "Resolver una alerta exige cambio real de disponibilidad o regla.")

    alert.resolved_at = datetime.now(timezone.utc)

    db.commit()

    return {"id": str(alert.id), "status": "resolved"}
