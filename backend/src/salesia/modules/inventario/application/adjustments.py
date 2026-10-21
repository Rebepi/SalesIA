from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.inventario.application.contracts.adjustments import AdjustmentRequest
from salesia.modules.inventario.service import move_stock, record_audit
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import ProductModel, WarehouseModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def create_adjustment(payload: AdjustmentRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: str):
    record, cached = claim_request(
        db, current_user.company_id, "inventory.adjust", idempotency_key, payload.model_dump(mode="json")
    )

    if cached is not None:
        return cached

    wh = db.scalar(
        select(WarehouseModel).where(
            WarehouseModel.id == payload.warehouse_id, WarehouseModel.company_id == current_user.company_id
        )
    )

    if not wh:
        raise HTTPException(422, "Almacén inexistente o de otra empresa.")

    prod = db.scalar(
        select(ProductModel).where(
            ProductModel.id == payload.product_id, ProductModel.company_id == current_user.company_id
        )
    )

    if not prod:
        raise HTTPException(422, "Producto inexistente o de otra empresa.")

    if abs(payload.quantity_delta) > 500 and current_user.role not in (
        "company_admin",
        "operations_manager",
        "inventory_manager",
    ):
        raise HTTPException(403, "Ajustes superiores a 500 unidades requieren autorización de administración.")

    reference = uuid4()

    movement = move_stock(
        db,
        current_user.company_id,
        payload.warehouse_id,
        payload.product_id,
        payload.quantity_delta,
        payload.unit_cost,
        reference,
        "AJUSTE",
    )

    record_audit(
        db,
        current_user,
        reference,
        "ADJUST_INVENTORY",
        {"reason": payload.reason, "quantity_delta": str(payload.quantity_delta), "evidence_url": payload.evidence_url},
    )

    result = {
        "movement_id": str(movement.id),
        "warehouse_id": str(payload.warehouse_id),
        "product_id": str(payload.product_id),
        "quantity_delta": str(payload.quantity_delta),
        "resulting_physical_qty": str(movement.resulting_physical_qty),
        "reason": payload.reason,
    }

    complete_request(record, result)

    db.commit()

    return result
