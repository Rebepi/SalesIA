import json
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import and_, func, or_, select

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.finanzas.application.saldos_proveedor import supplier_claim_credit_totals
from salesia.modules.finanzas.infrastructure.models.obligaciones import SupplierBalanceMovementModel
from salesia.modules.inventario.application.compras_saldos import capture_revision
from salesia.modules.inventario.application.compras_costos_conciliacion import accepted_receipt_quantities
from salesia.modules.inventario.application.contracts.comunes import StockLine
from salesia.modules.inventario.infrastructure.models.reclamos import SupplierClaimModel
from salesia.modules.inventario.infrastructure_models import PurchaseInvoiceMatch, Supplier, SupplyDocument
from salesia.modules.inventario.service import create_document, document
from salesia.modules.organizacion.application.periodos import business_date, require_open_period
from salesia.shared.infrastructure.models import CompanyModel, ProductModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request, next_number

SourceKind = Literal["purchase_order", "goods_receipt", "purchase_return", "invoice_match"]
Resolution = Literal["credit", "discount", "replacement"]
QUANTUM = Decimal("0.000001")


class ClaimItem(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(gt=0, max_digits=20, decimal_places=6)


class ClaimCreateRequest(BaseModel):
    source_kind: SourceKind
    source_id: UUID
    reason_type: Literal["return", "shortage", "overprice", "quality"]
    resolution: Resolution
    description: str = Field(min_length=5, max_length=4000)
    expected_amount: Decimal | None = Field(default=None, ge=0, max_digits=20, decimal_places=6)
    items: list[ClaimItem] = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def distinct_lines(self):
        if len({item.product_id for item in self.items}) != len(self.items):
            raise ValueError("Agrupa cada producto en una sola línea del reclamo.")
        return self


class ClaimAcknowledgeRequest(BaseModel):
    version: int = Field(ge=1)
    resolution: Resolution
    agreed_amount: Decimal | None = Field(default=None, ge=0, max_digits=20, decimal_places=6)
    notes: str = Field(min_length=5, max_length=4000)


class ClaimActionRequest(BaseModel):
    version: int = Field(ge=1)
    reason: str = Field(min_length=5, max_length=4000)


class ClaimCreditRequest(BaseModel):
    version: int = Field(ge=1)
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    movement_date: date
    reference: str = Field(min_length=1, max_length=128)
    notes: str = Field(min_length=5, max_length=4000)


class ClaimReplacementRequest(BaseModel):
    version: int = Field(ge=1)
    delivery_date: date
    notes: str = Field(min_length=5, max_length=4000)
    items: list[ClaimItem] = Field(min_length=1, max_length=500)


def audit(db, user, row, action, data):
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action=action, entity_type="SupplierClaim", entity_id=row.id, diff=data)


def history(row, user, action, notes, data=None):
    events = json.loads(row.history_json or "[]")
    events.append({"action": action, "actor": user.email, "at": datetime.now(timezone.utc).isoformat(), "notes": notes, **(data or {})})
    row.history_json = json.dumps(events)


def scoped_claim(db, user, identifier, lock=True):
    statement = select(SupplierClaimModel).where(SupplierClaimModel.company_id == user.company_id, SupplierClaimModel.id == identifier)
    row = db.scalar(statement.with_for_update() if lock else statement)
    if row is None:
        raise HTTPException(404, "Reclamo de proveedor no encontrado.")
    return row


