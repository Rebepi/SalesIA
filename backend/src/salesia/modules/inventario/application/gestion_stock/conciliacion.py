import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, select

from salesia.modules.inventario.application.gestion_stock.consulta import make_aware, product, warehouse
from salesia.modules.inventario.application.gestion_stock.movimientos import move_stock
from salesia.modules.inventario.infrastructure_models import (
    InventoryAlert,
    InventoryLot,
    InventoryReconciliation,
    StockRule,
)
from salesia.shared.infrastructure.models import InventoryStockModel, KardexMovementModel, WarehouseModel


def reconcile_stock(db, company_id, warehouse_id, product_id):
    warehouse(db, company_id, warehouse_id)
    product(db, company_id, product_id)
    stock = db.scalar(
        select(InventoryStockModel).where(
            InventoryStockModel.company_id == company_id,
            InventoryStockModel.warehouse_id == warehouse_id,
            InventoryStockModel.product_id == product_id,
        )
    )
    cached_qty = stock.physical_quantity if stock else Decimal("0")
    ledger_sum = db.scalar(
        select(func.coalesce(func.sum(KardexMovementModel.quantity_delta), Decimal("0"))).where(
            KardexMovementModel.company_id == company_id,
            KardexMovementModel.warehouse_id == warehouse_id,
            KardexMovementModel.product_id == product_id,
        )
    ) or Decimal("0")
    discrepancy = cached_qty - ledger_sum
    rec = InventoryReconciliation(
        id=uuid4(),
        company_id=company_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
        ledger_balance=ledger_sum,
        cached_stock_balance=cached_qty,
        discrepancy_delta=discrepancy,
        status="MATCH" if discrepancy == 0 else "DISCREPANCY",
        before_balance=cached_qty,
        after_balance=cached_qty,
    )
    db.add(rec)
    if discrepancy != 0:
        hash_val = hashlib.sha256(f"{company_id}:{warehouse_id}:{product_id}:DISCREPANCY".encode()).hexdigest()
        existing_alert = db.scalar(
            select(InventoryAlert).where(
                InventoryAlert.company_id == company_id,
                InventoryAlert.dedup_hash == hash_val,
                InventoryAlert.resolved_at.is_(None),
            )
        )
        if not existing_alert:
            db.add(
                InventoryAlert(
                    id=uuid4(),
                    company_id=company_id,
                    warehouse_id=warehouse_id,
                    product_id=product_id,
                    alert_type="DISCREPANCY",
                    severity="CRITICAL",
                    message=f"Discrepancia detectada: saldo stock {cached_qty} vs saldo kardex {ledger_sum}",
                    dedup_hash=hash_val,
                    computed_at=datetime.now(timezone.utc),
                )
            )
    db.flush()
    return rec


def repair_stock_discrepancy(db, user, reconciliation_id, reason, evidence):
    rec = db.scalar(
        select(InventoryReconciliation)
        .where(InventoryReconciliation.id == reconciliation_id, InventoryReconciliation.company_id == user.company_id)
        .with_for_update()
    )
    if not rec:
        raise HTTPException(404, "Registro de reconciliación no encontrado.")
    if rec.status == "REPAIRED":
        return rec
    if rec.discrepancy_delta == 0:
        rec.status = "MATCH"
        return rec
    stock = db.scalar(
        select(InventoryStockModel)
        .where(
            InventoryStockModel.company_id == user.company_id,
            InventoryStockModel.warehouse_id == rec.warehouse_id,
            InventoryStockModel.product_id == rec.product_id,
        )
        .with_for_update()
    )
    before = stock.physical_quantity if stock else Decimal("0")
    needed_adjustment = rec.ledger_balance - before
    move_stock(
        db,
        user.company_id,
        rec.warehouse_id,
        rec.product_id,
        needed_adjustment,
        Decimal("0"),
        rec.id,
        "RECONCILIACION_AJUSTE",
        allow_negative=False,
    )
    rec.status = "REPAIRED"
    rec.before_balance = before
    rec.after_balance = rec.ledger_balance
    rec.repair_reason = reason
    rec.evidence = evidence
    rec.repaired_by = user.user_id
    rec.repaired_at = datetime.now(timezone.utc)
    hash_val = hashlib.sha256(f"{user.company_id}:{rec.warehouse_id}:{rec.product_id}:DISCREPANCY".encode()).hexdigest()
    alert = db.scalar(
        select(InventoryAlert).where(
            InventoryAlert.company_id == user.company_id,
            InventoryAlert.dedup_hash == hash_val,
            InventoryAlert.resolved_at.is_(None),
        )
    )
    if alert:
        alert.resolved_at = datetime.now(timezone.utc)
    db.flush()
    return rec


def recalculate_alerts(db, company_id):
    rules = db.scalars(select(StockRule).where(StockRule.company_id == company_id, StockRule.is_active.is_(True))).all()
    now = datetime.now(timezone.utc)
    for rule in rules:
        stock = db.scalar(
            select(InventoryStockModel).where(
                InventoryStockModel.company_id == company_id,
                InventoryStockModel.warehouse_id == rule.warehouse_id,
                InventoryStockModel.product_id == rule.product_id,
            )
        )
        available = (stock.physical_quantity - stock.reserved_quantity) if stock else Decimal("0")
        hash_val = hashlib.sha256(f"{company_id}:{rule.warehouse_id}:{rule.product_id}:MIN_STOCK".encode()).hexdigest()
        existing = db.scalar(
            select(InventoryAlert)
            .where(InventoryAlert.company_id == company_id, InventoryAlert.dedup_hash == hash_val)
            .with_for_update()
        )
        if available < rule.min_quantity:
            if existing:
                existing.computed_at = now
                existing.resolved_at = None
            else:
                db.add(
                    InventoryAlert(
                        id=uuid4(),
                        company_id=company_id,
                        warehouse_id=rule.warehouse_id,
                        product_id=rule.product_id,
                        alert_type="MIN_STOCK",
                        severity="WARNING",
                        message=f"Stock disponible ({available}) inferior al mínimo ({rule.min_quantity})",
                        dedup_hash=hash_val,
                        computed_at=now,
                    )
                )
        else:
            if existing and existing.resolved_at is None:
                existing.resolved_at = now
    lots = db.scalars(
        select(InventoryLot).where(InventoryLot.company_id == company_id, InventoryLot.expiration_date.is_not(None))
    ).all()
    for lot in lots:
        if lot.expiration_date and make_aware(lot.expiration_date) <= now:
            hash_val = hashlib.sha256(f"{company_id}:{lot.product_id}:{lot.lot_code}:EXPIRATION".encode()).hexdigest()
            existing = db.scalar(
                select(InventoryAlert)
                .where(InventoryAlert.company_id == company_id, InventoryAlert.dedup_hash == hash_val)
                .with_for_update()
            )
            wh = db.scalar(
                select(WarehouseModel.id).where(
                    WarehouseModel.company_id == company_id, WarehouseModel.is_active.is_(True)
                )
            )
            if wh:
                if existing:
                    existing.computed_at = now
                else:
                    db.add(
                        InventoryAlert(
                            id=uuid4(),
                            company_id=company_id,
                            warehouse_id=wh,
                            product_id=lot.product_id,
                            alert_type="EXPIRATION",
                            severity="CRITICAL",
                            message=f"Lote {lot.lot_code} vencido en fecha {lot.expiration_date.isoformat()}",
                            dedup_hash=hash_val,
                            computed_at=now,
                        )
                    )
    db.flush()
    return db.scalars(
        select(InventoryAlert).where(InventoryAlert.company_id == company_id, InventoryAlert.resolved_at.is_(None))
    ).all()
