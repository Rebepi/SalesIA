import json
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from salesia.modules.inventario.application.contracts.transferencias import (
    TransferCreateRequest,
    TransferReceiveRequest,
)
from salesia.modules.inventario.infrastructure_models import InventoryQuarantine, SupplyDocument
from salesia.modules.inventario.service import create_document, document, move_stock, record_audit, response, transition
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import WarehouseModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def list_transfers(
    warehouse_id: Optional[UUID],
    status: Optional[str],
    limit: int,
    offset: int,
    current_user: AuthenticatedUser,
    db: Session,
):
    filters = [SupplyDocument.company_id == current_user.company_id, SupplyDocument.kind == "TRANSFER"]

    if warehouse_id:
        filters.append(
            or_(SupplyDocument.warehouse_id == warehouse_id, SupplyDocument.source_warehouse_id == warehouse_id)
        )

    if status:
        filters.append(SupplyDocument.status == status)

    rows = db.scalars(
        select(SupplyDocument).where(*filters).order_by(SupplyDocument.created_at.desc()).offset(offset).limit(limit)
    ).all()

    items = []

    for row in rows:
        r = response(row)

        r["destination_warehouse_id"] = r["warehouse_id"]

        r["document_number"] = r.get("document_number") or str(row.id)[:8].upper()

        items.append(r)

    return {"items": items, "count": len(items)}


def create_transfer(payload: TransferCreateRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: str):
    record, cached = claim_request(
        db, current_user.company_id, "inventory.transfer.create", idempotency_key, payload.model_dump(mode="json")
    )

    if cached is not None:
        return cached

    wh_src = db.scalar(
        select(WarehouseModel).where(
            WarehouseModel.id == payload.source_warehouse_id,
            WarehouseModel.company_id == current_user.company_id,
            WarehouseModel.is_active.is_(True),
        )
    )

    if not wh_src:
        raise HTTPException(422, "Almacén origen inexistente o de otra empresa.")

    wh_dst = db.scalar(
        select(WarehouseModel).where(
            WarehouseModel.id == payload.destination_warehouse_id,
            WarehouseModel.company_id == current_user.company_id,
            WarehouseModel.is_active.is_(True),
        )
    )

    if not wh_dst:
        raise HTTPException(422, "Almacén destino inexistente o de otra empresa.")

    row = create_document(
        db,
        current_user,
        "TRANSFER",
        "draft",
        payload.destination_warehouse_id,
        payload.items,
        source_warehouse_id=payload.source_warehouse_id,
        details_json=json.dumps({"notes": payload.notes}),
    )

    result = response(row)

    complete_request(record, result)

    db.commit()

    return result


def dispatch_transfer(transfer_id: UUID, current_user: AuthenticatedUser, db: Session, idempotency_key: str):
    record, cached = claim_request(
        db, current_user.company_id, "inventory.transfer.dispatch", idempotency_key, {"transfer_id": str(transfer_id)}
    )

    if cached is not None:
        return cached

    row = document(db, current_user, "TRANSFER", transfer_id)

    if transition(db, row, {"draft"}, "in_transit"):
        for line in row.lines:
            move_stock(
                db,
                row.company_id,
                row.source_warehouse_id,
                line.product_id,
                -line.quantity,
                line.unit_cost,
                row.id,
                "TRANSFERENCIA_SALIDA",
            )

            line.processed_quantity = Decimal("0")

            line.damaged_quantity = Decimal("0")

        record_audit(db, current_user, row.id, "DISPATCH_TRANSFER", {})

    db.flush()

    result = response(row)

    complete_request(record, result)

    db.commit()

    return result


