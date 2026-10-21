import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.inventario.application.contracts.conteos import CountEntriesRequest, PhysicalCountRequest
from salesia.modules.inventario.infrastructure_models import PhysicalCountSession
from salesia.modules.inventario.service import (
    approve_physical_count_session,
    create_document,
    create_physical_count_session,
    document,
    move_stock,
    record_audit,
    response,
    transition,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import InventoryStockModel, ProductModel, WarehouseModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def list_counts(
    warehouse_id: Optional[UUID],
    status: Optional[str],
    limit: int,
    offset: int,
    current_user: AuthenticatedUser,
    db: Session,
):
    filters = [PhysicalCountSession.company_id == current_user.company_id]

    if warehouse_id:
        filters.append(PhysicalCountSession.warehouse_id == warehouse_id)

    if status:
        filters.append(PhysicalCountSession.status == status)

    rows = db.scalars(
        select(PhysicalCountSession)
        .where(*filters)
        .order_by(PhysicalCountSession.cutoff_date.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    items = [
        {
            "id": str(row.id),
            "warehouse_id": str(row.warehouse_id),
            "status": row.status,
            "count_code": row.count_code,
            "version": row.version,
            "is_blind": row.is_blind,
            "notes": row.notes,
            "cutoff_at": row.cutoff_date.isoformat(),
            "created_at": row.created_at.isoformat(),
            "lines": [
                {
                    "id": str(line.id),
                    "product_id": str(line.product_id),
                    "counted_quantity": str(line.counted_quantity),
                    "counted_at": line.counted_at.isoformat() if line.counted_at else None,
                    "snapshot_system_quantity": str(line.system_quantity_snapshot)
                    if not row.is_blind or row.status in ("pending_approval", "approved")
                    else None,
                    "discrepancy_quantity": str(line.difference_quantity)
                    if not row.is_blind or row.status in ("pending_approval", "approved")
                    else None,
                }
                for line in row.lines
            ],
        }
        for row in rows
    ]

    return {"items": items, "count": len(items)}


def create_stock_count(payload: PhysicalCountRequest, current_user: AuthenticatedUser, db: Session):
    wh = db.scalar(
        select(WarehouseModel).where(
            WarehouseModel.id == payload.warehouse_id,
            WarehouseModel.company_id == current_user.company_id,
            WarehouseModel.is_active.is_(True),
        )
    )

    if not wh:
        raise HTTPException(422, "Almacén no encontrado o de otra empresa.")

    count_code = f"CNT-{uuid4().hex[:6].upper()}"

    if payload.items and payload.product_ids:
        raise HTTPException(422, "Selecciona productos o envía cantidades iniciales, no ambos.")

    product_ids = [item.product_id for item in payload.items] if payload.items else payload.product_ids

    if product_ids:
        if len(set(product_ids)) != len(product_ids):
            raise HTTPException(422, "No repitas productos en el alcance del conteo.")

        found = db.scalars(
            select(ProductModel.id).where(
                ProductModel.company_id == current_user.company_id,
                ProductModel.id.in_(product_ids),
                ProductModel.is_active.is_(True),
            )
        ).all()

        if len(found) != len(product_ids):
            raise HTTPException(422, "Uno de los productos no está activo o no pertenece a la empresa.")

    session = create_physical_count_session(
        db,
        current_user,
        payload.warehouse_id,
        count_code,
        payload.scope,
        payload.scope_filter,
        payload.is_blind,
        product_ids,
        payload.notes,
    )

    if payload.items:
        line_dict = {item.product_id: item.quantity for item in payload.items}

        for l in session.lines:
            if l.product_id in line_dict:
                l.counted_quantity = line_dict[l.product_id]

                l.difference_quantity = l.counted_quantity - l.system_quantity_snapshot

                l.counted_at = datetime.now(timezone.utc)

    row_doc = create_document(
        db,
        current_user,
        "COUNT",
        "pending_approval",
        payload.warehouse_id,
        payload.items or [],
        details_json=json.dumps({"notes": payload.notes, "session_id": str(session.id)}),
    )

    db.commit()

    return {
        "id": str(session.id),
        "document_id": str(row_doc.id),
        "count_code": session.count_code,
        "warehouse_id": str(session.warehouse_id),
        "scope": session.scope,
        "cutoff_date": session.cutoff_date.isoformat(),
        "is_blind": session.is_blind,
        "status": session.status,
        "lines_count": len(session.lines),
        "lines": [
            {
                "product_id": str(l.product_id),
                "counted_quantity": str(l.counted_quantity),
                "difference_quantity": str(l.difference_quantity) if not session.is_blind else "0",
            }
            for l in session.lines
        ],
    }


def update_count_entries(count_id: UUID, payload: CountEntriesRequest, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(PhysicalCountSession)
        .where(PhysicalCountSession.id == count_id, PhysicalCountSession.company_id == current_user.company_id)
        .with_for_update()
    )

    if not row:
        raise HTTPException(404, "Conteo no encontrado.")

    if row.status not in ("in_progress", "pending_count"):
        raise HTTPException(409, "El conteo ya fue enviado a revisión o aprobado.")

    if row.version != payload.version:
        raise HTTPException(409, "El conteo cambió. Actualiza la pantalla antes de guardar.")

    entries = {entry.product_id: entry.quantity for entry in payload.items}

    if len(entries) != len(payload.items):
        raise HTTPException(422, "Hay productos repetidos en el conteo.")

    lines = {line.product_id: line for line in row.lines}

    if not entries.keys() <= lines.keys():
        raise HTTPException(422, "Uno de los productos no pertenece al alcance del conteo.")

    for product_id, quantity in entries.items():
        line = lines[product_id]

        line.counted_quantity = quantity

        line.difference_quantity = quantity - line.system_quantity_snapshot

        line.counted_at = datetime.now(timezone.utc)

    if payload.submit:
        if any(line.counted_at is None for line in row.lines):
            raise HTTPException(409, "Registra todos los productos antes de enviar a revisión.")

        row.status = "pending_approval"

    row.version += 1

    record_audit(
        db, current_user, row.id, "RECORD_PHYSICAL_COUNT", {"products": len(entries), "submitted": payload.submit}
    )

    db.commit()

    return {"id": str(row.id), "version": row.version, "status": row.status}


def approve_stock_count(count_id: UUID, current_user: AuthenticatedUser, db: Session, idempotency_key: str):
    record, cached = claim_request(
        db, current_user.company_id, "inventory.count.approve", idempotency_key, {"count_id": str(count_id)}
    )

    if cached is not None:
        return cached

    session = db.scalar(
        select(PhysicalCountSession).where(
            PhysicalCountSession.id == count_id, PhysicalCountSession.company_id == current_user.company_id
        )
    )

    if session:
        approved = approve_physical_count_session(db, current_user, count_id)

        result = {
            "id": str(approved.id),
            "count_code": approved.count_code,
            "status": approved.status,
            "approved_by": str(approved.approved_by),
            "approved_at": approved.approved_at.isoformat() if approved.approved_at else None,
            "lines_count": len(approved.lines),
        }

        complete_request(record, result)

        db.commit()

        return result

    row = document(db, current_user, "COUNT", count_id)

    if row.created_by == current_user.user_id:
        raise HTTPException(403, "El creador no puede aprobar el conteo.")

    if transition(db, row, {"pending_approval"}, "approved"):
        for line in row.lines:
            stock = db.scalar(
                select(InventoryStockModel)
                .where(
                    InventoryStockModel.company_id == row.company_id,
                    InventoryStockModel.warehouse_id == row.warehouse_id,
                    InventoryStockModel.product_id == line.product_id,
                )
                .with_for_update()
            )

            current = stock.physical_quantity if stock else Decimal("0")

            delta = line.quantity - current

            if delta:
                move_stock(
                    db,
                    row.company_id,
                    row.warehouse_id,
                    line.product_id,
                    delta,
                    line.unit_cost,
                    row.id,
                    "CONTEO_FISICO",
                )

            line.processed_quantity = line.quantity

        record_audit(db, current_user, row.id, "APPROVE_COUNT", {})

    db.flush()

    result = response(row)

    complete_request(record, result)

    db.commit()

    return result
