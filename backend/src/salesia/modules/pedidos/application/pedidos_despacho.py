import json
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from salesia.modules.pedidos.application.auxiliares.add_history import add_history
from salesia.modules.pedidos.application.auxiliares.audit import audit
from salesia.modules.pedidos.application.auxiliares.locked_order import locked_order
from salesia.modules.pedidos.application.auxiliares.money import money
from salesia.modules.pedidos.application.auxiliares.now import now
from salesia.modules.pedidos.application.auxiliares.order_response import order_response
from salesia.modules.pedidos.application.contracts.pedidos_despacho import OrderFulfillPartialModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.pedidos.application.despacho_stock import dispatch_order_line
from salesia.modules.ventas.application.pedidos_facturacion import synchronize_order_fulfillment
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def fulfill_partial_order(
    order_id: UUID, req: OrderFulfillPartialModel, current_user: AuthenticatedUser, db: Session, idempotency_key: str
):
    record, cached = claim_request(
        db, current_user.company_id, f"orders.fulfill:{order_id}", idempotency_key, req.model_dump(mode="json")
    )

    if cached is not None:
        return cached

    row = locked_order(db, current_user, order_id)

    if row.status not in ("confirmed", "partially_fulfilled", "backorder", "partially_cancelled"):
        raise HTTPException(409, "El pedido no admite despacho.")

    lines = json.loads(row.lines_json)
    requested = {}
    for item in req.fulfilled_items:
        number = item.order_line_number
        if number is None:
            matches = [index for index, line in enumerate(lines, 1) if line["product_id"] == str(item.product_id)]
            if len(matches) != 1:
                raise HTTPException(422, "Identifica la línea concreta del pedido para despachar productos repetidos.")
            number = matches[0]
        if number > len(lines) or lines[number - 1]["product_id"] != str(item.product_id):
            raise HTTPException(422, "El producto no corresponde a la línea de despacho.")
        if number in requested:
            raise HTTPException(422, "No repitas líneas en el despacho.")
        requested[number] = item
    for number, item in requested.items():
        line = lines[number - 1]
        quantity = item.quantity
        fulfilled = Decimal(line.get("fulfilled_quantity", "0"))
        dispatch_order_line(db, row, line, quantity, item.serial_numbers)
        line["fulfilled_quantity"] = str(money(fulfilled + quantity))
        line["reserved_quantity"] = str(money(max(Decimal("0"), Decimal(line.get("reserved_quantity", "0")) - quantity)))

    complete = all(Decimal(line["fulfilled_quantity"]) + Decimal(line.get("cancelled_quantity", "0")) >= Decimal(line["quantity"]) for line in lines)

    row.lines_json, row.status, row.stock_reserved = (
        json.dumps(lines),
        "fulfilled" if complete else "partially_fulfilled",
        any(Decimal(line.get("reserved_quantity", "0")) > 0 for line in lines),
    )

    add_history(row, row.status, current_user, "Despacho registrado")

    audit(db, current_user, "FULFILL", "Order", row.id, req.model_dump(mode="json"))

    synchronize_order_fulfillment(db, row.company_id, row.id)

    response = order_response(row)

    complete_request(record, response)

    db.commit()

    return response


def create_order_picking(order_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = locked_order(db, current_user, order_id)

    if row.status not in ("confirmed", "backorder", "partially_fulfilled"):
        raise HTTPException(409, "Confirme y reserve el pedido antes de prepararlo.")

    current = json.loads(row.picking_json or "{}")

    if current and current.get("status") not in ("COMPLETED", "CANCELLED"):
        return current

    picking = {"id": str(uuid4()), "status": "PENDING", "created_at": now().isoformat(), "lines": []}

    for number, line in enumerate(json.loads(row.lines_json), 1):
        expected = Decimal(line.get("reserved_quantity", "0"))

        if expected > 0:
            picking["lines"].append(
                {
                    "product_id": line["product_id"],
                    "order_line_number": number,
                    "sku": line["sku"],
                    "name": line["name"],
                    "expected_quantity": str(expected),
                    "picked_quantity": "0.000000",
                    "verified": False,
                }
            )

    if not picking["lines"]:
        raise HTTPException(409, "El pedido no tiene cantidades reservadas para preparar.")

    row.picking_json = json.dumps(picking)

    add_history(row, "preparing", current_user, "Lista de preparación creada")

    db.commit()

    return picking
