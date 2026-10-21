import json
from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select

from salesia.modules.catalogo.infrastructure_models import ProductProfileModel
from salesia.modules.inventario.infrastructure_models import (
    InventoryLot,
    InventoryQuarantine,
    InventorySerial,
    LocationStock,
    WarehouseLocation,
)
from salesia.modules.inventario.service import (
    create_document,
    document,
    move_stock,
    product,
    record_audit,
    response,
    warehouse,
)
from salesia.shared.infrastructure.models import AttachmentModel


class ReceiptLot(BaseModel):
    lot_code: str = Field(min_length=1, max_length=64)
    quantity: Decimal = Field(gt=0, decimal_places=6)
    manufacture_date: Optional[date] = None
    expiration_date: Optional[date] = None

    @model_validator(mode="after")
    def valid_dates(self):
        self.lot_code = self.lot_code.strip()
        if not self.lot_code:
            raise ValueError("Escribe el código de lote")
        if self.manufacture_date and self.expiration_date and self.expiration_date < self.manufacture_date:
            raise ValueError("La caducidad no puede ser anterior a la fabricación")
        return self


class ReceiptLine(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(gt=0, decimal_places=6)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=6)
    inspection_status: Optional[Literal["accepted", "quarantine", "rejected"]] = None
    inspection_notes: Optional[str] = Field(default=None, max_length=1000)
    location_id: Optional[UUID] = None
    lots: list[ReceiptLot] = Field(default_factory=list, max_length=100)
    serial_numbers: list[str] = Field(default_factory=list, max_length=5000)

    @model_validator(mode="after")
    def valid_tracking(self):
        self.serial_numbers = [serial.strip() for serial in self.serial_numbers]
        if any(not serial or len(serial) > 128 for serial in self.serial_numbers) or len(
            set(self.serial_numbers)
        ) != len(self.serial_numbers):
            raise ValueError("Las series deben ser distintas y tener entre 1 y 128 caracteres")
        if self.serial_numbers and (
            self.quantity != self.quantity.to_integral_value() or len(self.serial_numbers) != self.quantity
        ):
            raise ValueError("Ingresa una serie distinta por cada unidad recibida")
        if self.lots and (
            sum((lot.quantity for lot in self.lots), Decimal("0")) != self.quantity
            or len({lot.lot_code for lot in self.lots}) != len(self.lots)
        ):
            raise ValueError("Los lotes deben ser distintos y sumar la cantidad recibida")
        if self.lots and self.serial_numbers:
            raise ValueError("Registra el seguimiento por lotes o por series según el producto")
        return self


class GoodsReceiptCreateRequest(BaseModel):
    purchase_order_id: UUID
    warehouse_id: UUID
    order_version: Optional[int] = Field(default=None, ge=1)
    items: list[ReceiptLine] = Field(min_length=1, max_length=500)
    inspection_status: Literal["accepted", "quarantine", "rejected"] = "accepted"
    tolerance_percentage: Decimal = Field(default=Decimal("0.05"), ge=0, le=Decimal("0.50"))
    notes: Optional[str] = Field(default=None, max_length=2000)
    difference_reason: Optional[str] = Field(default=None, max_length=1000)
    attachment_ids: list[UUID] = Field(default_factory=list, max_length=20)


def add_location_quantity(db, company_id, warehouse_id, location_id, product_id, quantity):
    location = db.scalar(
        select(WarehouseLocation)
        .where(
            WarehouseLocation.id == location_id,
            WarehouseLocation.company_id == company_id,
            WarehouseLocation.warehouse_id == warehouse_id,
        )
        .with_for_update()
    )
    if not location or not location.is_active:
        raise HTTPException(409, "La ubicación no pertenece al almacén o está desactivada.")
    occupied = db.scalar(
        select(func.coalesce(func.sum(LocationStock.quantity), 0)).where(
            LocationStock.company_id == company_id, LocationStock.location_id == location.id
        )
    )
    if occupied + quantity > location.capacity_units:
        raise HTTPException(409, "La recepción supera la capacidad de la ubicación.")
    stock = db.scalar(
        select(LocationStock)
        .where(
            LocationStock.company_id == company_id,
            LocationStock.location_id == location_id,
            LocationStock.product_id == product_id,
        )
        .with_for_update()
    )
    if stock:
        stock.quantity += quantity
    else:
        db.add(
            LocationStock(
                company_id=company_id,
                warehouse_id=warehouse_id,
                location_id=location_id,
                product_id=product_id,
                quantity=quantity,
            )
        )
    db.flush()