def claim_source(db, user, kind, identifier):
    if kind == "invoice_match":
        source = db.scalar(select(PurchaseInvoiceMatch).where(PurchaseInvoiceMatch.company_id == user.company_id, PurchaseInvoiceMatch.id == identifier))
        if source is None or source.status == "VOIDED":
            raise HTTPException(404, "Factura conciliada vigente no encontrada.")
        order = document(db, user, "PURCHASE_ORDER", source.purchase_order_id, lock=False)
        originals = json.loads(source.lines_snapshot_json or "[]")
        if not originals:
            raise HTTPException(409, "La factura histórica no tiene detalle por producto. Vincula el reclamo a la compra o a su recepción.")
        lines = [{"product_id": item["product_id"], "quantity": item["quantity"], "unit_cost": item["unit_price"], "tax_rate": item["tax_rate"], "pending_quantity": item["quantity"], "overprice_per_unit": str(max(Decimal("0"), Decimal(item["unit_price"]) - Decimal(item.get("order_unit_price", item["unit_price"]))))} for item in originals]
        label = source.invoice_number
    else:
        source = document(db, user, {"purchase_order": "PURCHASE_ORDER", "goods_receipt": "GOODS_RECEIPT", "purchase_return": "PURCHASE_RETURN"}[kind], identifier, lock=False)
        if kind == "purchase_order":
            order = source
            if source.status in ("draft", "submitted", "reopened"):
                raise HTTPException(409, "El reclamo requiere una compra comprometida, una recepción o una devolución.")
        else:
            receipt = source if kind == "goods_receipt" else document(db, user, "GOODS_RECEIPT", source.parent_id, lock=False)
            order = document(db, user, "PURCHASE_ORDER", receipt.parent_id, lock=False)
        commercial = {item["product_id"]: item for item in json.loads(order.details_json or "{}").get("commercial_lines", [])}
        lines = [{"product_id": str(item.product_id), "quantity": str(item.quantity), "unit_cost": str(item.unit_cost), "tax_rate": commercial.get(str(item.product_id), {}).get("tax_rate", "0"), "pending_quantity": str(max(Decimal("0"), item.quantity - item.processed_quantity - item.cancelled_quantity)) if kind == "purchase_order" else str(item.quantity), "shortage_claimable_quantity": str(item.cancelled_quantity) if kind == "purchase_order" else "0"} for item in source.lines]
        label = f"{source.kind} {str(source.id)[:8].upper()}"
    if order.supplier_claim_id:
        raise HTTPException(409, "La compra corresponde a una reposición. Registra su devolución o inspección; el reclamo original actualizará su cumplimiento.")
    for line in lines:
        product = db.scalar(select(ProductModel).where(ProductModel.company_id == user.company_id, ProductModel.id == UUID(line["product_id"])))
        line["sku"], line["name"] = (product.sku, product.name) if product else ("", "Producto histórico")
    supplier = db.scalar(select(Supplier).where(Supplier.company_id == user.company_id, Supplier.id == order.supplier_id))
    return {"source_kind": kind, "source_id": str(identifier), "label": label, "supplier_id": str(order.supplier_id), "supplier_name": supplier.legal_name if supplier else "Proveedor", "purchase_order_id": str(order.id), "currency": json.loads(order.details_json or "{}").get("currency", supplier.currency if supplier else "USD"), "lines": lines}


def source_options(db, user, kind, limit, offset):
    model = PurchaseInvoiceMatch if kind == "invoice_match" else SupplyDocument
    statement = select(model).where(model.company_id == user.company_id)
    if kind == "invoice_match":
        statement = statement.where(model.status != "VOIDED", model.lines_snapshot_json != "[]")
    else:
        statement = statement.where(model.kind == {"purchase_order": "PURCHASE_ORDER", "goods_receipt": "GOODS_RECEIPT", "purchase_return": "PURCHASE_RETURN"}[kind])
        if kind == "purchase_order":
            statement = statement.where(model.status.notin_(("draft", "submitted", "reopened")), model.supplier_claim_id.is_(None))
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = db.scalars(statement.order_by(model.created_at.desc(), model.id).offset(offset).limit(limit)).all()
    items = []
    for row in rows:
        try:
            items.append(claim_source(db, user, kind, row.id))
        except HTTPException as failure:
            if failure.status_code not in (404, 409):
                raise
    return {"items": items, "total_count": total}


