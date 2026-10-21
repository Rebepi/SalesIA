import json

from fastapi import HTTPException
from sqlalchemy import select

from salesia.modules.inventario.infrastructure_models import (
    InventoryLot,
    InventoryQuarantine,
    InventorySerial,
    SupplyDocument,
    SupplyLine,
    WarehouseLocation,
)
from salesia.shared.infrastructure.models import AuditLogModel, ProductModel, WarehouseModel


def tracking_trace(db, user, kind, resource_id):
    model = InventoryLot if kind == "lot" else InventorySerial
    tracked = db.scalar(select(model).where(model.company_id == user.company_id, model.id == resource_id))
    if not tracked:
        raise HTTPException(404, "Lote o serie no encontrado.")
    prod = db.scalar(
        select(ProductModel).where(ProductModel.id == tracked.product_id, ProductModel.company_id == user.company_id)
    )
    warehouses = {
        row.id: row.name
        for row in db.scalars(select(WarehouseModel).where(WarehouseModel.company_id == user.company_id)).all()
    }
    events = [
        {
            "id": f"created-{tracked.id}",
            "date": tracked.created_at.isoformat(),
            "title": "Lote registrado" if kind == "lot" else "Serie registrada",
            "quantity": None,
            "warehouse": warehouses.get(getattr(tracked, "warehouse_id", None)),
            "details": "Registro de control de inventario",
        }
    ]
    receipts = db.scalars(
        select(SupplyDocument)
        .join(SupplyLine, SupplyLine.document_id == SupplyDocument.id)
        .where(
            SupplyDocument.company_id == user.company_id,
            SupplyDocument.kind == "GOODS_RECEIPT",
            SupplyLine.product_id == tracked.product_id,
        )
        .order_by(SupplyDocument.created_at.desc())
        .limit(201)
    ).all()
    related_ids = {resource_id}
    for receipt in receipts[:200]:
        details = json.loads(receipt.details_json or "{}")
        for inspection in details.get("inspections", []):
            if inspection["product_id"] != str(tracked.product_id):
                continue
            allocation = (
                next((lot for lot in inspection.get("lots", []) if lot.get("lot_id") == str(resource_id)), None)
                if kind == "lot"
                else None
            )
            if (
                kind == "lot"
                and not allocation
                or kind == "serial"
                and tracked.serial_number not in inspection.get("serial_numbers", [])
            ):
                continue
            related_ids.add(receipt.id)
            quarantines = db.scalars(
                select(InventoryQuarantine.id).where(
                    InventoryQuarantine.company_id == user.company_id,
                    InventoryQuarantine.reference_doc_type == "GOODS_RECEIPT",
                    InventoryQuarantine.reference_doc_id == receipt.id,
                    InventoryQuarantine.product_id == tracked.product_id,
                )
            ).all()
            related_ids.update(quarantines)
            events.append(
                {
                    "id": f"receipt-{receipt.id}",
                    "date": receipt.created_at.isoformat(),
                    "title": {
                        "accepted": "Recepción aceptada",
                        "quarantine": "Recepción retenida en cuarentena",
                        "rejected": "Recepción rechazada",
                    }.get(inspection["status"], "Recepción de compra"),
                    "quantity": allocation["quantity"] if allocation else "1",
                    "warehouse": warehouses.get(receipt.warehouse_id, "Almacén no disponible"),
                    "details": inspection.get("notes") or "",
                    "receipt_id": str(receipt.id),
                    "purchase_order_id": str(receipt.parent_id),
                }
            )
    return_documents = db.scalars(
        select(SupplyDocument).where(
            SupplyDocument.company_id == user.company_id,
            SupplyDocument.kind == "PURCHASE_RETURN",
            SupplyDocument.parent_id.in_(related_ids),
        )
    ).all()
    for returned in return_documents:
        details = json.loads(returned.details_json or "{}")
        allocation = (
            next((line for line in details.get("tracking", []) if line.get("lot_id") == str(resource_id)), None)
            if kind == "lot"
            else None
        )
        if (
            kind == "lot"
            and not allocation
            or kind == "serial"
            and tracked.serial_number not in details.get("serial_numbers", [])
        ):
            continue
        related_ids.add(returned.id)
        events.append(
            {
                "id": f"return-{returned.id}",
                "date": returned.created_at.isoformat(),
                "title": "Devolución al proveedor",
                "quantity": allocation["quantity"] if allocation else "1",
                "warehouse": warehouses.get(returned.warehouse_id),
                "details": details.get("reason") or "",
            }
        )
    labels = {
        "BLOCK_LOT": "Lote bloqueado",
        "SELL_SERIAL": "Serie vinculada a una venta",
        "CREATE_SERIAL": "Serie registrada",
        "CREATE_LOT": "Lote registrado",
        "CLASSIFY_PURCHASE_QUARANTINE": "Inspección de cuarentena resuelta",
    }
    logs = db.scalars(
        select(AuditLogModel)
        .where(
            AuditLogModel.company_id == user.company_id,
            AuditLogModel.entity_id.in_(related_ids),
            AuditLogModel.action.notin_(("RECEIVE_PURCHASE", "RETURN_PURCHASE")),
        )
        .order_by(AuditLogModel.created_at.desc())
        .limit(200)
    ).all()
    for log in logs:
        payload = json.loads(log.payload_diff or "{}")
        if log.action == "CLASSIFY_PURCHASE_QUARANTINE":
            title = (
                "Cuarentena liberada a stock"
                if payload.get("action") == "RESTOCK"
                else "Artículo descartado tras inspección"
            )
        else:
            title = labels.get(log.action, "Cambio registrado en inventario")
        events.append(
            {
                "id": str(log.id),
                "date": log.created_at.isoformat(),
                "title": title,
                "code": log.action,
                "quantity": payload.get("quantity"),
                "details": "",
                "warehouse": None,
            }
        )
    location = (
        db.scalar(
            select(WarehouseLocation.code).where(
                WarehouseLocation.id == tracked.location_id, WarehouseLocation.company_id == user.company_id
            )
        )
        if kind == "serial" and tracked.location_id
        else None
    )
    return {
        "kind": kind,
        "code": tracked.lot_code if kind == "lot" else tracked.serial_number,
        "product_name": prod.name if prod else "Producto no disponible",
        "sku": prod.sku if prod else "",
        "status": tracked.status,
        "warehouse": warehouses.get(tracked.warehouse_id) if kind == "serial" else None,
        "location": location,
        "expiration_date": tracked.expiration_date.isoformat() if kind == "lot" and tracked.expiration_date else None,
        "events": sorted(events, key=lambda item: item["date"], reverse=True),
        "truncated": len(receipts) > 200 or len(logs) == 200,
        "coverage": "Recepciones con seguimiento y acciones registradas. Los movimientos históricos sin lote o serie no se atribuyen a este registro.",
    }
