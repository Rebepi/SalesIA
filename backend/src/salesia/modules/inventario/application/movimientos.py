from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import KardexMovementModel, ProductModel, WarehouseModel


def list_movements(
    warehouse_id: Optional[UUID],
    product_id: Optional[UUID],
    movement_type: Optional[str],
    cursor: Optional[str],
    limit: int,
    offset: int,
    current_user: AuthenticatedUser,
    db: Session,
):
    if warehouse_id:
        wh = db.scalar(
            select(WarehouseModel).where(
                WarehouseModel.id == warehouse_id, WarehouseModel.company_id == current_user.company_id
            )
        )

        if not wh:
            raise HTTPException(404, "Almacén no encontrado o de otra empresa.")

    if product_id:
        p = db.scalar(
            select(ProductModel).where(
                ProductModel.id == product_id, ProductModel.company_id == current_user.company_id
            )
        )

        if not p:
            raise HTTPException(404, "Producto no encontrado o de otra empresa.")

    filters = [KardexMovementModel.company_id == current_user.company_id]

    if warehouse_id:
        filters.append(KardexMovementModel.warehouse_id == warehouse_id)

    if product_id:
        filters.append(KardexMovementModel.product_id == product_id)

    if movement_type:
        filters.append(KardexMovementModel.movement_type == movement_type)

    rows = db.scalars(
        select(KardexMovementModel)
        .where(*filters)
        .order_by(KardexMovementModel.occurred_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return {
        "items": [
            {
                "id": str(row.id),
                "warehouse_id": str(row.warehouse_id),
                "product_id": str(row.product_id),
                "movement_type": row.movement_type,
                "reference_doc_type": row.reference_doc_type,
                "reference_doc_id": str(row.reference_doc_id),
                "quantity_delta": str(row.quantity_delta),
                "resulting_physical_qty": str(row.resulting_physical_qty),
                "unit_cost": str(row.unit_cost),
                "moving_average_cost": str(row.moving_average_cost),
                "occurred_at": row.occurred_at.isoformat(),
            }
            for row in rows
        ],
        "count": len(rows),
        "limit": limit,
        "offset": offset,
        "cursor": cursor,
    }
