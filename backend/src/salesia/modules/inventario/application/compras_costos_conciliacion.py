import json
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from salesia.modules.inventario.application.contracts.compras_costos_conciliacion import ThreeWayMatchRequest
from salesia.modules.inventario.infrastructure_models import PurchaseInvoiceMatch, SupplyDocument
from salesia.modules.inventario.service import document, record_audit
from salesia.modules.organizacion.application.periodos import business_date, require_open_period
from salesia.modules.organizacion.application.politicas import effective_policy
from salesia.shared.infrastructure.models import ProductModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request

ACTIVE_MATCHES = ("MATCHED", "APPROVED_OVERRIDE", "UNDER_REVIEW")
SCALE = Decimal("0.000001")


class MatchActionRequest(BaseModel):
    version: int = Field(ge=1)
    reason: str = Field(min_length=5, max_length=2000)


def accepted_receipt_quantities(db, company_id, order):
    received = defaultdict(lambda: Decimal("0"))
    receipts = db.scalars(select(SupplyDocument).where(SupplyDocument.company_id == company_id, SupplyDocument.parent_id == order.id, SupplyDocument.kind == "GOODS_RECEIPT")).all()
    returned = defaultdict(lambda: Decimal("0"))
    if receipts:
        returns = db.scalars(select(SupplyDocument).where(SupplyDocument.company_id == company_id, SupplyDocument.parent_id.in_([row.id for row in receipts]), SupplyDocument.kind == "PURCHASE_RETURN", SupplyDocument.status == "completed")).all()
        for returned_document in returns:
            for line in returned_document.lines:
                returned[(returned_document.parent_id, line.product_id)] += line.quantity
    for receipt in receipts:
        inspections = {item["product_id"]: item for item in json.loads(receipt.details_json or "{}").get("inspections", [])}
        for line in receipt.lines:
            inspection = inspections.get(str(line.product_id))
            accepted = inspection and (inspection.get("status") == "accepted" or inspection.get("resolution") == "RESTOCK")
            if accepted or (not inspections and receipt.status == "accepted"):
                quantity = line.processed_quantity if line.processed_quantity > 0 else line.quantity
                received[line.product_id] += max(Decimal("0"), quantity - returned[(receipt.id, line.product_id)])
    return received, receipts


def reserved_invoice_quantities(db, company_id, order, exclude_match_id=None):
    quantities = defaultdict(lambda: Decimal("0"))
    statement = select(PurchaseInvoiceMatch).where(PurchaseInvoiceMatch.company_id == company_id, PurchaseInvoiceMatch.purchase_order_id == order.id, PurchaseInvoiceMatch.status.in_(ACTIVE_MATCHES))
    if exclude_match_id:
        statement = statement.where(PurchaseInvoiceMatch.id != exclude_match_id)
    legacy = []
    for match in db.scalars(statement).all():
        lines = json.loads(match.lines_snapshot_json or "[]")
        if not lines:
            legacy.append(str(match.id))
        for line in lines:
            quantities[UUID(line["product_id"])] += Decimal(line["quantity"])
    return quantities, legacy


def invoice_context(db, user, order_id):
    order = document(db, user, "PURCHASE_ORDER", order_id, lock=False)
    received, receipts = accepted_receipt_quantities(db, user.company_id, order)
    reserved, legacy = reserved_invoice_quantities(db, user.company_id, order)
    commercial = {item["product_id"]: item for item in json.loads(order.details_json or "{}").get("commercial_lines", [])}
    lines = []
    for line in order.lines:
        product = db.scalar(select(ProductModel).where(ProductModel.company_id == user.company_id, ProductModel.id == line.product_id))
        eligible = max(Decimal("0"), min(line.quantity - line.cancelled_quantity, received[line.product_id]) - reserved[line.product_id]) if not legacy else Decimal("0")
        lines.append({"product_id": str(line.product_id), "sku": product.sku if product else "", "name": product.name if product else "Producto", "ordered_quantity": str(line.quantity), "accepted_quantity": str(received[line.product_id]), "committed_invoice_quantity": str(reserved[line.product_id]), "invoiceable_quantity": str(eligible), "unit_price": str(line.unit_cost), "tax_rate": str(commercial.get(str(line.product_id), {}).get("tax_rate", "0"))})
    details = json.loads(order.details_json or "{}")
    matches = db.scalars(select(PurchaseInvoiceMatch).where(PurchaseInvoiceMatch.company_id == user.company_id, PurchaseInvoiceMatch.purchase_order_id == order.id).order_by(PurchaseInvoiceMatch.created_at.desc())).all()
    return {"supplier_id": str(order.supplier_id), "business_date": business_date(db, user.company_id).isoformat(), "order_id": str(order.id), "order_version": order.version, "status": order.status, "currency": details.get("currency", "USD"), "payment_terms_days": details.get("payment_terms_days", 30), "lines": lines, "receipts": [str(row.id) for row in receipts], "legacy_matches_requiring_review": legacy, "policy": effective_policy(db, user.company_id, "purchase_matching_policy"), "matches": [serialize_match(db, row) for row in matches]}