def receive_purchase(db, user, payload):
    from salesia.modules.inventario.application.compras_saldos import capture_revision
    order = document(db, user, "PURCHASE_ORDER", payload.purchase_order_id)
    if order.warehouse_id != payload.warehouse_id or order.status not in (
        "submitted",
        "approved",
        "partially_received",
    ):
        raise HTTPException(409, "La orden no admite recepción en este almacén.")
    if payload.order_version is not None and order.version != payload.order_version:
        raise HTTPException(409, "La orden cambió. Actualiza los saldos antes de recibir.")
    warehouse(db, user.company_id, payload.warehouse_id, lock=True)
    attachments = (
        db.scalars(
            select(AttachmentModel).where(
                AttachmentModel.company_id == user.company_id, AttachmentModel.id.in_(payload.attachment_ids)
            )
        ).all()
        if payload.attachment_ids
        else []
    )
    if len(attachments) != len(set(payload.attachment_ids)) or any(
        not item.verified
        or item.scan_status != "clean"
        or item.related_entity_type != "purchase_order"
        or item.related_entity_id != order.id
        for item in attachments
    ):
        raise HTTPException(422, "Adjunta únicamente archivos verificados de esta orden de compra.")
    capture_revision(db, user, order, "BEFORE_RECEIPT", "Estado anterior a recepción")
    ordered = {line.product_id: line for line in order.lines}
    inspections = []
    states = {item.inspection_status or payload.inspection_status for item in payload.items}
    receipt = create_document(
        db,
        user,
        "GOODS_RECEIPT",
        next(iter(states)) if len(states) == 1 else "mixed",
        payload.warehouse_id,
        payload.items,
        supplier_id=order.supplier_id,
        parent_id=order.id,
    )
    receipt_lines = {line.product_id: line for line in receipt.lines}
    for item in payload.items:
        source = ordered.get(item.product_id)
        if not source:
            raise HTTPException(409, "Producto no presente en la orden.")
        status = item.inspection_status or payload.inspection_status
        if source.processed_quantity + item.quantity > (
            (source.quantity - source.cancelled_quantity) * (Decimal("1") + payload.tolerance_percentage)
        ).quantize(Decimal("0.000001")):
            raise HTTPException(409, "La recepción supera el saldo y la tolerancia autorizada de la orden.")
        if item.unit_cost != source.unit_cost:
            raise HTTPException(409, "El costo no coincide con la orden.")
        if (
            payload.order_version is not None
            and source.processed_quantity + item.quantity > source.quantity - source.cancelled_quantity
            and len((payload.difference_reason or "").strip()) < 3
        ):
            raise HTTPException(422, "Explica la diferencia antes de recibir cantidades adicionales.")
        if item.inspection_status and status != "accepted" and len((item.inspection_notes or "").strip()) < 3:
            raise HTTPException(422, "Registra el motivo de cuarentena o rechazo por artículo.")
        prod = product(db, user.company_id, item.product_id)
        profile = db.scalar(
            select(ProductProfileModel).where(
                ProductProfileModel.company_id == user.company_id, ProductProfileModel.product_id == prod.id
            )
        )
        tracking = profile.tracking_mode if profile else "NONE"
        if tracking == "LOT" and not item.lots:
            raise HTTPException(422, f"El producto {prod.sku} requiere lotes y sus cantidades.")
        if tracking == "SERIAL" and not item.serial_numbers:
            raise HTTPException(422, f"El producto {prod.sku} requiere una serie por unidad.")
        if item.location_id and not db.scalar(
            select(WarehouseLocation.id).where(
                WarehouseLocation.id == item.location_id,
                WarehouseLocation.company_id == user.company_id,
                WarehouseLocation.warehouse_id == payload.warehouse_id,
                WarehouseLocation.is_active.is_(True),
            )
        ):
            raise HTTPException(422, "Selecciona una ubicación activa del almacén de la orden.")
        lots = []
        for allocation in item.lots:
            lot = db.scalar(
                select(InventoryLot)
                .where(
                    InventoryLot.company_id == user.company_id,
                    InventoryLot.product_id == prod.id,
                    InventoryLot.lot_code == allocation.lot_code,
                )
                .with_for_update()
            )
            if lot:
                if lot.supplier_id and lot.supplier_id != order.supplier_id:
                    raise HTTPException(409, "El lote ya pertenece a otro proveedor.")
                for field in ("manufacture_date", "expiration_date"):
                    existing = getattr(lot, field)
                    supplied = getattr(allocation, field)
                    if supplied and existing and existing.date() != supplied:
                        raise HTTPException(409, "Las fechas del lote no coinciden con el lote existente.")
                    if supplied and not existing:
                        setattr(lot, field, datetime.combine(supplied, time.min, timezone.utc))
            else:
                lot = InventoryLot(
                    company_id=user.company_id,
                    product_id=prod.id,
                    lot_code=allocation.lot_code,
                    supplier_id=order.supplier_id,
                    manufacture_date=datetime.combine(allocation.manufacture_date, time.min, timezone.utc)
                    if allocation.manufacture_date
                    else None,
                    expiration_date=datetime.combine(allocation.expiration_date, time.min, timezone.utc)
                    if allocation.expiration_date
                    else None,
                )
                db.add(lot)
                db.flush()
            if status == "accepted" and (
                lot.status != "ACTIVE"
                or lot.expiration_date
                and lot.expiration_date.date() < datetime.now(timezone.utc).date()
            ):
                raise HTTPException(409, "Un lote bloqueado o vencido debe quedar en cuarentena o rechazarse.")
            lots.append(
                {
                    "lot_id": str(lot.id),
                    "lot_code": lot.lot_code,
                    "quantity": str(allocation.quantity),
                    "manufacture_date": lot.manufacture_date.isoformat() if lot.manufacture_date else None,
                    "expiration_date": lot.expiration_date.isoformat() if lot.expiration_date else None,
                }
            )
        if item.serial_numbers:
            if db.scalar(
                select(InventorySerial.id).where(
                    InventorySerial.company_id == user.company_id,
                    InventorySerial.product_id == prod.id,
                    InventorySerial.serial_number.in_(item.serial_numbers),
                )
            ):
                raise HTTPException(
                    409, "Una de las series ya está registrada. Revisa la recepción para evitar duplicados."
                )
            db.add_all(
                [
                    InventorySerial(
                        company_id=user.company_id,
                        product_id=prod.id,
                        serial_number=serial,
                        warehouse_id=payload.warehouse_id,
                        location_id=item.location_id,
                        status={"accepted": "IN_STOCK", "quarantine": "IN_QUARANTINE", "rejected": "REJECTED"}[status],
                        current_doc_type="GOODS_RECEIPT",
                        current_doc_id=receipt.id,
                    )
                    for serial in item.serial_numbers
                ]
            )
        receipt_line = receipt_lines[prod.id]
        receipt_line.processed_quantity = item.quantity if status != "rejected" else Decimal("0")
        receipt_line.damaged_quantity = item.quantity if status == "rejected" else Decimal("0")
        if status == "accepted":
            move_stock(
                db,
                user.company_id,
                payload.warehouse_id,
                prod.id,
                item.quantity,
                source.unit_cost,
                receipt.id,
                "COMPRA",
            )
            if item.location_id:
                add_location_quantity(
                    db, user.company_id, payload.warehouse_id, item.location_id, prod.id, item.quantity
                )
            source.processed_quantity += item.quantity
        elif status == "quarantine":
            db.add(
                InventoryQuarantine(
                    company_id=user.company_id,
                    warehouse_id=payload.warehouse_id,
                    product_id=prod.id,
                    quantity=item.quantity,
                    reason="RECEIPT_INSPECTION",
                    status="IN_QUARANTINE",
                    reference_doc_type="GOODS_RECEIPT",
                    reference_doc_id=receipt.id,
                )
            )
            source.processed_quantity += item.quantity
        else:
            source.damaged_quantity += item.quantity
        inspections.append(
            {
                "product_id": str(prod.id),
                "product_name": prod.name,
                "sku": prod.sku,
                "quantity": str(item.quantity),
                "unit_cost": str(source.unit_cost),
                "status": status,
                "notes": item.inspection_notes,
                "location_id": str(item.location_id) if item.location_id else None,
                "lots": lots,
                "serial_numbers": item.serial_numbers,
                "pending_quantity": str(max(Decimal("0"), source.quantity - source.processed_quantity - source.cancelled_quantity)),
            }
        )
    order.status = (
        "received" if all(line.processed_quantity + line.cancelled_quantity >= line.quantity for line in order.lines) else "partially_received"
    )
    order.version += 1
    capture_revision(db, user, order, "RECEIVE", payload.notes or "Recepción de compra registrada")
    receipt.details_json = json.dumps(
        {
            "order_version": payload.order_version,
            "inspected_by": str(user.user_id),
            "notes": payload.notes,
            "difference_reason": payload.difference_reason,
            "inspections": inspections,
            "attachments": [
                {"id": str(item.id), "file_name": item.file_name, "mime_type": item.mime_type} for item in attachments
            ],
        }
    )
    record_audit(
        db,
        user,
        receipt.id,
        "RECEIVE_PURCHASE",
        {
            "purchase_order_id": str(order.id),
            "inspection_count": len(inspections),
            "attachments": [str(item.id) for item in attachments],
            "status": receipt.status,
        },
    )
    db.flush()
    from salesia.modules.inventario.application.reclamos_proveedor import synchronize_replacement_order
    synchronize_replacement_order(db, user, order)
    return response(receipt)


