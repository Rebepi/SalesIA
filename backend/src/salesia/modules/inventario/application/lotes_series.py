from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.inventario.application.contracts.lotes_series import (
    LotCreateRequest,
    SerialCreateRequest,
    SerialSellRequest,
)
from salesia.modules.inventario.infrastructure_models import InventoryLot, InventorySerial
from salesia.modules.inventario.inventory_trace import tracking_trace
from salesia.modules.inventario.service import record_audit
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import ProductModel, SaleLineModel, SaleModel, WarehouseModel


def create_lot(payload: LotCreateRequest, current_user: AuthenticatedUser, db: Session):
    prod = db.scalar(
        select(ProductModel).where(
            ProductModel.id == payload.product_id, ProductModel.company_id == current_user.company_id
        )
    )

    if not prod:
        raise HTTPException(422, "Producto no encontrado o de otra empresa.")

    existing = db.scalar(
        select(InventoryLot).where(
            InventoryLot.company_id == current_user.company_id,
            InventoryLot.product_id == payload.product_id,
            InventoryLot.lot_code == payload.lot_code,
        )
    )

    if existing:
        raise HTTPException(409, "El código de lote ya existe para este producto.")

    try:
        exp_dt = datetime.fromisoformat(payload.expiration_date) if payload.expiration_date else None

        man_dt = datetime.fromisoformat(payload.manufacture_date) if payload.manufacture_date else None

        if exp_dt and man_dt and exp_dt.date() < man_dt.date():
            raise ValueError("date order")

    except ValueError:
        raise HTTPException(
            422, "Revisa las fechas del lote. El vencimiento debe ser igual o posterior a la fabricación."
        )

    lot = InventoryLot(
        id=uuid4(),
        company_id=current_user.company_id,
        product_id=payload.product_id,
        lot_code=payload.lot_code,
        supplier_id=payload.supplier_id,
        manufacture_date=man_dt,
        expiration_date=exp_dt,
        notes=payload.notes,
    )

    db.add(lot)

    db.commit()

    return {"id": str(lot.id), "lot_code": lot.lot_code, "product_id": str(lot.product_id), "status": lot.status}


def list_lots(product_id: Optional[UUID], current_user: AuthenticatedUser, db: Session):
    filters = [InventoryLot.company_id == current_user.company_id]

    if product_id:
        filters.append(InventoryLot.product_id == product_id)

    rows = db.scalars(select(InventoryLot).where(*filters).order_by(InventoryLot.created_at.desc())).all()

    return {
        "items": [
            {
                "id": str(r.id),
                "product_id": str(r.product_id),
                "lot_code": r.lot_code,
                "status": r.status,
                "is_blocked": r.status == "BLOCKED",
                "expiration_date": r.expiration_date.isoformat() if r.expiration_date else None,
            }
            for r in rows
        ]
    }


def lot_trace(lot_id: UUID, current_user: AuthenticatedUser, db: Session):
    return tracking_trace(db, current_user, "lot", lot_id)


def serial_trace(serial_id: UUID, current_user: AuthenticatedUser, db: Session):
    return tracking_trace(db, current_user, "serial", serial_id)


def block_lot(lot_id: UUID, current_user: AuthenticatedUser, db: Session):
    lot = db.scalar(
        select(InventoryLot).where(InventoryLot.id == lot_id, InventoryLot.company_id == current_user.company_id)
    )

    if not lot:
        raise HTTPException(404, "Lote no encontrado.")

    lot.status = "BLOCKED"

    db.commit()

    return {"id": str(lot.id), "status": lot.status}


def create_serial(payload: SerialCreateRequest, current_user: AuthenticatedUser, db: Session):
    wh = db.scalar(
        select(WarehouseModel).where(
            WarehouseModel.id == payload.warehouse_id, WarehouseModel.company_id == current_user.company_id
        )
    )

    if not wh:
        raise HTTPException(422, "Almacén no encontrado o de otra empresa.")

    prod = db.scalar(
        select(ProductModel).where(
            ProductModel.id == payload.product_id, ProductModel.company_id == current_user.company_id
        )
    )

    if not prod:
        raise HTTPException(422, "Producto no encontrado o de otra empresa.")

    existing = db.scalar(
        select(InventorySerial).where(
            InventorySerial.company_id == current_user.company_id,
            InventorySerial.product_id == payload.product_id,
            InventorySerial.serial_number == payload.serial_number,
        )
    )

    if existing:
        raise HTTPException(409, "La serie ya se encuentra registrada para este producto.")

    serial = InventorySerial(
        id=uuid4(),
        company_id=current_user.company_id,
        product_id=payload.product_id,
        warehouse_id=payload.warehouse_id,
        serial_number=payload.serial_number,
        location_id=payload.location_id,
        lot_id=payload.lot_id,
        status="IN_STOCK",
    )

    db.add(serial)

    db.commit()

    return {"id": str(serial.id), "serial_number": serial.serial_number, "status": serial.status}


def list_serials(
    product_id: Optional[UUID], warehouse_id: Optional[UUID], current_user: AuthenticatedUser, db: Session
):
    filters = [InventorySerial.company_id == current_user.company_id]

    if product_id:
        filters.append(InventorySerial.product_id == product_id)

    if warehouse_id:
        filters.append(InventorySerial.warehouse_id == warehouse_id)

    rows = db.scalars(select(InventorySerial).where(*filters)).all()

    return {
        "items": [
            {
                "id": str(r.id),
                "serial_number": r.serial_number,
                "product_id": str(r.product_id),
                "warehouse_id": str(r.warehouse_id),
                "status": r.status,
            }
            for r in rows
        ]
    }


def sell_serial(payload: SerialSellRequest, current_user: AuthenticatedUser, db: Session):
    serial = db.scalar(
        select(InventorySerial)
        .where(
            InventorySerial.company_id == current_user.company_id,
            InventorySerial.product_id == payload.product_id,
            InventorySerial.serial_number == payload.serial_number,
        )
        .with_for_update()
    )

    if not serial:
        raise HTTPException(404, "Serie no encontrada.")

    if serial.status != "IN_STOCK":
        raise HTTPException(409, f"La serie no se puede vender: su estado actual es {serial.status}.")

    sale = db.scalar(
        select(SaleModel).where(
            SaleModel.id == payload.sale_id,
            SaleModel.company_id == current_user.company_id,
            SaleModel.status.in_(["confirmed", "paid"]),
        )
    )

    sale_line = db.scalar(
        select(SaleLineModel.id).where(
            SaleLineModel.sale_id == payload.sale_id,
            SaleLineModel.company_id == current_user.company_id,
            SaleLineModel.product_id == payload.product_id,
        )
    )

    if not sale or not sale_line or sale.warehouse_id != serial.warehouse_id:
        raise HTTPException(422, "Selecciona una venta confirmada de este producto y almacén.")

    serial.status = "SOLD"

    serial.current_doc_type = "SALE"

    serial.current_doc_id = payload.sale_id

    record_audit(
        db, current_user, serial.id, "SELL_SERIAL", {"sale_id": str(sale.id), "serial_number": serial.serial_number}
    )

    db.commit()

    return {"id": str(serial.id), "serial_number": serial.serial_number, "status": serial.status}