def inspect_invoice(db, user, order, lines, amount, policy, exclude_match_id=None):
    original = {line.product_id: line for line in order.lines}
    received, receipts = accepted_receipt_quantities(db, user.company_id, order)
    reserved, legacy = reserved_invoice_quantities(db, user.company_id, order, exclude_match_id)
    commercial = {item["product_id"]: item for item in json.loads(order.details_json or "{}").get("commercial_lines", [])}
    errors, snapshots, seen = [], [], set()
    if not lines:
        errors.append({"code": "missing_lines", "message": "Detalla los productos, cantidades, precios e impuestos de la factura."})
    if legacy:
        errors.append({"code": "legacy_match", "message": "Existen conciliaciones históricas sin líneas; revísalas y anula las que deban reemplazarse antes de comprometer unidades adicionales.", "match_ids": legacy})
    expected_total, actual_total = Decimal("0"), Decimal("0")
    for item in lines:
        product_id = UUID(str(item["product_id"]))
        if product_id in seen or product_id not in original:
            raise HTTPException(422, "Agrupa cada producto una vez y utiliza únicamente artículos de la orden.")
        seen.add(product_id)
        source = original[product_id]
        quantity, unit_price = Decimal(str(item["quantity"])), Decimal(str(item["unit_price"]))
        expected_tax = Decimal(str(commercial.get(str(product_id), {}).get("tax_rate", "0")))
        tax = Decimal(str(item["tax_rate"])) if item.get("tax_rate") is not None else expected_tax
        eligible = max(Decimal("0"), min(source.quantity - source.cancelled_quantity, received[product_id]) - reserved[product_id])
        expected = (quantity * source.unit_cost * (1 + expected_tax)).quantize(SCALE)
        total = (quantity * unit_price * (1 + tax)).quantize(SCALE)
        expected_total += expected
        actual_total += total
        if quantity > eligible:
            errors.append({"code": "quantity", "product_id": str(product_id), "message": "La cantidad facturada supera lo aceptado y aún no comprometido.", "available": str(eligible), "requested": str(quantity)})
        price_variance = abs(unit_price - source.unit_cost)
        tolerance = source.unit_cost * Decimal(str(policy.get("unit_price_tolerance_percentage", "0"))) / 100
        if price_variance > tolerance:
            errors.append({"code": "price", "product_id": str(product_id), "message": "El precio difiere de la orden por encima de la tolerancia autorizada.", "expected": str(source.unit_cost), "actual": str(unit_price)})
        if tax != expected_tax:
            errors.append({"code": "tax", "product_id": str(product_id), "message": "La tasa de impuesto no coincide con la orden.", "expected": str(expected_tax), "actual": str(tax)})
        snapshots.append({"product_id": str(product_id), "quantity": str(quantity), "unit_price": str(unit_price), "tax_rate": str(tax), "order_unit_price": str(source.unit_cost), "order_tax_rate": str(expected_tax), "total": str(total), "expected_total": str(expected)})
    if abs(amount - actual_total) > Decimal(str(policy.get("rounding_tolerance", "0.01"))):
        errors.append({"code": "header_total", "message": "El importe del documento no coincide con la suma de sus líneas e impuestos.", "calculated_total": str(actual_total)})
    return snapshots, {"errors": errors, "reference_amount": str(expected_total), "calculated_total": str(actual_total), "currency": json.loads(order.details_json or "{}").get("currency", "USD"), "receipt_ids": [str(row.id) for row in receipts], "order_version": order.version}


