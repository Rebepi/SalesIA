from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.inventario.application.auxiliares.build_inventory_row import build_inventory_row
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import InventoryStockModel, ProductModel, WarehouseModel


def list_inventory(
    warehouse_id: Optional[UUID],
    product_id: Optional[UUID],
    search: Optional[str],
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

    filters = [InventoryStockModel.company_id == current_user.company_id]

    if warehouse_id:
        filters.append(InventoryStockModel.warehouse_id == warehouse_id)

    if product_id:
        filters.append(InventoryStockModel.product_id == product_id)

    if search:
        search_pattern = f"%{search}%"

        prod_ids = db.scalars(
            select(ProductModel.id).where(
                ProductModel.company_id == current_user.company_id,
                (ProductModel.name.ilike(search_pattern)) | (ProductModel.sku.ilike(search_pattern)),
            )
        ).all()

        filters.append(InventoryStockModel.product_id.in_(prod_ids))

    total = db.scalar(select(func.count()).select_from(InventoryStockModel).where(*filters))

    rows = db.scalars(
        select(InventoryStockModel)
        .where(*filters)
        .order_by(InventoryStockModel.updated_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return {
        "items": [build_inventory_row(db, row) for row in rows],
        "count": len(rows),
        "total_count": total,
        "limit": limit,
        "offset": offset,
    }