def check_source_coverage(db, user, source, requested, reason_type, exclude_claim_id=None):
    if source["source_kind"] == "purchase_order" and reason_type != "shortage":
        raise HTTPException(422, "La compra permite reclamar faltantes previamente cancelados. Para calidad o devoluciones usa su recepción, y para sobreprecios usa la factura conciliada.")
    if source["source_kind"] == "invoice_match" and reason_type != "overprice":
        raise HTTPException(422, "La factura conciliada permite reclamar sobreprecios; los reclamos físicos requieren una recepción o devolución.")
    scope = and_(SupplierClaimModel.source_kind == source["source_kind"], SupplierClaimModel.source_id == UUID(source["source_id"]))
    if source["source_kind"] in ("goods_receipt", "purchase_return"):
        origin = document(db, user, {"goods_receipt": "GOODS_RECEIPT", "purchase_return": "PURCHASE_RETURN"}[source["source_kind"]], UUID(source["source_id"]), lock=False)
        receipt_id = origin.id if source["source_kind"] == "goods_receipt" else origin.parent_id
        return_ids = db.scalars(select(SupplyDocument.id).where(SupplyDocument.company_id == user.company_id, SupplyDocument.kind == "PURCHASE_RETURN", SupplyDocument.parent_id == receipt_id)).all()
        scope = or_(and_(SupplierClaimModel.source_kind == "goods_receipt", SupplierClaimModel.source_id == receipt_id), and_(SupplierClaimModel.source_kind == "purchase_return", SupplierClaimModel.source_id.in_(return_ids)))
    statement = select(SupplierClaimModel).where(SupplierClaimModel.company_id == user.company_id, scope, SupplierClaimModel.status.notin_(("cancelled", "rejected")))
    if exclude_claim_id:
        statement = statement.where(SupplierClaimModel.id != exclude_claim_id)
    previous = defaultdict(lambda: Decimal("0"))
    for row in db.scalars(statement).all():
        for item in json.loads(row.items_json):
            previous[item["product_id"]] += Decimal(item["quantity"])
    by_product = {item["product_id"]: item for item in source["lines"]}
    selected, value = [], Decimal("0")
    for item in requested:
        identifier = str(item.product_id)
        original = by_product.get(identifier)
        if original is None:
            raise HTTPException(422, "El producto no pertenece al documento de origen.")
        cap = Decimal(original["shortage_claimable_quantity"] if source["source_kind"] == "purchase_order" else original["quantity"])
        if item.quantity + previous[identifier] > cap:
            raise HTTPException(409, "Las unidades ya están reclamadas o superan el saldo de origen. Para faltantes de compra cancela primero las unidades no entregadas desde el control de saldos.")
        price = Decimal(original["unit_cost"])
        if reason_type == "overprice" and original.get("overprice_per_unit") is not None:
            price = Decimal(original["overprice_per_unit"])
        value += item.quantity * price * (1 + Decimal(original["tax_rate"]))
        selected.append({**original, "quantity": str(item.quantity)})
    return selected, value.quantize(QUANTUM)


def replacement_totals(db, user, claim):
    received, committed = defaultdict(lambda: Decimal("0")), defaultdict(lambda: Decimal("0"))
    orders = db.scalars(select(SupplyDocument).where(SupplyDocument.company_id == user.company_id, SupplyDocument.supplier_claim_id == claim.id, SupplyDocument.kind == "PURCHASE_ORDER").order_by(SupplyDocument.created_at)).all()
    for order in orders:
        if order.status == "cancelled":
            continue
        accepted, receipts = accepted_receipt_quantities(db, user.company_id, order)
        returned = defaultdict(lambda: Decimal("0"))
        if receipts:
            returns = db.scalars(select(SupplyDocument).where(SupplyDocument.company_id == user.company_id, SupplyDocument.parent_id.in_([receipt.id for receipt in receipts]), SupplyDocument.kind == "PURCHASE_RETURN", SupplyDocument.status == "completed")).all()
            for returned_doc in returns:
                for line in returned_doc.lines:
                    returned[line.product_id] += line.quantity
        scrapped = defaultdict(lambda: Decimal("0"))
        for receipt in receipts:
            by_product = {line.product_id: line for line in receipt.lines}
            for inspection in json.loads(receipt.details_json or "{}").get("inspections", []):
                identifier = UUID(inspection["product_id"])
                if inspection.get("status") == "quarantine" and inspection.get("resolution") == "SCRAP" and identifier in by_product:
                    scrapped[identifier] += by_product[identifier].quantity
        for line in order.lines:
            received[line.product_id] += max(Decimal("0"), accepted[line.product_id])
            committed[line.product_id] += max(Decimal("0"), line.quantity - line.cancelled_quantity - returned[line.product_id] - scrapped[line.product_id])
    return received, committed, orders


def compensation_state(db, user, claim):
    if claim.status in ("open", "cancelled", "rejected"):
        return claim.status, {"issued": Decimal("0"), "available": Decimal("0"), "applied": Decimal("0")}
    if claim.resolution != "replacement":
        totals = supplier_claim_credit_totals(db, user.company_id, claim.supplier_id, claim.currency, claim.id)
        target = claim.agreed_amount or Decimal("0")
        status = "resolved" if target > 0 and totals["applied"] >= target else "partially_compensated" if totals["applied"] > 0 else "credit_available" if totals["issued"] > 0 else "acknowledged"
        return status, totals
    received, _, _ = replacement_totals(db, user, claim)
    items = json.loads(claim.items_json)
    complete = bool(items) and all(received[UUID(item["product_id"])] >= Decimal(item["quantity"]) for item in items)
    status = "resolved" if complete else "partially_compensated" if any(quantity > 0 for quantity in received.values()) else "acknowledged"
    return status, {"issued": Decimal("0"), "available": Decimal("0"), "applied": Decimal("0")}


