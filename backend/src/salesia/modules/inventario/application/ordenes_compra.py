import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.catalogo.infrastructure_models import ProductProfileModel
from salesia.modules.inventario.application.compras_saldos import capture_revision, pending_quantity
from salesia.modules.inventario.application.auxiliares.purchase_line_values import purchase_line_values
from salesia.modules.inventario.application.contracts.comunes import (
    PurchaseOrderCreateRequest,
    PurchaseOrderUpdateRequest,
    PurchaseReturnCreateRequest,
    StockLine,
    ThreeWayMatchResolveRequest,
)
from salesia.modules.inventario.infrastructure_models import (
    InventorySerial,
    LocationStock,
    PurchaseInvoiceMatch,
    Supplier,
    SupplyDocument,
    SupplyLine,
    WarehouseLocation,
)
from salesia.modules.inventario.service import (
    create_document,
    document,
    move_stock,
    product,
    record_audit,
    response,
    transition,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import ProductModel, WarehouseModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def create_purchase_order(
    payload: PurchaseOrderCreateRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: str
):
    record, cached = claim_request(
        db, current_user.company_id, "purchase_order.create", idempotency_key, payload.model_dump(mode="json")
    )

    if cached is not None:
        return cached

    supplier = db.scalar(
        select(Supplier).where(
            Supplier.id == payload.supplier_id,
            Supplier.company_id == current_user.company_id,
            Supplier.is_active.is_(True),
        )
    )

    if not supplier:
        raise HTTPException(422, "Proveedor inexistente o inactivo.")

    from salesia.modules.inventario.application.homologacion_proveedor import require_supplier_qualified
    require_supplier_qualified(db, current_user, supplier)
    source = (
        document(db, current_user, "PURCHASE_REQUISITION", payload.source_requisition_id)
        if payload.source_requisition_id
        else None
    )

    if source:
        if source.status != "approved":
            raise HTTPException(409, "La requisición debe estar aprobada y no convertida.")

        if payload.source_version != source.version:
            raise HTTPException(409, "La requisición cambió. Vuelve a consultarla antes de convertir.")

        expected = {line.product_id: line.quantity for line in source.lines}

        received = {line.product_id: line.quantity for line in payload.items}

        if source.warehouse_id != payload.warehouse_id or expected != received:
            raise HTTPException(422, "Conserva el almacén, los productos y las cantidades de la requisición aprobada.")

    from salesia.modules.inventario.application.catalogo_proveedor import purchase_catalog_snapshot
    catalog_snapshot = purchase_catalog_snapshot(db, current_user, supplier.id, payload.currency, payload.items)
    items, totals = purchase_line_values(payload.items)

    details = {
        "currency": payload.currency,
        "supplier_catalog_snapshot": catalog_snapshot,
        "payment_terms_days": payload.payment_terms_days,
        "delivery_date": payload.delivery_date.isoformat() if payload.delivery_date else None,
        "notes": payload.notes,
        **totals,
    }

    if source:
        details["source_requisition_id"] = str(source.id)

    row = create_document(
        db,
        current_user,
        "PURCHASE_ORDER",
        "submitted",
        payload.warehouse_id,
        items,
        supplier_id=supplier.id,
        parent_id=source.id if source else None,
        details_json=json.dumps(details),
    )

    if source:
        transition(db, source, {"approved"}, "converted")

        source.details_json = json.dumps({**json.loads(source.details_json or "{}"), "purchase_order_id": str(row.id)})

        record_audit(
            db,
            current_user,
            source.id,
            "CONVERT_REQUISITION",
            {"purchase_order_id": str(row.id), "supplier_id": str(supplier.id)},
        )

    record_audit(
        db,
        current_user,
        row.id,
        "CREATE_PURCHASE_ORDER",
        {
            "source_requisition_id": str(source.id) if source else None,
            "lines": len(items),
            "currency": payload.currency,
            "total": totals["total"],
        },
    )

    capture_revision(db, current_user, row, "CREATE", "Orden de compra creada")
    result = response(row)

    complete_request(record, result)

    db.commit()

    return result


def list_purchase_orders(
    supplier_id: Optional[UUID],
    warehouse_id: Optional[UUID],
    status: Optional[str],
    limit: int,
    offset: int,
    current_user: AuthenticatedUser,
    db: Session,
):
    query = select(SupplyDocument).where(
        SupplyDocument.company_id == current_user.company_id, SupplyDocument.kind == "PURCHASE_ORDER"
    )

    if supplier_id:
        query = query.where(SupplyDocument.supplier_id == supplier_id)

    if warehouse_id:
        query = query.where(SupplyDocument.warehouse_id == warehouse_id)

    if status:
        query = query.where(SupplyDocument.status == status)

    rows = db.scalars(query.order_by(SupplyDocument.created_at.desc()).offset(offset).limit(limit)).all()

    return {"items": [response(r) for r in rows], "count": len(rows)}


def get_purchase_order(order_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = document(db, current_user, "PURCHASE_ORDER", order_id)

    return response(row)


def approve_purchase_order(order_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = document(db, current_user, "PURCHASE_ORDER", order_id)

    if row.status not in ("submitted", "reopened"):
        raise HTTPException(409, "La orden no está en estado pendiente de aprobación.")

    from salesia.modules.seguridad.application.separacion_funciones import enforce
    enforce(db, current_user, "purchase_order", [row.created_by], "SupplyDocument", row.id)
    from salesia.modules.inventario.application.homologacion_proveedor import require_supplier_qualified
    supplier = db.scalar(select(Supplier).where(Supplier.company_id == current_user.company_id, Supplier.id == row.supplier_id))
    require_supplier_qualified(db, current_user, supplier)
    total_amount = sum((l.quantity - l.cancelled_quantity) * l.unit_cost for l in row.lines)

    approval_threshold = Decimal("10000.00")

    if total_amount > approval_threshold:
        if not (
            "organization:manage" in current_user.permissions
            or "purchases:approve" in current_user.permissions
            or current_user.role in ("company_admin", "platform_admin")
        ):
            raise HTTPException(
                403, "Se requiere aprobación gerencial para órdenes de compra que superen el límite autorizado."
            )

    capture_revision(db, current_user, row, "BEFORE_APPROVAL", "Estado anterior a aprobación")
    row.status = "approved"

    row.version += 1

    capture_revision(db, current_user, row, "APPROVE", "Orden de compra aprobada")
    db.commit()

    return response(row)


def update_purchase_order(
    order_id: UUID, payload: PurchaseOrderUpdateRequest, current_user: AuthenticatedUser, db: Session, idempotency_key=None
):
    record, cached = claim_request(db, current_user.company_id, f"purchase_order.update:{order_id}", idempotency_key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    row = document(db, current_user, "PURCHASE_ORDER", order_id)

    if row.supplier_claim_id:
        raise HTTPException(409, "La orden es una reposición acordada sin nueva deuda. Ajusta su saldo desde el reclamo y conserva sus costos de referencia.")
    if row.version != payload.version:
        raise HTTPException(409, "La orden cambió; recarga antes de modificarla.")
    if row.status in ("partially_received", "received", "cancelled", "closed"):
        raise HTTPException(409, "No se puede modificar una orden que ya tiene recepciones o está cancelada.")

    if row.status == "approved" and not ({"purchases:approve", "approvals:manage", "organization:manage"} & set(current_user.permissions)):
        raise HTTPException(403, "Revisar una orden aprobada requiere autorización de compras o administración.")
    from salesia.modules.inventario.infrastructure.models.reclamos import SupplierClaimModel
    if db.scalar(select(SupplierClaimModel.id).where(SupplierClaimModel.company_id == current_user.company_id, SupplierClaimModel.purchase_order_id == row.id, SupplierClaimModel.status.notin_(("cancelled", "rejected")))):
        raise HTTPException(409, "La compra tiene reclamos vigentes. Conserva su evidencia y modifica únicamente los saldos pendientes autorizados.")
    capture_revision(db, current_user, row, "BEFORE_EDIT", "Estado anterior a corrección")
    if db.scalar(select(SupplyDocument.id).where(SupplyDocument.company_id == current_user.company_id, SupplyDocument.parent_id == row.id, SupplyDocument.kind == "GOODS_RECEIPT").limit(1)):
        raise HTTPException(409, "La orden ya tiene recepciones. Corrige el saldo mediante cancelación o una nueva orden vinculada.")
    was_approved = row.status == "approved"

    details = json.loads(row.details_json) if row.details_json else {}

    if payload.currency:
        if payload.currency != details.get("currency", "USD") and not payload.items:
            raise HTTPException(422, "Al cambiar la moneda, confirma nuevamente todas las líneas y sus costos.")
        details["currency"] = payload.currency

    if payload.payment_terms_days is not None:
        details["payment_terms_days"] = payload.payment_terms_days

    if "delivery_date" in payload.model_fields_set:
        details["delivery_date"] = payload.delivery_date.isoformat() if payload.delivery_date else None

    if payload.notes is not None:
        details["notes"] = payload.notes

    if payload.items:
        if len({item.product_id for item in payload.items}) != len(payload.items):
            raise HTTPException(422, "Agrupe cada producto en una sola línea.")

        if row.parent_id:
            parent = db.scalar(select(SupplyDocument).where(SupplyDocument.company_id == current_user.company_id, SupplyDocument.id == row.parent_id))
            if parent and parent.kind == "PURCHASE_AGREEMENT":
                raise HTTPException(409, "La liberación conserva los precios del acuerdo. Cancela el saldo y genera una nueva liberación para cambiar cantidades.")
            source = document(db, current_user, "PURCHASE_REQUISITION", row.parent_id)
            if {line.product_id: line.quantity for line in source.lines} != {item.product_id: item.quantity for item in payload.items}:
                raise HTTPException(422, "Las cantidades requieren una nueva requisición aprobada.")

        from salesia.modules.inventario.application.catalogo_proveedor import purchase_catalog_snapshot
        details["supplier_catalog_snapshot"] = purchase_catalog_snapshot(db, current_user, row.supplier_id, details.get("currency", "USD"), payload.items)
        normalized, totals = purchase_line_values(payload.items)

        details.update(totals)

        for old_line in list(row.lines):
            db.delete(old_line)

        db.flush()

        row.lines = [
            SupplyLine(
                company_id=current_user.company_id,
                product_id=product(db, current_user.company_id, item.product_id).id,
                quantity=item.quantity,
                processed_quantity=Decimal("0"),
                damaged_quantity=Decimal("0"),
                unit_cost=item.unit_cost,
            )
            for item in normalized
        ]

    row.details_json = json.dumps(details)

    row.version += 1

    if was_approved:
        row.status = "submitted"

    capture_revision(db, current_user, row, "EDIT", payload.reason)
    record_audit(db, current_user, row.id, "REVISE_PURCHASE_ORDER", {"version": row.version, "reason": payload.reason, "requires_approval": was_approved})
    result = response(row)
    complete_request(record, result)
    db.commit()
    return result


def get_purchase_order_timeline(order_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = document(db, current_user, "PURCHASE_ORDER", order_id)

    receipts = db.scalars(
        select(SupplyDocument).where(
            SupplyDocument.company_id == current_user.company_id,
            SupplyDocument.parent_id == row.id,
            SupplyDocument.kind == "GOODS_RECEIPT",
        )
    ).all()

    receipt_ids = [r.id for r in receipts]

    returns = []

    if receipt_ids:
        returns = db.scalars(
            select(SupplyDocument).where(
                SupplyDocument.company_id == current_user.company_id,
                SupplyDocument.parent_id.in_(receipt_ids),
                SupplyDocument.kind == "PURCHASE_RETURN",
            )
        ).all()

    matches = db.scalars(
        select(PurchaseInvoiceMatch).where(
            PurchaseInvoiceMatch.company_id == current_user.company_id, PurchaseInvoiceMatch.purchase_order_id == row.id
        )
    ).all()

    timeline = [
        {"stage": "CREATION", "status": "COMPLETED", "date": row.created_at.isoformat(), "version": 1},
        {
            "stage": "APPROVAL",
            "status": "COMPLETED" if row.status in ("approved", "partially_received", "received") else "PENDING",
            "version": row.version,
        },
    ]

    for rc in receipts:
        timeline.append(
            {"stage": "RECEIPT", "status": rc.status, "date": rc.created_at.isoformat(), "document_id": str(rc.id)}
        )

    for ret in returns:
        timeline.append(
            {"stage": "RETURN", "status": ret.status, "date": ret.created_at.isoformat(), "document_id": str(ret.id)}
        )

    for m in matches:
        timeline.append(
            {
                "stage": "INVOICE_MATCH",
                "status": m.status,
                "date": m.created_at.isoformat(),
                "invoice_number": m.invoice_number,
            }
        )

    all_received = all(pending_quantity(l) == 0 for l in row.lines) if row.lines else False

    next_step = (
        "APPROVE_ORDER"
        if row.status in ("submitted", "reopened")
        else "RECEIVE_GOODS"
        if row.status in ("approved", "partially_received") and not all_received
        else "MATCH_INVOICE"
        if all_received and not matches
        else "COMPLETED"
    )

    line_balances = [
        {
            "product_id": str(l.product_id),
            "ordered_quantity": str(l.quantity),
            "received_quantity": str(l.processed_quantity),
            "pending_quantity": str(pending_quantity(l)),
            "cancelled_quantity": str(l.cancelled_quantity),
            "unit_cost": str(l.unit_cost),
        }
        for l in row.lines
    ]

    return {
        "order_id": str(row.id),
        "status": row.status,
        "version": row.version,
        "timeline": timeline,
        "line_balances": line_balances,
        "next_recommended_step": next_step,
    }


def purchase_receiving_context(order_id: UUID, current_user: AuthenticatedUser, db: Session):
    order = document(db, current_user, "PURCHASE_ORDER", order_id, lock=False)

    wh = db.scalar(
        select(WarehouseModel).where(
            WarehouseModel.id == order.warehouse_id, WarehouseModel.company_id == current_user.company_id
        )
    )

    supplier = db.scalar(
        select(Supplier).where(Supplier.id == order.supplier_id, Supplier.company_id == current_user.company_id)
    )

    rows = db.execute(
        select(ProductModel, ProductProfileModel)
        .outerjoin(
            ProductProfileModel,
            (ProductProfileModel.product_id == ProductModel.id)
            & (ProductProfileModel.company_id == current_user.company_id),
        )
        .where(
            ProductModel.company_id == current_user.company_id,
            ProductModel.id.in_([line.product_id for line in order.lines]),
        )
    ).all()

    products = {prod.id: (prod, profile) for prod, profile in rows}

    locations = db.scalars(
        select(WarehouseLocation)
        .where(
            WarehouseLocation.company_id == current_user.company_id,
            WarehouseLocation.warehouse_id == order.warehouse_id,
            WarehouseLocation.is_active.is_(True),
        )
        .order_by(WarehouseLocation.code)
    ).all()

    receipts = db.scalars(
        select(SupplyDocument)
        .where(
            SupplyDocument.company_id == current_user.company_id,
            SupplyDocument.kind == "GOODS_RECEIPT",
            SupplyDocument.parent_id == order.id,
        )
        .order_by(SupplyDocument.created_at.desc())
    ).all()

    return_rows = (
        db.execute(
            select(SupplyDocument.parent_id, SupplyLine.product_id, func.sum(SupplyLine.quantity))
            .join(SupplyLine, SupplyLine.document_id == SupplyDocument.id)
            .where(
                SupplyDocument.company_id == current_user.company_id,
                SupplyDocument.kind == "PURCHASE_RETURN",
                SupplyDocument.parent_id.in_([receipt.id for receipt in receipts]),
            )
            .group_by(SupplyDocument.parent_id, SupplyLine.product_id)
        ).all()
        if receipts
        else []
    )

    returned = {(receipt_id, product_id): quantity for receipt_id, product_id, quantity in return_rows}

    receipt_data = []

    for receipt in receipts:
        data = response(receipt)

        inspections = {item["product_id"]: item for item in data["details"].get("inspections", [])}

        available = []

        for line in receipt.lines:
            inspection = inspections.get(str(line.product_id))

            eligible = (
                (inspection["status"] == "accepted" or inspection.get("resolution") == "RESTOCK")
                if inspection
                else receipt.status == "accepted"
            )

            pending = (
                max(Decimal("0"), line.processed_quantity - returned.get((receipt.id, line.product_id), Decimal("0")))
                if eligible
                else Decimal("0")
            )

            serial_numbers = inspection.get("serial_numbers", []) if inspection else []

            if serial_numbers:
                serial_numbers = list(
                    db.scalars(
                        select(InventorySerial.serial_number).where(
                            InventorySerial.company_id == current_user.company_id,
                            InventorySerial.product_id == line.product_id,
                            InventorySerial.serial_number.in_(serial_numbers),
                            InventorySerial.status == "IN_STOCK",
                            InventorySerial.warehouse_id == order.warehouse_id,
                        )
                    ).all()
                )

                pending = min(pending, Decimal(len(serial_numbers)))

            available.append(
                {
                    "product_id": str(line.product_id),
                    "name": products[line.product_id][0].name,
                    "sku": products[line.product_id][0].sku,
                    "quantity": str(line.quantity),
                    "returnable_quantity": str(pending),
                    "unit_cost": str(line.unit_cost),
                    "lots": inspection.get("lots", []) if inspection else [],
                    "serial_numbers": serial_numbers,
                }
            )

        data["returnable_lines"] = available

        receipt_data.append(data)

    return {
        "order_id": str(order.id),
        "version": order.version,
        "status": order.status,
        "warehouse_id": str(order.warehouse_id),
        "warehouse_name": wh.name if wh else "Almacén no disponible",
        "supplier_name": supplier.legal_name if supplier else "Proveedor no disponible",
        "currency": json.loads(order.details_json or "{}").get("currency"),
        "locations": [{"id": str(loc.id), "code": loc.code} for loc in locations],
        "lines": [
            {
                "product_id": str(line.product_id),
                "name": products[line.product_id][0].name,
                "sku": products[line.product_id][0].sku,
                "tracking_mode": products[line.product_id][1].tracking_mode if products[line.product_id][1] else "NONE",
                "ordered_quantity": str(line.quantity),
                "received_quantity": str(line.processed_quantity),
                "rejected_quantity": str(line.damaged_quantity),
                "pending_quantity": str(pending_quantity(line)),
                "cancelled_quantity": str(line.cancelled_quantity),
                "unit_cost": str(line.unit_cost),
            }
            for line in order.lines
        ],
        "receipts": receipt_data,
    }


def create_purchase_return(
    payload: PurchaseReturnCreateRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: Optional[str]
):
    record = None

    if idempotency_key:
        record, cached = claim_request(
            db, current_user.company_id, "purchase_return.create", idempotency_key, payload.model_dump(mode="json")
        )

        if cached is not None:
            return cached

    receipt = document(db, current_user, "GOODS_RECEIPT", payload.goods_receipt_id)

    if receipt.warehouse_id != payload.warehouse_id:
        raise HTTPException(409, "El almacén de devolución no coincide con el de recepción.")

    inspections = json.loads(receipt.details_json or "{}").get("inspections", [])

    accepted_ids = {
        UUID(item["product_id"])
        for item in inspections
        if item["status"] == "accepted" or item.get("resolution") == "RESTOCK"
    }

    if (
        inspections
        and any(item.product_id not in accepted_ids for item in payload.items)
        or not inspections
        and receipt.status != "accepted"
    ):
        raise HTTPException(
            409, "Solo se pueden devolver artículos aceptados. Resuelve la cuarentena por su flujo de inspección."
        )

    original_order = (
        document(db, current_user, "PURCHASE_ORDER", receipt.parent_id, lock=False) if receipt.parent_id else None
    )

    original_costs = {line.product_id: line.unit_cost for line in original_order.lines} if original_order else {}

    rc_lines = {l.product_id: l for l in receipt.lines}

    existing_returns = db.scalars(
        select(SupplyLine)
        .join(SupplyDocument, SupplyDocument.id == SupplyLine.document_id)
        .where(
            SupplyDocument.company_id == current_user.company_id,
            SupplyDocument.parent_id == receipt.id,
            SupplyDocument.kind == "PURCHASE_RETURN",
        )
    ).all()

    already_returned = {}

    for line in existing_returns:
        already_returned[line.product_id] = already_returned.get(line.product_id, Decimal("0")) + line.quantity

    selected_serials = []

    selected_lots = []

    inspection_by_product = {UUID(item["product_id"]): item for item in inspections}

    total_expected_credit = Decimal("0")

    for item in payload.items:
        if item.product_id not in rc_lines:
            raise HTTPException(409, "Producto no presente en la recepción original.")

        rc_line = rc_lines[item.product_id]

        received_qty = rc_line.processed_quantity if rc_line.processed_quantity > 0 else rc_line.quantity

        available_returnable = received_qty - already_returned.get(item.product_id, Decimal("0"))

        if item.quantity > available_returnable:
            raise HTTPException(
                409,
                "No se puede devolver más del saldo disponible de la recepción, incluidas las devoluciones anteriores.",
            )

        inspection = inspection_by_product.get(item.product_id, {})

        serial_values = [value.strip() for value in item.serial_numbers]

        if inspection.get("serial_numbers"):
            if (
                len(set(serial_values)) != len(serial_values)
                or len(serial_values) != item.quantity
                or not set(serial_values).issubset(inspection["serial_numbers"])
            ):
                raise HTTPException(422, "Selecciona una serie distinta de esta recepción por cada unidad a devolver.")

            rows = db.scalars(
                select(InventorySerial)
                .where(
                    InventorySerial.company_id == current_user.company_id,
                    InventorySerial.product_id == item.product_id,
                    InventorySerial.serial_number.in_(serial_values),
                    InventorySerial.warehouse_id == payload.warehouse_id,
                    InventorySerial.status == "IN_STOCK",
                )
                .with_for_update()
            ).all()

            if len(rows) != len(serial_values):
                raise HTTPException(409, "Una serie ya fue vendida, devuelta o trasladada. Actualiza la recepción.")

            selected_serials.extend(rows)

        if inspection.get("lots"):
            allocation = next((lot for lot in inspection["lots"] if lot["lot_id"] == str(item.lot_id)), None)

            if not allocation:
                raise HTTPException(422, "Selecciona un lote de la recepción para la devolución.")

            previous_lot_quantity = Decimal("0")

            previous_documents = db.scalars(
                select(SupplyDocument).where(
                    SupplyDocument.company_id == current_user.company_id,
                    SupplyDocument.kind == "PURCHASE_RETURN",
                    SupplyDocument.parent_id == receipt.id,
                )
            ).all()

            for previous in previous_documents:
                previous_lot_quantity += sum(
                    (
                        Decimal(line["quantity"])
                        for line in json.loads(previous.details_json or "{}").get("tracking", [])
                        if line.get("lot_id") == str(item.lot_id)
                    ),
                    Decimal("0"),
                )

            if item.quantity > Decimal(allocation["quantity"]) - previous_lot_quantity:
                raise HTTPException(409, "La devolución supera el saldo disponible de este lote en la recepción.")

            selected_lots.append(
                {"product_id": str(item.product_id), "lot_id": str(item.lot_id), "quantity": str(item.quantity)}
            )

        total_expected_credit += item.quantity * original_costs.get(item.product_id, rc_line.unit_cost)

    return_lines = [
        StockLine(product_id=it.product_id, quantity=it.quantity, unit_cost=rc_lines[it.product_id].unit_cost)
        for it in payload.items
    ]

    details = {
        "reason": payload.reason,
        "override_reason": payload.override_reason,
        "expected_credit_note_amount": str(total_expected_credit),
        "tracking": selected_lots,
        "serial_numbers": [row.serial_number for row in selected_serials],
    }

    ret_doc = create_document(
        db,
        current_user,
        "PURCHASE_RETURN",
        "completed",
        payload.warehouse_id,
        return_lines,
        supplier_id=receipt.supplier_id,
        parent_id=receipt.id,
        details_json=json.dumps(details),
    )

    for it in payload.items:
        move_stock(
            db,
            current_user.company_id,
            payload.warehouse_id,
            it.product_id,
            -it.quantity,
            rc_lines[it.product_id].unit_cost,
            ret_doc.id,
            "DEVOLUCION_PROVEEDOR",
        )

    for serial in selected_serials:
        serial.status = "RETURNED_TO_SUPPLIER"

        serial.current_doc_type = "PURCHASE_RETURN"

        serial.current_doc_id = ret_doc.id

    for it in payload.items:
        inspection = inspection_by_product.get(it.product_id, {})

        if inspection.get("location_id"):
            located = db.scalar(
                select(LocationStock)
                .where(
                    LocationStock.company_id == current_user.company_id,
                    LocationStock.location_id == UUID(inspection["location_id"]),
                    LocationStock.product_id == it.product_id,
                )
                .with_for_update()
            )

            if not located or located.quantity < it.quantity:
                raise HTTPException(
                    409,
                    "La ubicación de origen no tiene cantidad suficiente. Revisa sus movimientos antes de devolver.",
                )

            located.quantity -= it.quantity

    record_audit(
        db,
        current_user,
        ret_doc.id,
        "RETURN_PURCHASE",
        {
            "goods_receipt_id": str(receipt.id),
            "expected_credit": str(total_expected_credit),
            "serials": len(selected_serials),
        },
    )

    from salesia.modules.inventario.application.reclamos_proveedor import synchronize_replacement_order
    synchronize_replacement_order(db, current_user, original_order)
    result = response(ret_doc)

    if record is not None:
        complete_request(record, result)

    db.commit()

    return result


def resolve_three_way_match(
    order_id: UUID, payload: ThreeWayMatchResolveRequest, current_user: AuthenticatedUser, db: Session
):
    from salesia.modules.inventario.application.compras_costos_conciliacion import MatchActionRequest, match_action
    if payload.match_id is None or payload.version is None:
        raise HTTPException(422, "Selecciona la conciliación concreta y su versión desde la revisión de facturas.")
    match_rec = db.scalar(select(PurchaseInvoiceMatch).where(PurchaseInvoiceMatch.company_id == current_user.company_id, PurchaseInvoiceMatch.id == payload.match_id, PurchaseInvoiceMatch.purchase_order_id == order_id))
    if match_rec is None:
        raise HTTPException(404, "Conciliación no encontrada para la orden.")
    return match_action(db, current_user, match_rec.id, MatchActionRequest(version=payload.version, reason=payload.resolution_notes), "approve")