def release_receipt_quarantine(db, user, item, restock):
    receipt = document(db, user, "GOODS_RECEIPT", item.reference_doc_id)
    details = json.loads(receipt.details_json or "{}")
    inspection = next(
        (line for line in details.get("inspections", []) if line["product_id"] == str(item.product_id)), None
    )
    source_line = next((line for line in receipt.lines if line.product_id == item.product_id), None)
    if not source_line:
        raise HTTPException(409, "La cuarentena no tiene una línea de recepción válida.")
    warehouse(db, user.company_id, item.warehouse_id, lock=True)
    if restock:
        for allocation in inspection.get("lots", []) if inspection else []:
            lot = db.scalar(
                select(InventoryLot)
                .where(InventoryLot.id == UUID(allocation["lot_id"]), InventoryLot.company_id == user.company_id)
                .with_for_update()
            )
            if (
                not lot
                or lot.status != "ACTIVE"
                or lot.expiration_date
                and lot.expiration_date.date() < datetime.now(timezone.utc).date()
            ):
                raise HTTPException(409, "No se puede liberar un lote bloqueado o vencido.")
        move_stock(
            db,
            user.company_id,
            item.warehouse_id,
            item.product_id,
            item.quantity,
            source_line.unit_cost,
            item.id,
            "CUARENTENA_LIBERADA",
        )
        if inspection and inspection.get("location_id"):
            add_location_quantity(
                db, user.company_id, item.warehouse_id, UUID(inspection["location_id"]), item.product_id, item.quantity
            )
    serials = db.scalars(
        select(InventorySerial)
        .where(
            InventorySerial.company_id == user.company_id,
            InventorySerial.product_id == item.product_id,
            InventorySerial.current_doc_id == receipt.id,
            InventorySerial.status == "IN_QUARANTINE",
        )
        .with_for_update()
    ).all()
    for serial in serials:
        serial.status = "IN_STOCK" if restock else "SCRAPPED"
    if inspection:
        inspection["resolution"] = "RESTOCK" if restock else "SCRAP"
        inspection["resolved_at"] = datetime.now(timezone.utc).isoformat()
        inspection["resolved_by"] = str(user.user_id)
        receipt.details_json = json.dumps(details)
    record_audit(
        db,
        user,
        item.id,
        "CLASSIFY_PURCHASE_QUARANTINE",
        {
            "receipt_id": str(receipt.id),
            "action": "RESTOCK" if restock else "SCRAP",
            "quantity": str(item.quantity),
            "serials": len(serials),
        },
    )

    from salesia.modules.inventario.application.reclamos_proveedor import synchronize_replacement_order
    source_order = document(db, user, "PURCHASE_ORDER", receipt.parent_id, lock=False)
    synchronize_replacement_order(db, user, source_order)
