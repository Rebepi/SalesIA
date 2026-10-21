import json
from datetime import timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from salesia.modules.pedidos.application.auxiliares.add_history import add_history
from salesia.modules.pedidos.application.auxiliares.audit import audit
from salesia.modules.pedidos.application.auxiliares.locked_order import locked_order
from salesia.modules.pedidos.application.auxiliares.now import now
from salesia.modules.pedidos.application.auxiliares.order_response import order_response
from salesia.modules.pedidos.application.auxiliares.validate_references import validate_references
from salesia.modules.pedidos.application.contracts.pedidos_reservas_faltantes import OrderShortageResolution
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import InventoryStockModel, ProductModel, WarehouseModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def release_order_reservation(order_id: UUID, current_user: AuthenticatedUser, db: Session, idempotency_key: str):
    record, cached = claim_request(db, current_user.company_id, f"orders.release_res:{order_id}", idempotency_key, {})

    if cached is not None:
        return cached

    row = locked_order(db, current_user, order_id)

    if row.status not in ("confirmed", "backorder", "partially_fulfilled") or not row.stock_reserved:
        raise HTTPException(409, "El pedido no tiene reservas activas.")

    lines = json.loads(row.lines_json)

    for line in lines:
        reserved = Decimal(line.get("reserved_quantity", "0"))

        if reserved > 0:
            changed = db.execute(
                update(InventoryStockModel)
                .where(
                    InventoryStockModel.company_id == row.company_id,
                    InventoryStockModel.warehouse_id == row.warehouse_id,
                    InventoryStockModel.product_id == UUID(line["product_id"]),
                    InventoryStockModel.reserved_quantity >= reserved,
                )
                .values(reserved_quantity=InventoryStockModel.reserved_quantity - reserved)
            )

            if changed.rowcount == 1:
                line["reserved_quantity"] = "0.000000"

    row.lines_json = json.dumps(lines)

    row.stock_reserved = False

    row.reservation_expires_at = None

    add_history(row, row.status, current_user, "Reserva de stock liberada")

    audit(db, current_user, "RELEASE_RESERVATION", "Order", row.id, {})

    response = order_response(row)

    complete_request(record, response)

    db.commit()

    return response


def renew_order_reservation(order_id: UUID, extension_days: int, current_user: AuthenticatedUser, db: Session):
    row = locked_order(db, current_user, order_id)

    if row.status not in ("confirmed", "backorder", "partially_fulfilled") or not row.stock_reserved:
        raise HTTPException(409, "El pedido no tiene reservas activas para renovar.")

    new_expiry = (now() + timedelta(days=extension_days)).isoformat()

    row.reservation_expires_at = new_expiry

    add_history(row, row.status, current_user, f"Reserva renovada hasta {new_expiry}")

    db.commit()

    return order_response(row)


