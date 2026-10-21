from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.inventario.application.contracts.reglas import StockRuleRequest
from salesia.modules.inventario.infrastructure_models import StockRule
from salesia.modules.inventario.service import record_audit
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import ProductModel, WarehouseModel


def configure_stock_rule(payload: StockRuleRequest, current_user: AuthenticatedUser, db: Session):
    wh = db.scalar(
        select(WarehouseModel).where(
            WarehouseModel.id == payload.warehouse_id, WarehouseModel.company_id == current_user.company_id
        )
    )

    if not wh:
        raise HTTPException(422, "Almacén no encontrado.")

    prod = db.scalar(
        select(ProductModel).where(
            ProductModel.id == payload.product_id, ProductModel.company_id == current_user.company_id
        )
    )

    if not prod:
        raise HTTPException(422, "Producto no encontrado.")

    rule = db.scalar(
        select(StockRule).where(
            StockRule.company_id == current_user.company_id,
            StockRule.warehouse_id == payload.warehouse_id,
            StockRule.product_id == payload.product_id,
        )
    )

    if not rule:
        rule = StockRule(
            id=uuid4(),
            company_id=current_user.company_id,
            warehouse_id=payload.warehouse_id,
            product_id=payload.product_id,
            min_quantity=payload.min_quantity,
            max_quantity=payload.max_quantity,
            reorder_point=payload.reorder_point,
            reorder_quantity=payload.reorder_quantity,
        )

        db.add(rule)

    else:
        rule.min_quantity = payload.min_quantity

        rule.max_quantity = payload.max_quantity

        rule.reorder_point = payload.reorder_point

        rule.reorder_quantity = payload.reorder_quantity

    rule.is_active = True

    db.commit()

    return {"id": str(rule.id), "min_quantity": str(rule.min_quantity), "max_quantity": str(rule.max_quantity)}


def list_stock_rules(current_user: AuthenticatedUser, db: Session):
    rows = db.scalars(select(StockRule).where(StockRule.company_id == current_user.company_id)).all()

    return {
        "items": [
            {
                "id": str(r.id),
                "warehouse_id": str(r.warehouse_id),
                "product_id": str(r.product_id),
                "min_quantity": str(r.min_quantity),
                "max_quantity": str(r.max_quantity),
                "reorder_point": str(r.reorder_point),
                "reorder_quantity": str(r.reorder_quantity),
                "is_active": r.is_active,
            }
            for r in rows
        ]
    }


def deactivate_stock_rule(rule_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(StockRule)
        .where(StockRule.id == rule_id, StockRule.company_id == current_user.company_id)
        .with_for_update()
    )

    if not row:
        raise HTTPException(404, "Regla no encontrada.")

    row.is_active = False

    record_audit(db, current_user, row.id, "DEACTIVATE_STOCK_RULE", {})

    db.commit()

    return {"id": str(row.id), "is_active": False}
