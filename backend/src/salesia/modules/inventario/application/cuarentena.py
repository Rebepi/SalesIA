from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.inventario.application.contracts.cuarentena import QuarantineClassifyRequest
from salesia.modules.inventario.infrastructure_models import InventoryQuarantine
from salesia.modules.inventario.receipt_workflow import release_receipt_quarantine
from salesia.modules.inventario.service import move_stock, product
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def list_quarantine_items(current_user: AuthenticatedUser, db: Session):
    rows = db.scalars(
        select(InventoryQuarantine).where(
            InventoryQuarantine.company_id == current_user.company_id, InventoryQuarantine.status == "IN_QUARANTINE"
        )
    ).all()

    return {
        "items": [
            {
                "id": str(r.id),
                "warehouse_id": str(r.warehouse_id),
                "product_id": str(r.product_id),
                "quantity": str(r.quantity),
                "reason": r.reason,
                "status": r.status,
            }
            for r in rows
        ]
    }


def classify_quarantine_item(
    quarantine_id: UUID, payload: QuarantineClassifyRequest, current_user: AuthenticatedUser, db: Session
):
    item = db.scalar(
        select(InventoryQuarantine)
        .where(InventoryQuarantine.id == quarantine_id, InventoryQuarantine.company_id == current_user.company_id)
        .with_for_update()
    )

    if not item or item.status != "IN_QUARANTINE":
        raise HTTPException(404, "Elemento en cuarentena no encontrado o ya clasificado.")

    if item.reference_doc_type == "GOODS_RECEIPT":
        release_receipt_quarantine(db, current_user, item, payload.action == "RESTOCK")

        item.status = "RELEASED_TO_STOCK" if payload.action == "RESTOCK" else "SCRAPPED"

    elif payload.action == "RESTOCK":
        prod = product(db, current_user.company_id, item.product_id)

        move_stock(
            db,
            current_user.company_id,
            item.warehouse_id,
            item.product_id,
            item.quantity,
            prod.unit_cost,
            item.id,
            "CUARENTENA_LIBERADA",
        )

        item.status = "RELEASED_TO_STOCK"

    else:
        item.status = "SCRAPPED"

    item.inspected_by = current_user.user_id

    item.resolution_notes = payload.notes

    db.commit()

    return {"id": str(item.id), "status": item.status}