def get_order_shortages(order_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = locked_order(db, current_user, order_id)

    shortages = []

    for line in json.loads(row.lines_json):
        product_id = UUID(line["product_id"])

        stock = db.scalar(
            select(InventoryStockModel).where(
                InventoryStockModel.company_id == row.company_id,
                InventoryStockModel.warehouse_id == row.warehouse_id,
                InventoryStockModel.product_id == product_id,
            )
        )

        available = max(Decimal("0"), stock.physical_quantity - stock.reserved_quantity) if stock else Decimal("0")

        required = (
            Decimal(line["quantity"])
            - Decimal(line.get("fulfilled_quantity", "0"))
            - Decimal(line.get("reserved_quantity", "0"))
        )

        if available < required or Decimal(line.get("backorder_quantity", "0")) > 0:
            alternatives = db.execute(
                select(
                    WarehouseModel.id,
                    WarehouseModel.name,
                    InventoryStockModel.physical_quantity,
                    InventoryStockModel.reserved_quantity,
                )
                .join(InventoryStockModel, InventoryStockModel.warehouse_id == WarehouseModel.id)
                .where(
                    WarehouseModel.company_id == row.company_id,
                    WarehouseModel.id != row.warehouse_id,
                    InventoryStockModel.product_id == product_id,
                    InventoryStockModel.physical_quantity > InventoryStockModel.reserved_quantity,
                )
            ).all()

            shortages.append(
                {
                    "product_id": str(product_id),
                    "sku": line["sku"],
                    "name": line["name"],
                    "required_quantity": str(required),
                    "available_quantity": str(available),
                    "missing_quantity": str(max(Decimal("0"), required - available)),
                    "alternatives": [
                        {
                            "warehouse_id": str(item.id),
                            "warehouse_name": item.name,
                            "available_quantity": str(item.physical_quantity - item.reserved_quantity),
                        }
                        for item in alternatives
                    ],
                    "actions": ["SUBSTITUTE", "BACKORDER", "PARTIAL_DELIVERY", "CHANGE_WAREHOUSE", "ESTIMATED_DATE"],
                }
            )

    return {"order_id": str(row.id), "warehouse_id": str(row.warehouse_id), "shortages": shortages}


def resolve_order_shortage(order_id: UUID, req: OrderShortageResolution, current_user: AuthenticatedUser, db: Session):
    row = locked_order(db, current_user, order_id)

    if row.status in ("fulfilled", "cancelled"):
        raise HTTPException(409, "El pedido ya no admite cambios de abastecimiento.")

    lines = json.loads(row.lines_json)

    line = next((item for item in lines if UUID(item["product_id"]) == req.product_id), None)

    if not line:
        raise HTTPException(404, "El producto no pertenece al pedido.")

    if req.action in ("CHANGE_WAREHOUSE", "SUBSTITUTE") and row.stock_reserved:
        raise HTTPException(409, "Libere primero la reserva activa antes de cambiar el almacén o sustituir productos.")

    if req.action == "CHANGE_WAREHOUSE":
        if not req.warehouse_id:
            raise HTTPException(422, "Seleccione el almacén alternativo.")

        validate_references(db, row.company_id, row.customer_id, row.branch_id, req.warehouse_id)

        for item in lines:
            stock = db.scalar(
                select(InventoryStockModel).where(
                    InventoryStockModel.company_id == row.company_id,
                    InventoryStockModel.warehouse_id == req.warehouse_id,
                    InventoryStockModel.product_id == UUID(item["product_id"]),
                )
            )

            if not stock or stock.physical_quantity - stock.reserved_quantity < Decimal(item["quantity"]) - Decimal(
                item.get("fulfilled_quantity", "0")
            ):
                raise HTTPException(409, f"El almacén alternativo no cubre {item['sku']}.")

        row.warehouse_id = req.warehouse_id

        row.status = "draft"

        row.stock_reserved = False

    elif req.action == "SUBSTITUTE":
        if not req.substitute_product_id:
            raise HTTPException(422, "Seleccione el producto sustituto.")

        substitute = db.scalar(
            select(ProductModel).where(
                ProductModel.id == req.substitute_product_id,
                ProductModel.company_id == row.company_id,
                ProductModel.is_active.is_(True),
            )
        )

        if not substitute:
            raise HTTPException(404, "Producto sustituto no encontrado.")

        if any(UUID(item["product_id"]) == substitute.id for item in lines):
            raise HTTPException(409, "El producto sustituto ya figura en el pedido.")

        line.update(
            {
                "product_id": str(substitute.id),
                "sku": substitute.sku,
                "name": substitute.name,
                "unit_price": str(substitute.unit_price),
                "unit_cost": str(substitute.unit_cost),
                "tax_rate": str(substitute.tax_rate),
                "reserved_quantity": "0.000000",
                "backorder_quantity": "0.000000",
                "is_backorder": False,
            }
        )

        row.status = "draft"

        row.stock_reserved = False

    elif req.action == "BACKORDER":
        line["is_backorder"] = True

        line["backorder_quantity"] = str(
            Decimal(line["quantity"])
            - Decimal(line.get("fulfilled_quantity", "0"))
            - Decimal(line.get("reserved_quantity", "0"))
        )

        row.status = "backorder"

    elif req.action == "PARTIAL_DELIVERY":
        row.status = "partially_fulfilled"

    else:
        if not req.estimated_delivery_date:
            raise HTTPException(422, "Indique la fecha estimada de reposición.")

        line["estimated_delivery_date"] = req.estimated_delivery_date

        line["is_backorder"] = True

        row.status = "backorder"

    row.lines_json = json.dumps(lines)

    add_history(row, row.status, current_user, f"Faltante resuelto con {req.action}")

    audit(db, current_user, "RESOLVE_SHORTAGE", "Order", row.id, req.model_dump(mode="json"))

    db.commit()

    return order_response(row)