def synchronize_claim(db, user, claim):
    db.flush()
    status, totals = compensation_state(db, user, claim)
    if status != claim.status:
        before = claim.status
        claim.status, claim.version = status, claim.version + 1
        history(claim, user, "COMPENSATION_UPDATED", "Estado recalculado según créditos aplicados y reposiciones aceptadas.", {"before": before, "status": status, "applied": str(totals["applied"])})
        audit(db, user, claim, "SUPPLIER_CLAIM_COMPENSATION", {"before": before, "status": status, "version": claim.version, "applied": str(totals["applied"])})


def synchronize_replacement_order(db, user, order):
    if order and order.supplier_claim_id:
        synchronize_claim(db, user, scoped_claim(db, user, order.supplier_claim_id))


def serialize_claim(db, user, claim):
    supplier = db.scalar(select(Supplier).where(Supplier.company_id == user.company_id, Supplier.id == claim.supplier_id))
    state, credits = compensation_state(db, user, claim)
    received, committed, orders = replacement_totals(db, user, claim)
    lines = [{**item, "replacement_received": str(received[UUID(item["product_id"])]), "replacement_committed": str(committed[UUID(item["product_id"])]), "replacement_available": str(max(Decimal("0"), Decimal(item["quantity"]) - committed[UUID(item["product_id"])]))} for item in json.loads(claim.items_json)]
    movements = db.scalars(select(SupplierBalanceMovementModel).where(SupplierBalanceMovementModel.company_id == user.company_id, SupplierBalanceMovementModel.source_claim_id == claim.id).order_by(SupplierBalanceMovementModel.created_at)).all()
    return {"id": str(claim.id), "code": claim.code, "supplier_id": str(claim.supplier_id), "supplier_name": supplier.legal_name if supplier else "Proveedor", "purchase_order_id": str(claim.purchase_order_id), "source_kind": claim.source_kind, "source_id": str(claim.source_id), "reason_type": claim.reason_type, "resolution": claim.resolution, "description": claim.description, "currency": claim.currency, "expected_amount": str(claim.expected_amount), "agreed_amount": str(claim.agreed_amount) if claim.agreed_amount is not None else None, "status": state, "version": claim.version, "credits": {key: str(value) for key, value in credits.items()}, "items": lines, "history": json.loads(claim.history_json or "[]"), "credit_documents": [{"id": str(row.id), "reference": row.reference, "amount": str(row.amount_delta), "date": row.movement_date.isoformat()} for row in movements], "replacement_orders": [{"id": str(order.id), "status": order.status, "version": order.version} for order in orders], "created_at": claim.created_at.isoformat(), "business_date": business_date(db, user.company_id).isoformat()}


