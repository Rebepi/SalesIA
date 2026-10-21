import json
from collections import defaultdict
from decimal import Decimal
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select

from salesia.modules.pedidos.infrastructure.models import OrderModel
from salesia.modules.ventas.infrastructure.models import SaleLineModel, SaleModel


def locked_billing_order(db, company_id, order_id):
    row = db.scalar(select(OrderModel).where(OrderModel.company_id == company_id, OrderModel.id == order_id).with_for_update())
    if row is None:
        raise HTTPException(404, "Pedido de origen no encontrado.")
    if row.status not in ("confirmed", "partially_fulfilled", "fulfilled", "backorder"):
        raise HTTPException(409, "El pedido debe estar confirmado para generar una venta vinculada.")
    return row


def validate_billing_capacity(db, company_id, order, requested, exclude_sale_id=None):
    source = json.loads(order.lines_json or "[]")
    by_number = {index: line for index, line in enumerate(source, 1)}
    statement = select(SaleLineModel).join(SaleModel, SaleModel.id == SaleLineModel.sale_id).where(SaleModel.company_id == company_id, SaleModel.order_id == order.id, SaleModel.status.in_(("draft", "confirmed", "paid", "refunded")))
    if exclude_sale_id:
        statement = statement.where(SaleModel.id != exclude_sale_id)
    billed = defaultdict(lambda: Decimal("0"))
    for line in db.scalars(statement).all():
        if line.order_line_number:
            billed[line.order_line_number] += line.quantity
    for line in requested:
        number = line.order_line_number
        if number is None:
            matches = [index for index, original in by_number.items() if original["product_id"] == str(line.product_id)]
            if len(matches) != 1:
                raise HTTPException(422, "Selecciona el número de línea del pedido que se facturará.")
            number = matches[0]
            line.order_line_number = number
        original = by_number.get(number)
        if not original or original["product_id"] != str(line.product_id):
            raise HTTPException(422, "La línea no corresponde al producto del pedido.")
        billed[number] += line.quantity
        if billed[number] > Decimal(original["quantity"]) - Decimal(original.get("cancelled_quantity", "0")):
            raise HTTPException(409, f"La línea {number} ya está facturada o comprometida en otra venta en borrador.")
    return by_number


def validate_sale_source(db, sale):
    if not sale.order_id:
        return
    order = locked_billing_order(db, sale.company_id, sale.order_id)
    validate_billing_capacity(db, sale.company_id, order, sale.lines, sale.id)


def synchronize_order_fulfillment(db, company_id, order_id):
    db.flush()
    order = db.scalar(select(OrderModel).where(OrderModel.company_id == company_id, OrderModel.id == order_id))
    if order is None:
        return
    remaining = {index: Decimal(line.get("fulfilled_quantity", "0")) for index, line in enumerate(json.loads(order.lines_json or "[]"), 1)}
    serials = {index: list(line.get("fulfilled_serial_numbers", [])) for index, line in enumerate(json.loads(order.lines_json or "[]"), 1)}
    events = [event for event in json.loads(order.history_json or "[]") if event.get("status") in ("fulfilled", "partially_fulfilled")]
    last_dispatch = datetime.fromisoformat(events[-1]["timestamp"]) if events and events[-1].get("timestamp") else datetime.now(timezone.utc)
    sales = db.scalars(select(SaleModel).where(SaleModel.company_id == company_id, SaleModel.order_id == order_id, SaleModel.status.in_(("confirmed", "paid", "refunded"))).order_by(SaleModel.confirmed_at, SaleModel.created_at, SaleModel.id).with_for_update()).all()
    for sale in sales:
        expected, fulfilled = Decimal("0"), Decimal("0")
        for line in sale.lines:
            number = line.order_line_number
            expected += line.quantity
            assigned = min(line.quantity, remaining.get(number, Decimal("0")))
            line.fulfilled_quantity = assigned
            if assigned > 0 and line.delivered_at is None:
                line.delivered_at = last_dispatch
            if number in serials and serials[number]:
                line.serial_numbers_json = json.dumps(serials[number][:int(assigned)])
                serials[number] = serials[number][int(assigned):]
            fulfilled += assigned
            remaining[number] = remaining.get(number, Decimal("0")) - assigned
        sale.fulfillment_status = "delivered" if expected > 0 and fulfilled == expected else "partial" if fulfilled > 0 else "pending"
