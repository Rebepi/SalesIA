from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select

from salesia.modules.inventario.application.gestion_stock.consulta import product, warehouse
from salesia.modules.inventario.infrastructure_models import InventoryReservation
from salesia.modules.organizacion.application.periodos import business_date, require_open_period
from salesia.shared.infrastructure.models import InventoryStockModel


def reserve_stock(
    db, company_id, warehouse_id, product_id, quantity, document_type, document_id, allow_backorder=False
):
    require_open_period(db, company_id, business_date(db, company_id), ["inventory"])
    warehouse(db, company_id, warehouse_id, lock=True)
    product(db, company_id, product_id)
    existing = db.scalar(
        select(InventoryReservation)
        .where(
            InventoryReservation.company_id == company_id,
            InventoryReservation.document_type == document_type,
            InventoryReservation.document_id == document_id,
            InventoryReservation.product_id == product_id,
        )
        .with_for_update()
    )
    if existing:
        if existing.status == "ACTIVE":
            return existing
        if existing.status in ("CONSUMED", "RELEASED"):
            return existing
    stock = db.scalar(
        select(InventoryStockModel)
        .where(
            InventoryStockModel.company_id == company_id,
            InventoryStockModel.warehouse_id == warehouse_id,
            InventoryStockModel.product_id == product_id,
        )
        .with_for_update()
    )
    if not stock:
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
    available = stock.physical_quantity - stock.reserved_quantity
    if available < quantity and not allow_backorder:
        raise HTTPException(409, "Disponibilidad insuficiente para reservar existencias.")
    stock.reserved_quantity += quantity
    db.flush()
    res = InventoryReservation(
        id=uuid4(),
        company_id=company_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
        document_type=document_type,
        document_id=document_id,
        reserved_quantity=quantity,
        status="ACTIVE",
    )
    db.add(res)
    db.flush()
    return res


def release_reservation(db, company_id, document_type, document_id, product_id=None):
    require_open_period(db, company_id, business_date(db, company_id), ["inventory"])
    query = select(InventoryReservation).where(
        InventoryReservation.company_id == company_id,
        InventoryReservation.document_type == document_type,
        InventoryReservation.document_id == document_id,
    )
    if product_id:
        query = query.where(InventoryReservation.product_id == product_id)
    reservations = db.scalars(query.with_for_update()).all()
    count_released = 0
    for res in reservations:
        if res.status != "ACTIVE":
            continue
        stock = db.scalar(
            select(InventoryStockModel)
            .where(
                InventoryStockModel.company_id == company_id,
                InventoryStockModel.warehouse_id == res.warehouse_id,
                InventoryStockModel.product_id == res.product_id,
            )
            .with_for_update()
        )
        if stock:
            stock.reserved_quantity = max(Decimal("0"), stock.reserved_quantity - res.reserved_quantity)
        res.status = "RELEASED"
        count_released += 1
    db.flush()
    return count_released


def consume_reservation(db, company_id, document_type, document_id, product_id=None):
    require_open_period(db, company_id, business_date(db, company_id), ["inventory"])
    query = select(InventoryReservation).where(
        InventoryReservation.company_id == company_id,
        InventoryReservation.document_type == document_type,
        InventoryReservation.document_id == document_id,
    )
    if product_id:
        query = query.where(InventoryReservation.product_id == product_id)
    reservations = db.scalars(query.with_for_update()).all()
    consumed = 0
    for res in reservations:
        if res.status != "ACTIVE":
            continue
        stock = db.scalar(
            select(InventoryStockModel)
            .where(
                InventoryStockModel.company_id == company_id,
                InventoryStockModel.warehouse_id == res.warehouse_id,
                InventoryStockModel.product_id == res.product_id,
            )
            .with_for_update()
        )
        if stock:
            stock.reserved_quantity = max(Decimal("0"), stock.reserved_quantity - res.reserved_quantity)
            stock.physical_quantity = max(Decimal("0"), stock.physical_quantity - res.reserved_quantity)
        res.status = "CONSUMED"
        consumed += 1
    db.flush()
    return consumed
