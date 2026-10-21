import json
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select, update

from salesia.modules.inventario.application.gestion_stock.consulta import product, warehouse
from salesia.modules.inventario.infrastructure_models import SupplyDocument, SupplyLine


def document(db, user, kind, document_id, lock=True):
    query = select(SupplyDocument).where(
        SupplyDocument.id == document_id, SupplyDocument.company_id == user.company_id, SupplyDocument.kind == kind
    )
    row = db.scalar(query.with_for_update() if lock else query)
    if not row:
        raise HTTPException(404, "Documento no encontrado.")
    return row


def transition(db, row, expected, target):
    if row.status == target:
        return False
    if row.status not in expected:
        raise HTTPException(409, "El estado actual no permite esta operación.")
    changed = db.execute(
        update(SupplyDocument)
        .where(SupplyDocument.id == row.id, SupplyDocument.version == row.version, SupplyDocument.status == row.status)
        .values(status=target, version=SupplyDocument.version + 1)
    )
    if changed.rowcount != 1:
        raise HTTPException(409, "El documento cambió; vuelva a consultar.")
    return True


def create_document(db, user, kind, status, warehouse_id, items=(), **values):
    warehouse(db, user.company_id, warehouse_id)
    from salesia.modules.catalogo.service import validate_unit_fraction
    for item in items:
        selected_product = product(db, user.company_id, item.product_id)
        validate_unit_fraction(db, user.company_id, selected_product.unit_of_measure, item.quantity)
    if len({item.product_id for item in items}) != len(items):
        raise HTTPException(422, "Agrupe cada producto en una sola línea.")
    row = SupplyDocument(
        id=uuid4(),
        company_id=user.company_id,
        kind=kind,
        status=status,
        version=1,
        warehouse_id=warehouse_id,
        created_by=user.user_id,
        **values,
    )
    row.lines = [
        SupplyLine(
            company_id=user.company_id,
            product_id=product(db, user.company_id, item.product_id).id,
            quantity=item.quantity,
            processed_quantity=Decimal("0"),
            damaged_quantity=Decimal("0"),
            unit_cost=item.unit_cost,
        )
        for item in items
    ]
    db.add(row)
    db.flush()
    return row


def response(row):
    lines_data = [
        {
            "product_id": str(line.product_id),
            "quantity": str(line.quantity),
            "processed_quantity": str(line.processed_quantity),
            "cancelled_quantity": str(line.cancelled_quantity or 0),
            "pending_quantity": str(max(Decimal("0"), line.quantity - line.processed_quantity - Decimal(line.cancelled_quantity or 0) - (line.damaged_quantity if row.kind == "TRANSFER" else Decimal("0")))),
            "damaged_quantity": str(line.damaged_quantity),
            "unit_cost": str(line.unit_cost),
        }
        for line in row.lines
    ]
    return {
        "id": str(row.id),
        "company_id": str(row.company_id),
        "kind": row.kind,
        "status": row.status,
        "version": row.version,
        "warehouse_id": str(row.warehouse_id),
        "source_warehouse_id": str(row.source_warehouse_id) if row.source_warehouse_id else None,
        "sale_id": str(row.sale_id) if row.sale_id else None,
        "supplier_id": str(row.supplier_id) if row.supplier_id else None,
        "supplier_claim_id": str(row.supplier_claim_id) if row.supplier_claim_id else None,
        "parent_id": str(row.parent_id) if row.parent_id else None,
        "created_at": row.created_at.isoformat(),
        "items_count": len(row.lines),
        "items": lines_data,
        "lines": lines_data,
        "details": json.loads(row.details_json) if row.details_json else {},
        "details_json": row.details_json or "{}",
    }