def receive_transfer(
    transfer_id: UUID,
    payload: Optional[TransferReceiveRequest],
    current_user: AuthenticatedUser,
    db: Session,
    idempotency_key: str,
):
    body_data = payload.model_dump(mode="json") if payload else {}

    body_data["transfer_id"] = str(transfer_id)

    record, cached = claim_request(
        db, current_user.company_id, "inventory.transfer.receive", idempotency_key, body_data
    )

    if cached is not None:
        return cached

    row = document(db, current_user, "TRANSFER", transfer_id)

    if row.status not in ("in_transit", "partially_received", "received"):
        raise HTTPException(409, "La transferencia no está en estado de tránsito.")

    if row.status == "received":
        result = response(row)

        complete_request(record, result)

        db.commit()

        return result

    line_map = {line.product_id: line for line in row.lines}

    if payload and payload.items:
        for item in payload.items:
            line = line_map.get(item.product_id)

            if not line:
                raise HTTPException(409, "Producto no presente en la transferencia.")

            remaining = line.quantity - line.processed_quantity - line.damaged_quantity

            if item.quantity_received + item.quantity_damaged > remaining:
                raise HTTPException(409, "La cantidad a recibir o dañar supera el saldo en tránsito.")

            if item.quantity_received > 0:
                move_stock(
                    db,
                    row.company_id,
                    row.warehouse_id,
                    line.product_id,
                    item.quantity_received,
                    line.unit_cost,
                    row.id,
                    "TRANSFERENCIA_ENTRADA",
                )

                line.processed_quantity += item.quantity_received

            if item.quantity_damaged > 0:
                line.damaged_quantity += item.quantity_damaged

                db.add(
                    InventoryQuarantine(
                        id=uuid4(),
                        company_id=row.company_id,
                        warehouse_id=row.warehouse_id,
                        product_id=line.product_id,
                        quantity=item.quantity_damaged,
                        reason="DAMAGED_IN_TRANSIT",
                        status="IN_QUARANTINE",
                        reference_doc_type="TRANSFER",
                        reference_doc_id=row.id,
                        resolution_notes=payload.notes or "Daño durante transferencia",
                    )
                )

    else:
        for line in row.lines:
            remaining = line.quantity - line.processed_quantity - line.damaged_quantity

            if remaining > 0:
                move_stock(
                    db,
                    row.company_id,
                    row.warehouse_id,
                    line.product_id,
                    remaining,
                    line.unit_cost,
                    row.id,
                    "TRANSFERENCIA_ENTRADA",
                )

                line.processed_quantity += remaining

    all_done = all((line.processed_quantity + line.damaged_quantity == line.quantity) for line in row.lines)

    row.status = "received" if all_done else "partially_received"

    row.version += 1

    record_audit(
        db,
        current_user,
        row.id,
        "RECEIVE_TRANSFER",
        {"status": row.status, "notes": payload.notes if payload else None},
    )

    db.flush()

    result = response(row)

    complete_request(record, result)

    db.commit()

    return result


def cancel_transfer(transfer_id: UUID, current_user: AuthenticatedUser, db: Session, idempotency_key: str):
    record, cached = claim_request(
        db, current_user.company_id, "inventory.transfer.cancel", idempotency_key, {"transfer_id": str(transfer_id)}
    )

    if cached is not None:
        return cached

    row = document(db, current_user, "TRANSFER", transfer_id)

    if row.status == "cancelled":
        result = response(row)

        complete_request(record, result)

        db.commit()

        return result

    if row.status not in ("draft", "in_transit"):
        raise HTTPException(409, "Solo se pueden cancelar transferencias en borrador o en tránsito.")

    if row.status == "in_transit":
        for line in row.lines:
            move_stock(
                db,
                row.company_id,
                row.source_warehouse_id,
                line.product_id,
                line.quantity,
                line.unit_cost,
                row.id,
                "TRANSFERENCIA_CANCELADA",
            )

    row.status = "cancelled"

    row.version += 1

    record_audit(db, current_user, row.id, "CANCEL_TRANSFER", {})

    db.flush()

    result = response(row)

    complete_request(record, result)

    db.commit()

    return result
