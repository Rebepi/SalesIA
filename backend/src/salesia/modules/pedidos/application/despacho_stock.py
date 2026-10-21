from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, update

from salesia.modules.catalogo.infrastructure_models import ProductProfileModel
from salesia.modules.inventario.infrastructure_models import InventorySerial
from salesia.modules.organizacion.application.periodos import business_date, require_open_period
from salesia.modules.pedidos.application.auxiliares.now import now
from salesia.shared.infrastructure.models import InventoryStockModel, KardexMovementModel


def dispatch_order_line(db, order, line, quantity, serial_numbers=None):
    require_open_period(db, order.company_id, business_date(db, order.company_id), ["inventory"])
    product_id = UUID(line["product_id"])
    fulfilled = Decimal(line.get("fulfilled_quantity", "0"))
    if fulfilled + quantity + Decimal(line.get("cancelled_quantity", "0")) > Decimal(line["quantity"]):
        raise HTTPException(409, "El despacho supera el saldo pendiente de la línea.")
    profile = db.scalar(select(ProductProfileModel).where(ProductProfileModel.company_id == order.company_id, ProductProfileModel.product_id == product_id))
    if profile and (profile.product_type == "service" or not profile.track_inventory):
        return
    if Decimal(line.get("reserved_quantity", "0")) < quantity:
        raise HTTPException(409, f"La reserva propia de {line['sku']} no alcanza para este despacho.")
    stock = db.scalar(select(InventoryStockModel).where(InventoryStockModel.company_id == order.company_id, InventoryStockModel.warehouse_id == order.warehouse_id, InventoryStockModel.product_id == product_id).with_for_update())
    if not stock:
        raise HTTPException(409, "Faltan existencias para despachar.")
    selected = [value.strip() for value in serial_numbers or [] if value.strip()]
    serial_required = bool(profile and profile.tracking_mode == "SERIAL")
    if serial_required or selected:
        if quantity != quantity.to_integral_value() or len(selected) != int(quantity) or len(set(selected)) != len(selected):
            raise HTTPException(422, "Escanea una serie distinta por cada unidad que despachas.")
        serials = db.scalars(select(InventorySerial).where(InventorySerial.company_id == order.company_id, InventorySerial.product_id == product_id, InventorySerial.warehouse_id == order.warehouse_id, InventorySerial.serial_number.in_(selected), InventorySerial.status == "IN_STOCK").with_for_update()).all()
        if len(serials) != len(selected):
            raise HTTPException(409, "Una de las series ya no está disponible en el almacén del pedido.")
        for serial in serials:
            serial.status, serial.current_doc_type, serial.current_doc_id = "SOLD", "ORDER", order.id
        line["fulfilled_serial_numbers"] = list(line.get("fulfilled_serial_numbers", [])) + selected
    changed = db.execute(update(InventoryStockModel).where(InventoryStockModel.id == stock.id, InventoryStockModel.physical_quantity >= quantity, InventoryStockModel.reserved_quantity >= quantity).values(physical_quantity=InventoryStockModel.physical_quantity - quantity, reserved_quantity=InventoryStockModel.reserved_quantity - quantity))
    if changed.rowcount != 1:
        raise HTTPException(409, "El inventario o las reservas cambiaron durante el despacho.")
    db.refresh(stock)
    db.add(KardexMovementModel(company_id=order.company_id, warehouse_id=order.warehouse_id, product_id=product_id, movement_type="ORDER_DISPATCH", reference_doc_type="ORDER", reference_doc_id=order.id, quantity_delta=-quantity, resulting_physical_qty=stock.physical_quantity, unit_cost=stock.average_cost, moving_average_cost=stock.average_cost, occurred_at=now()))
