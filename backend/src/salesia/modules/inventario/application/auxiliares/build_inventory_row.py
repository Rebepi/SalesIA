from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.inventario.infrastructure_models import InventoryQuarantine, SupplyDocument, SupplyLine
from salesia.shared.infrastructure.models import InventoryStockModel, ProductModel


def build_inventory_row(db: Session, row: InventoryStockModel):

    prod = db.scalar(
        select(ProductModel).where(ProductModel.id == row.product_id, ProductModel.company_id == row.company_id)
    )

    uom = prod.unit_of_measure if prod else "NIU"

    sku = prod.sku if prod else ""

    prod_name = prod.name if prod else ""

    quarantine_qty = db.scalar(
        select(func.coalesce(func.sum(InventoryQuarantine.quantity), Decimal("0"))).where(
            InventoryQuarantine.company_id == row.company_id,
            InventoryQuarantine.warehouse_id == row.warehouse_id,
            InventoryQuarantine.product_id == row.product_id,
            InventoryQuarantine.status == "IN_QUARANTINE",
        )
    ) or Decimal("0")

    transit_qty = db.scalar(
        select(
            func.coalesce(
                func.sum(SupplyLine.quantity - SupplyLine.processed_quantity - SupplyLine.damaged_quantity),
                Decimal("0"),
            )
        )
        .join(SupplyDocument, SupplyDocument.id == SupplyLine.document_id)
        .where(
            SupplyDocument.company_id == row.company_id,
            SupplyDocument.kind == "TRANSFER",
            SupplyDocument.warehouse_id == row.warehouse_id,
            SupplyDocument.status.in_(("in_transit", "partially_received")),
            SupplyLine.product_id == row.product_id,
        )
    ) or Decimal("0")

    avail = max(Decimal("0"), row.physical_quantity - row.reserved_quantity)

    return {
        "id": str(row.id),
        "warehouse_id": str(row.warehouse_id),
        "product_id": str(row.product_id),
        "sku": sku,
        "product_name": prod_name,
        "unit_of_measure": uom,
        "physical_quantity": str(row.physical_quantity),
        "reserved_quantity": str(row.reserved_quantity),
        "available_quantity": str(avail),
        "transit_quantity": str(transit_qty),
        "quarantine_quantity": str(quarantine_qty),
        "blocked_quantity": str(row.reserved_quantity + quarantine_qty),
        "average_cost": str(row.average_cost),
        "updated_at": row.updated_at.isoformat(),
    }