def create_claim(db, user, payload, key):
    record, cached = claim_request(db, user.company_id, "supplier_claim.create", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    source = claim_source(db, user, payload.source_kind, payload.source_id)
    selected, value = check_source_coverage(db, user, source, payload.items, payload.reason_type)
    expected = payload.expected_amount if payload.expected_amount is not None else value
    if expected > value and "approvals:manage" not in user.permissions:
        raise HTTPException(403, "Un importe reclamado superior al valor de referencia requiere autorización de aprobaciones.")
    if payload.resolution != "replacement" and expected <= 0:
        raise HTTPException(422, "El reclamo monetario requiere un importe positivo sustentado.")
    row = SupplierClaimModel(company_id=user.company_id, supplier_id=UUID(source["supplier_id"]), purchase_order_id=UUID(source["purchase_order_id"]), source_kind=payload.source_kind, source_id=payload.source_id, code=f"RCP-{next_number(db, user.company_id, 'RCP'):08d}", reason_type=payload.reason_type, resolution=payload.resolution, description=payload.description, currency=source["currency"], expected_amount=expected, status="open", version=1, requested_by=user.user_id, items_json=json.dumps(selected), history_json="[]")
    history(row, user, "CREATE", payload.description, {"reference_amount": str(value), "expected_amount": str(expected)})
    db.add(row)
    db.flush()
    result = serialize_claim(db, user, row)
    audit(db, user, row, "CREATE_SUPPLIER_CLAIM", result)
    complete_request(record, result)
    db.commit()
    return result


def list_claims(db, user, status=None, supplier_id=None, limit=25, offset=0):
    statement = select(SupplierClaimModel).where(SupplierClaimModel.company_id == user.company_id)
    if status:
        statement = statement.where(SupplierClaimModel.status == status)
    if supplier_id:
        statement = statement.where(SupplierClaimModel.supplier_id == supplier_id)
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = db.scalars(statement.order_by(SupplierClaimModel.created_at.desc(), SupplierClaimModel.id).offset(offset).limit(limit)).all()
    return {"items": [serialize_claim(db, user, row) for row in rows], "total_count": total}


def acknowledge_claim(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"supplier_claim.acknowledge:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    row = scoped_claim(db, user, identifier)
    if row.version != payload.version or row.status != "open":
        raise HTTPException(409, "El reclamo cambió o ya tiene un acuerdo registrado.")
    from salesia.modules.seguridad.application.separacion_funciones import enforce
    enforce(db, user, "supplier_claim", [row.requested_by], "SupplierClaim", row.id)
    amount = payload.agreed_amount if payload.agreed_amount is not None else row.expected_amount
    if payload.resolution != "replacement" and (amount <= 0 or amount > row.expected_amount):
        raise HTTPException(422, "El acuerdo monetario debe ser positivo y no superar el importe reclamado.")
    row.resolution, row.agreed_amount = payload.resolution, amount if payload.resolution != "replacement" else Decimal("0")
    row.status, row.version, row.acknowledged_by = "acknowledged", row.version + 1, user.user_id
    history(row, user, "ACKNOWLEDGE", payload.notes, {"resolution": row.resolution, "agreed_amount": str(row.agreed_amount)})
    result = serialize_claim(db, user, row)
    audit(db, user, row, "ACKNOWLEDGE_SUPPLIER_CLAIM", result)
    complete_request(record, result)
    db.commit()
    return result


def claim_action(db, user, identifier, action, payload, key):
    record, cached = claim_request(db, user.company_id, f"supplier_claim.{action}:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    row = scoped_claim(db, user, identifier)
    if row.version != payload.version:
        raise HTTPException(409, "El reclamo cambió; vuelve a consultar su versión.")
    if action == "reopen":
        if row.status not in ("cancelled", "rejected"):
            raise HTTPException(409, "Solo se reabren reclamos cancelados o rechazados sin compensación.")
        source = claim_source(db, user, row.source_kind, row.source_id)
        requested = [ClaimItem(product_id=item["product_id"], quantity=item["quantity"]) for item in json.loads(row.items_json)]
        check_source_coverage(db, user, source, requested, row.reason_type, row.id)
        row.status, row.agreed_amount, row.acknowledged_by = "open", None, None
    else:
        if row.status not in ("open", "acknowledged") or (action == "reject" and row.status != "open"):
            raise HTTPException(409, "El reclamo tiene compensaciones o no admite esta transición.")
        if db.scalar(select(SupplierBalanceMovementModel.id).where(SupplierBalanceMovementModel.company_id == user.company_id, SupplierBalanceMovementModel.source_claim_id == row.id)):
            raise HTTPException(409, "El reclamo ya tiene documentos financieros vinculados.")
        _, committed, _ = replacement_totals(db, user, row)
        if any(amount > 0 for amount in committed.values()):
            raise HTTPException(409, "Cancela primero los saldos de reposición pendientes; las unidades ya recibidas conservan su expediente.")
        row.status = "rejected" if action == "reject" else "cancelled"
    row.version += 1
    history(row, user, action.upper(), payload.reason)
    result = serialize_claim(db, user, row)
    audit(db, user, row, "CHANGE_SUPPLIER_CLAIM", {"action": action, "reason": payload.reason, "status": row.status, "version": row.version})
    complete_request(record, result)
    db.commit()
    return result


def issue_claim_credit(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"supplier_claim.credit:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, payload.movement_date)
    if payload.movement_date > business_date(db, user.company_id) or not payload.reference.strip():
        raise HTTPException(422, "Registra una compensación documentada, con fecha de hoy o anterior y referencia válida.")
    row = scoped_claim(db, user, identifier)
    if row.version != payload.version or row.status in ("open", "cancelled", "rejected", "resolved") or row.resolution == "replacement":
        raise HTTPException(409, "El reclamo cambió o no tiene un acuerdo monetario vigente.")
    totals = supplier_claim_credit_totals(db, user.company_id, row.supplier_id, row.currency, row.id)
    if totals["issued"] + payload.amount > row.agreed_amount:
        raise HTTPException(409, "Los documentos de crédito superarían el importe acordado.")
    reference = payload.reference.strip().upper()
    if db.scalar(select(SupplierBalanceMovementModel.id).where(SupplierBalanceMovementModel.company_id == user.company_id, SupplierBalanceMovementModel.supplier_id == row.supplier_id, SupplierBalanceMovementModel.currency == row.currency, func.upper(SupplierBalanceMovementModel.reference) == reference, SupplierBalanceMovementModel.kind == "credit")):
        raise HTTPException(409, "Este documento de crédito del proveedor ya fue registrado.")
    movement = SupplierBalanceMovementModel(company_id=user.company_id, supplier_id=row.supplier_id, currency=row.currency, amount_delta=payload.amount, movement_date=payload.movement_date, kind="credit", reference=reference, source_claim_id=row.id, source_document_id=row.purchase_order_id, created_by=user.user_id, notes=payload.notes, allocations_json="[]")
    db.add(movement)
    db.flush()
    row.version += 1
    history(row, user, "CREDIT_DOCUMENT", payload.notes, {"movement_id": str(movement.id), "reference": reference, "amount": str(payload.amount)})
    synchronize_claim(db, user, row)
    result = serialize_claim(db, user, row)
    audit(db, user, row, "REGISTER_SUPPLIER_CLAIM_CREDIT", {"movement_id": str(movement.id), "amount": str(payload.amount), "reference": reference})
    complete_request(record, result)
    db.commit()
    return result


def create_replacement_order(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"supplier_claim.replacement:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    if not ({"purchases:approve", "approvals:manage", "organization:manage"} & set(user.permissions)):
        raise HTTPException(403, "Autorizar una reposición sin nueva deuda requiere autorización de compras o administración.")
    row = scoped_claim(db, user, identifier)
    if row.version != payload.version or row.resolution != "replacement" or row.status not in ("acknowledged", "partially_compensated"):
        raise HTTPException(409, "El reclamo cambió o no tiene una reposición pendiente acordada.")
    if payload.delivery_date < business_date(db, user.company_id):
        raise HTTPException(422, "La fecha de reposición no puede ser anterior a hoy.")
    _, committed, _ = replacement_totals(db, user, row)
    by_product = {UUID(item["product_id"]): item for item in json.loads(row.items_json)}
    seen, lines, value = set(), [], Decimal("0")
    for item in payload.items:
        original = by_product.get(item.product_id)
        if original is None or item.product_id in seen or item.quantity + committed[item.product_id] > Decimal(original["quantity"]):
            raise HTTPException(409, "La cantidad de reposición está duplicada, ya comprometida o supera lo acordado.")
        seen.add(item.product_id)
        cost = Decimal(original["unit_cost"])
        lines.append(StockLine(product_id=item.product_id, quantity=item.quantity, unit_cost=cost))
        value += item.quantity * cost
    original_order = document(db, user, "PURCHASE_ORDER", row.purchase_order_id, lock=False)
    details = {"currency": row.currency, "payment_terms_days": 0, "delivery_date": payload.delivery_date.isoformat(), "notes": payload.notes, "supplier_claim_id": str(row.id), "supplier_claim_code": row.code, "no_additional_debt": True, "subtotal": "0", "tax_total": "0", "total": "0", "replacement_inventory_value": str(value), "commercial_lines": [{"product_id": str(item.product_id), "unit_list_cost": str(item.unit_cost), "discount_percentage": "0", "tax_rate": "0", "subtotal": "0", "tax_amount": "0", "total": "0"} for item in lines]}
    order = create_document(db, user, "PURCHASE_ORDER", "approved", original_order.warehouse_id, lines, supplier_id=row.supplier_id, supplier_claim_id=row.id, details_json=json.dumps(details))
    row.version += 1
    history(row, user, "REPLACEMENT_ORDER", payload.notes, {"purchase_order_id": str(order.id)})
    capture_revision(db, user, order, "SUPPLIER_REPLACEMENT", f"Reposición del reclamo {row.code}: {payload.notes}")
    result = serialize_claim(db, user, row)
    audit(db, user, row, "CREATE_SUPPLIER_REPLACEMENT", {"purchase_order_id": str(order.id), "inventory_value": str(value)})
    complete_request(record, result)
    db.commit()
    return result
