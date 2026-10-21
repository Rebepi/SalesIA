from datetime import datetime, timezone
from decimal import ROUND_HALF_EVEN, Decimal
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select, update

from salesia.modules.inventario.application.gestion_stock.consulta import product, warehouse
from salesia.modules.inventario.infrastructure_models import LocationStock, WarehouseLocation
from salesia.shared.infrastructure.models import InventoryStockModel, KardexMovementModel
from salesia.modules.organizacion.application.periodos import business_date, require_open_period


def move_stock(
    db, company_id, warehouse_id, product_id, delta, cost, reference_id, movement_type, allow_negative=False
):
    require_open_period(db, company_id, business_date(db, company_id), ["inventory"])
    from salesia.modules.organizacion.application.perfil_operativo import require_area
    require_area(db, company_id, "inventory")
    warehouse(db, company_id, warehouse_id, lock=True)
    product(db, company_id, product_id)
    stock = db.scalar(
        select(InventoryStockModel)
        .where(
            InventoryStockModel.company_id == company_id,
            InventoryStockModel.warehouse_id == warehouse_id,
            InventoryStockModel.product_id == product_id,
        )
        .with_for_update()
    )
    if stock is None:
        if delta < 0 and not allow_negative:
            raise HTTPException(409, "No hay stock registrado para la salida.")
        stock = InventoryStockModel(
            company_id=company_id,
            warehouse_id=warehouse_id,
            product_id=product_id,
            physical_quantity=Decimal("0"),
            reserved_quantity=Decimal("0"),
            average_cost=Decimal("0"),
        )
        db.add(stock)
        db.flush()
    if stock.physical_quantity + delta < stock.reserved_quantity and not allow_negative:
        raise HTTPException(409, "La operación consumiría existencias reservadas o produciría stock negativo.")
    before = stock.physical_quantity
    resulting = before + delta
    if resulting < 0 and not allow_negative:
        raise HTTPException(409, "Saldo vendible negativo no permitido.")
    applied_cost = cost if delta > 0 else stock.average_cost
    average = (
        ((before * stock.average_cost + delta * cost) / resulting).quantize(
            Decimal("0.000001"), rounding=ROUND_HALF_EVEN
        )
        if delta > 0 and resulting > 0
        else stock.average_cost
    )
    changed = db.execute(
        update(InventoryStockModel)
        .where(InventoryStockModel.id == stock.id, InventoryStockModel.physical_quantity == before)
        .values(physical_quantity=resulting, average_cost=average)
    )
    if changed.rowcount != 1:
        raise HTTPException(409, "El inventario cambió; reintente con la misma clave.")
    movement = KardexMovementModel(
        id=uuid4(),
        company_id=company_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
        movement_type=movement_type,
        reference_doc_type=movement_type,
        reference_doc_id=reference_id,
        quantity_delta=delta,
        resulting_physical_qty=resulting,
        unit_cost=applied_cost,
        moving_average_cost=average,
        occurred_at=datetime.now(timezone.utc),
    )
    db.add(movement)
    db.flush()
    return movement


def move_between_locations(db, user, warehouse_id, product_id, from_location_id, to_location_id, quantity):
    if from_location_id == to_location_id:
        raise HTTPException(422, "Las ubicaciones origen y destino deben ser distintas.")
    if quantity <= 0:
        raise HTTPException(422, "La cantidad a transferir debe ser mayor a cero.")
    warehouse(db, user.company_id, warehouse_id)
    product(db, user.company_id, product_id)
    loc_from = db.scalar(
        select(WarehouseLocation).where(
            WarehouseLocation.id == from_location_id,
            WarehouseLocation.warehouse_id == warehouse_id,
            WarehouseLocation.company_id == user.company_id,
            WarehouseLocation.is_active.is_(True),
        )
    )
    loc_to = db.scalar(
        select(WarehouseLocation).where(
            WarehouseLocation.id == to_location_id,
            WarehouseLocation.warehouse_id == warehouse_id,
            WarehouseLocation.company_id == user.company_id,
            WarehouseLocation.is_active.is_(True),
        )
    )
    if not loc_from or not loc_to:
        raise HTTPException(422, "Ubicación origen o destino no encontrada en este almacén.")
    stock_from = db.scalar(
        select(LocationStock)
        .where(
            LocationStock.company_id == user.company_id,
            LocationStock.location_id == from_location_id,
            LocationStock.product_id == product_id,
        )
        .with_for_update()
    )
    if not stock_from or stock_from.quantity < quantity:
        raise HTTPException(409, "Existencias insuficientes en la ubicación origen.")
    stock_to = db.scalar(
        select(LocationStock)
        .where(
            LocationStock.company_id == user.company_id,
            LocationStock.location_id == to_location_id,
            LocationStock.product_id == product_id,
        )
        .with_for_update()
    )
    if not stock_to:
        stock_to = LocationStock(
            company_id=user.company_id,
            warehouse_id=warehouse_id,
            location_id=to_location_id,
            product_id=product_id,
            quantity=Decimal("0"),
        )
        db.add(stock_to)
        db.flush()
    stock_from.quantity -= quantity
    stock_to.quantity += quantity
    db.flush()
    return {
        "warehouse_id": str(warehouse_id),
        "product_id": str(product_id),
        "from_location_id": str(from_location_id),
        "to_location_id": str(to_location_id),
        "quantity": str(quantity),
    }