def serialize_match(db, row):
    from salesia.modules.finanzas.infrastructure.models.obligaciones import PayableModel
    payable = db.scalar(select(PayableModel).where(PayableModel.company_id == row.company_id, PayableModel.invoice_match_id == row.id))
    validation = json.loads(row.validation_json or "{}")
    return {"id": str(row.id), "purchase_order_id": str(row.purchase_order_id), "status": row.status, "invoice_number": row.invoice_number, "invoice_amount": str(row.invoice_amount), "matched_amount": str(row.matched_amount), "discrepancy_amount": str(row.discrepancy_amount), "requires_review": row.status == "UNDER_REVIEW", "version": row.version, "lines": json.loads(row.lines_snapshot_json or "[]"), "validation": validation, "currency": validation.get("currency"), "policy": json.loads(row.policy_snapshot_json or "{}"), "reviewed_by": str(row.reviewed_by) if row.reviewed_by else None, "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None, "payable_id": str(payable.id) if payable else None, "payable_status": payable.status if payable else None, "notes": row.notes}


def process_three_way_match(order_id: UUID, payload: ThreeWayMatchRequest, current_user, db, idempotency_key=None):
    record, cached = claim_request(db, current_user.company_id, f"purchase_invoice.match:{order_id}", idempotency_key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, current_user.company_id, business_date(db, current_user.company_id))
    order = document(db, current_user, "PURCHASE_ORDER", order_id)
    if order.supplier_claim_id or json.loads(order.details_json or "{}").get("no_additional_debt"):
        raise HTTPException(409, "La orden es una reposición sin nueva deuda. No admite otra factura ni obligación de pago.")
    if order.status not in ("approved", "partially_received", "received", "closed"):
        raise HTTPException(409, "La orden debe estar aprobada y contar con recepción aceptada.")
    number = payload.supplier_invoice_number.strip().upper()
    if not number:
        raise HTTPException(422, "Indica el número de la factura del proveedor.")
    duplicate = db.scalar(select(PurchaseInvoiceMatch.id).join(SupplyDocument, SupplyDocument.id == PurchaseInvoiceMatch.purchase_order_id).where(PurchaseInvoiceMatch.company_id == current_user.company_id, SupplyDocument.company_id == current_user.company_id, SupplyDocument.supplier_id == order.supplier_id, PurchaseInvoiceMatch.invoice_number == number, PurchaseInvoiceMatch.status != "VOIDED"))
    if duplicate:
        raise HTTPException(409, "La factura de este proveedor ya tiene una conciliación vigente.")
    policy = effective_policy(db, current_user.company_id, "purchase_matching_policy")
    snapshots, validation = inspect_invoice(db, current_user, order, [item.model_dump(mode="json") for item in payload.invoice_lines or []], payload.invoice_amount, policy)
    status = "UNDER_REVIEW" if validation["errors"] else "MATCHED"
    current = datetime.now(timezone.utc)
    row = PurchaseInvoiceMatch(company_id=current_user.company_id, purchase_order_id=order.id, goods_receipt_id=UUID(validation["receipt_ids"][0]) if validation["receipt_ids"] else None, invoice_number=number, invoice_amount=payload.invoice_amount, matched_amount=Decimal(validation["reference_amount"]), discrepancy_amount=abs(payload.invoice_amount - Decimal(validation["reference_amount"])), status=status, notes=payload.notes, reviewed_by=current_user.user_id if status == "MATCHED" else None, reviewed_at=current if status == "MATCHED" else None, version=1, lines_snapshot_json=json.dumps(snapshots), validation_json=json.dumps(validation), policy_snapshot_json=json.dumps(policy))
    db.add(row)
    db.flush()
    result = serialize_match(db, row)
    record_audit(db, current_user, row.id, "MATCH_PURCHASE_INVOICE", result)
    complete_request(record, result)
    db.commit()
    return result


def match_action(db, user, identifier, payload, action, key=None):
    record, cached = claim_request(db, user.company_id, f"purchase_invoice.{action}:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    row = db.scalar(select(PurchaseInvoiceMatch).where(PurchaseInvoiceMatch.company_id == user.company_id, PurchaseInvoiceMatch.id == identifier).with_for_update())
    if row is None:
        raise HTTPException(404, "Conciliación no encontrada.")
    if row.version != payload.version or row.status == "VOIDED":
        raise HTTPException(409, "La conciliación cambió o ya fue anulada.")
    from salesia.modules.finanzas.infrastructure.models.obligaciones import PayableModel
    payable = db.scalar(select(PayableModel).where(PayableModel.company_id == user.company_id, PayableModel.invoice_match_id == row.id))
    if payable and (action != "void" or payable.status != "cancelled"):
        raise HTTPException(409, "La conciliación tiene una obligación vinculada. Cancélala antes de anular el documento.")
    if action == "approve":
        if "approvals:manage" not in user.permissions:
            raise HTTPException(403, "Aprobar diferencias de precio requiere autorización de aprobaciones.")
        if row.status != "UNDER_REVIEW":
            raise HTTPException(409, "Solo se resuelven conciliaciones pendientes de revisión.")
        order = document(db, user, "PURCHASE_ORDER", row.purchase_order_id)
        _, validation = inspect_invoice(db, user, order, json.loads(row.lines_snapshot_json or "[]"), row.invoice_amount, json.loads(row.policy_snapshot_json or "{}"), row.id)
        if any(item["code"] != "price" for item in validation["errors"]):
            raise HTTPException(409, {"message": "Corrige la factura o la recepción; una autorización de precio no libera cantidades, impuestos o totales inconsistentes.", "errors": validation["errors"]})
        row.validation_json = json.dumps(validation)
        row.status = "APPROVED_OVERRIDE" if validation["errors"] else "MATCHED"
    else:
        row.status = "VOIDED"
    row.notes = f"{row.notes or ''}\n{action}: {payload.reason}".strip()
    row.reviewed_by, row.reviewed_at = user.user_id, datetime.now(timezone.utc)
    row.version += 1
    result = serialize_match(db, row)
    record_audit(db, user, row.id, f"PURCHASE_INVOICE_{action.upper()}", {"reason": payload.reason, "status": row.status, "version": row.version})
    complete_request(record, result)
    db.commit()
    return result


def validate_match_for_payable(db, user, payload):
    match = db.scalar(select(PurchaseInvoiceMatch).where(PurchaseInvoiceMatch.company_id == user.company_id, PurchaseInvoiceMatch.id == payload.invoice_match_id).with_for_update())
    if match is None or match.status not in ("MATCHED", "APPROVED_OVERRIDE") or not json.loads(match.lines_snapshot_json or "[]"):
        raise HTTPException(409, "Vincula una conciliación vigente, revisada por línea y sin diferencias pendientes.")
    order = document(db, user, "PURCHASE_ORDER", match.purchase_order_id)
    if order.supplier_claim_id or json.loads(order.details_json or "{}").get("no_additional_debt"):
        raise HTTPException(409, "Una reposición sin deuda no genera otra obligación financiera.")
    currency = json.loads(order.details_json or "{}").get("currency", "USD")
    if payload.purchase_order_id != order.id or payload.supplier_id != order.supplier_id or payload.currency != currency or payload.amount != match.invoice_amount or payload.document_number.strip().upper() != match.invoice_number:
        raise HTTPException(422, "La obligación debe conservar proveedor, orden, moneda, importe y número de la factura conciliada.")
    _, validation = inspect_invoice(db, user, order, json.loads(match.lines_snapshot_json), match.invoice_amount, json.loads(match.policy_snapshot_json), match.id)
    failures = [error for error in validation["errors"] if error["code"] != "price" or match.status != "APPROVED_OVERRIDE"]
    if failures:
        raise HTTPException(409, {"message": "Las recepciones o las cantidades comprometidas cambiaron después de conciliar.", "errors": failures})
    from salesia.modules.finanzas.infrastructure.models.obligaciones import PayableModel
    if db.scalar(select(PayableModel.id).where(PayableModel.company_id == user.company_id, PayableModel.invoice_match_id == match.id)):
        raise HTTPException(409, "La factura conciliada ya tiene una obligación registrada.")
    return match
