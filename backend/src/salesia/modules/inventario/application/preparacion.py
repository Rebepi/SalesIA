from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.inventario.application.contracts.preparacion import PickingCreateRequest, PickingVerifyRequest
from salesia.modules.inventario.infrastructure_models import InventoryPickingLine, InventoryPickingList
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import ProductModel, SaleModel


def create_picking_list(payload: PickingCreateRequest, current_user: AuthenticatedUser, db: Session):
    sale = db.scalar(
        select(SaleModel).where(SaleModel.id == payload.sale_id, SaleModel.company_id == current_user.company_id)
    )

    if not sale:
        raise HTTPException(404, "Venta no encontrada.")

    picking = InventoryPickingList(
        id=uuid4(),
        company_id=current_user.company_id,
        warehouse_id=payload.warehouse_id,
        sale_id=payload.sale_id,
        assigned_to=current_user.user_id,
        status="PENDING",
    )

    db.add(picking)

    db.flush()

    for line in sale.lines:
        db.add(
            InventoryPickingLine(
                id=uuid4(),
                company_id=current_user.company_id,
                picking_list_id=picking.id,
                product_id=line.product_id,
                expected_quantity=line.quantity,
                picked_quantity=Decimal("0"),
                is_verified=False,
            )
        )

    db.commit()

    return {"id": str(picking.id), "sale_id": str(picking.sale_id), "status": picking.status}


def verify_picking_item(picking_id: UUID, payload: PickingVerifyRequest, current_user: AuthenticatedUser, db: Session):
    picking = db.scalar(
        select(InventoryPickingList).where(
            InventoryPickingList.id == picking_id, InventoryPickingList.company_id == current_user.company_id
        )
    )

    if not picking:
        raise HTTPException(404, "Lista de picking no encontrada.")

    line = db.scalar(
        select(InventoryPickingLine)
        .where(
            InventoryPickingLine.picking_list_id == picking_id, InventoryPickingLine.product_id == payload.product_id
        )
        .with_for_update()
    )

    if not line:
        raise HTTPException(422, "Producto incorrecto escaneado; no pertenece a esta orden de preparación.")

    prod = db.scalar(
        select(ProductModel).where(
            ProductModel.id == payload.product_id, ProductModel.company_id == current_user.company_id
        )
    )

    if prod and payload.scanned_code not in (prod.sku, str(prod.id)):
        raise HTTPException(422, "Código o SKU escaneado no coincide con el producto esperado.")

    line.picked_quantity += payload.quantity

    if line.picked_quantity >= line.expected_quantity:
        line.is_verified = True

    db.commit()

    return {
        "picking_id": str(picking.id),
        "product_id": str(line.product_id),
        "picked_quantity": str(line.picked_quantity),
        "is_verified": line.is_verified,
    }


def complete_picking_list(picking_id: UUID, current_user: AuthenticatedUser, db: Session):
    picking = db.scalar(
        select(InventoryPickingList)
        .where(InventoryPickingList.id == picking_id, InventoryPickingList.company_id == current_user.company_id)
        .with_for_update()
    )

    if not picking:
        raise HTTPException(404, "Lista de picking no encontrada.")

    if not all(l.is_verified for l in picking.lines):
        raise HTTPException(422, "No se puede completar: aún existen líneas pendientes o no verificadas.")

    picking.status = "COMPLETED"

    db.commit()

    return {"id": str(picking.id), "status": picking.status}
