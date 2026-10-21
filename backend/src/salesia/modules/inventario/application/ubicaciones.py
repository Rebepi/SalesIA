from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.inventario.application.contracts.ubicaciones import (
    LocationCreateRequest,
    LocationTransferRequest,
    LocationUpdateRequest,
)
from salesia.modules.inventario.infrastructure_models import InventorySerial, LocationStock, WarehouseLocation
from salesia.modules.inventario.service import move_between_locations, record_audit, warehouse
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import WarehouseModel


def create_location(payload: LocationCreateRequest, current_user: AuthenticatedUser, db: Session):
    wh = db.scalar(
        select(WarehouseModel).where(
            WarehouseModel.id == payload.warehouse_id, WarehouseModel.company_id == current_user.company_id
        )
    )

    if not wh:
        raise HTTPException(422, "Almacén no encontrado o de otra empresa.")

    existing = db.scalar(
        select(WarehouseLocation).where(
            WarehouseLocation.company_id == current_user.company_id,
            WarehouseLocation.warehouse_id == payload.warehouse_id,
            WarehouseLocation.code == payload.code,
        )
    )

    if existing:
        raise HTTPException(409, "El código de ubicación ya existe en este almacén.")

    loc = WarehouseLocation(
        id=uuid4(),
        company_id=current_user.company_id,
        warehouse_id=payload.warehouse_id,
        code=payload.code,
        aisle=payload.aisle,
        rack=payload.rack,
        shelf=payload.shelf,
        bin=payload.bin,
        capacity_units=payload.capacity_units,
    )

    db.add(loc)

    db.commit()

    return {
        "id": str(loc.id),
        "code": loc.code,
        "warehouse_id": str(loc.warehouse_id),
        "capacity_units": str(loc.capacity_units),
    }


def list_locations(warehouse_id: Optional[UUID], current_user: AuthenticatedUser, db: Session):
    wh = (
        db.scalar(
            select(WarehouseModel).where(
                WarehouseModel.id == warehouse_id, WarehouseModel.company_id == current_user.company_id
            )
        )
        if warehouse_id
        else None
    )

    if warehouse_id and not wh:
        raise HTTPException(404, "Almacén no encontrado o de otra empresa.")

    query = select(WarehouseLocation).where(WarehouseLocation.company_id == current_user.company_id)

    if warehouse_id:
        query = query.where(WarehouseLocation.warehouse_id == warehouse_id)

    rows = db.scalars(query).all()

    return {
        "items": [
            {
                "id": str(r.id),
                "warehouse_id": str(r.warehouse_id),
                "code": r.code,
                "aisle": r.aisle,
                "rack": r.rack,
                "shelf": r.shelf,
                "bin": r.bin,
                "capacity_units": str(r.capacity_units),
                "is_active": r.is_active,
            }
            for r in rows
        ]
    }


def update_location(location_id: UUID, payload: LocationUpdateRequest, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(WarehouseLocation)
        .where(WarehouseLocation.id == location_id, WarehouseLocation.company_id == current_user.company_id)
        .with_for_update()
    )

    if not row:
        raise HTTPException(404, "Ubicación no encontrada.")

    warehouse(db, current_user.company_id, row.warehouse_id, lock=True)

    if db.scalar(
        select(WarehouseLocation.id).where(
            WarehouseLocation.company_id == current_user.company_id,
            WarehouseLocation.warehouse_id == row.warehouse_id,
            WarehouseLocation.code == payload.code,
            WarehouseLocation.id != row.id,
        )
    ):
        raise HTTPException(409, "El código ya está utilizado en el almacén.")

    occupied = db.scalar(
        select(func.coalesce(func.sum(LocationStock.quantity), 0)).where(
            LocationStock.company_id == current_user.company_id, LocationStock.location_id == row.id
        )
    )

    has_serials = db.scalar(
        select(InventorySerial.id).where(
            InventorySerial.company_id == current_user.company_id,
            InventorySerial.location_id == row.id,
            InventorySerial.status == "IN_STOCK",
        )
    )

    if not payload.is_active and (occupied or has_serials):
        raise HTTPException(409, "Traslada las existencias y series antes de desactivar esta ubicación.")

    if payload.capacity_units < occupied:
        raise HTTPException(409, "La capacidad no puede ser menor que las existencias ubicadas.")

    for key, value in payload.model_dump().items():
        setattr(row, key, value)

    record_audit(db, current_user, row.id, "UPDATE_LOCATION", payload.model_dump(mode="json"))

    db.commit()

    return {"id": str(row.id), "is_active": row.is_active}


def transfer_location_stock(payload: LocationTransferRequest, current_user: AuthenticatedUser, db: Session):
    res = move_between_locations(
        db,
        current_user,
        payload.warehouse_id,
        payload.product_id,
        payload.from_location_id,
        payload.to_location_id,
        payload.quantity,
    )

    db.commit()

    return res
