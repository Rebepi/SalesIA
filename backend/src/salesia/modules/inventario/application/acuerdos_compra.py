import json
from collections import defaultdict
from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select

from salesia.modules.inventario.application.auxiliares.purchase_line_values import purchase_line_values
from salesia.modules.inventario.application.compras_saldos import capture_revision
from salesia.modules.inventario.application.homologacion_proveedor import supplier_qualified, require_supplier_qualified
from salesia.modules.inventario.application.contracts.comunes import PurchaseStockLine, StockLine
from salesia.modules.inventario.infrastructure_models import Supplier, SupplyDocument
from salesia.modules.inventario.service import create_document, document, product, record_audit, response
from salesia.modules.organizacion.application.periodos import business_date, require_open_period
from salesia.shared.infrastructure.models import CompanyModel, ProductModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request, next_number


class PurchaseAgreementRequest(BaseModel):
    supplier_id: UUID
    warehouse_id: UUID
    reference: str = Field(min_length=2, max_length=128)
    currency: str = Field(pattern="^[A-Z]{3}$")
    valid_from: date
    valid_until: date
    amount_limit: Decimal | None = Field(default=None, gt=0, max_digits=20, decimal_places=6)
    payment_terms_days: int = Field(default=30, ge=0, le=365)
    notes: str = Field(default="", max_length=4000)
    items: list[PurchaseStockLine] = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def valid_dates(self):
        if self.valid_until < self.valid_from:
            raise ValueError("La vigencia del acuerdo no es válida.")
        return self


class AgreementReleaseLine(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(gt=0, max_digits=20, decimal_places=6)


class AgreementReleaseRequest(BaseModel):
    version: int = Field(ge=1)
    delivery_date: date
    notes: str = Field(default="", max_length=2000)
    items: list[AgreementReleaseLine] = Field(min_length=1, max_length=500)


class AgreementActionRequest(BaseModel):
    version: int = Field(ge=1)
    reason: str = Field(min_length=5, max_length=2000)


def agreement_data(db, user, agreement):
    data = response(agreement)
    details = data["details"]
    supplier = db.scalar(select(Supplier).where(Supplier.company_id == user.company_id, Supplier.id == agreement.supplier_id))
    data["supplier_name"] = supplier.legal_name if supplier else "Proveedor"
    orders = db.scalars(select(SupplyDocument).where(SupplyDocument.company_id == user.company_id, SupplyDocument.parent_id == agreement.id, SupplyDocument.kind == "PURCHASE_ORDER")).all()
    committed, received, amount = defaultdict(lambda: Decimal("0")), defaultdict(lambda: Decimal("0")), Decimal("0")
    commercial = {item["product_id"]: item for item in details["commercial_lines"]}
    for order in orders:
        if order.status == "cancelled":
            continue
        for line in order.lines:
            quantity = max(Decimal("0"), line.quantity - line.cancelled_quantity)
            committed[line.product_id] += quantity
            received[line.product_id] += line.processed_quantity
            amount += quantity * line.unit_cost * (1 + Decimal(commercial[str(line.product_id)]["tax_rate"]))
    for line in data["lines"]:
        identifier = UUID(line["product_id"])
        item = db.scalar(select(ProductModel).where(ProductModel.company_id == user.company_id, ProductModel.id == identifier))
        line.update(sku=item.sku if item else "", name=item.name if item else "Producto", committed_quantity=str(committed[identifier]), received_quantity=str(received[identifier]), available_quantity=str(max(Decimal("0"), Decimal(line["quantity"]) - committed[identifier])))
    limit = Decimal(details["amount_limit"]) if details.get("amount_limit") else None
    data["committed_amount"] = str(amount.quantize(Decimal("0.000001")))
    data["available_amount"] = str(max(Decimal("0"), limit - amount)) if limit is not None else None
    data["orders"] = [{"id": str(row.id), "status": row.status, "version": row.version, "delivery_date": json.loads(row.details_json or "{}").get("delivery_date")} for row in orders]
    today = business_date(db, user.company_id).isoformat()
    data["can_release"] = agreement.status == "active" and details["valid_from"] <= today <= details["valid_until"] and bool(supplier and supplier_qualified(supplier, business_date(db, user.company_id)))
    return data


def list_agreements(db, user):
    rows = db.scalars(select(SupplyDocument).where(SupplyDocument.company_id == user.company_id, SupplyDocument.kind == "PURCHASE_AGREEMENT").order_by(SupplyDocument.created_at.desc())).all()
    return {"items": [agreement_data(db, user, row) for row in rows]}


def create_agreement(db, user, payload, key):
    record, cached = claim_request(db, user.company_id, "purchase_agreement.create", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    supplier = db.scalar(select(Supplier).where(Supplier.company_id == user.company_id, Supplier.id == payload.supplier_id, Supplier.is_active.is_(True)))
    if supplier is None or payload.valid_until < business_date(db, user.company_id):
        raise HTTPException(422, "Selecciona un proveedor activo y una vigencia que no haya terminado.")
    require_supplier_qualified(db, user, supplier)
    normalized, totals = purchase_line_values(payload.items)
    for item in payload.items:
        product(db, user.company_id, item.product_id)
    details = {**payload.model_dump(mode="json", exclude={"items", "supplier_id", "warehouse_id"}), **totals, "agreement_number": f"ACU-{next_number(db, user.company_id, 'ACU'):08d}"}
    row = create_document(db, user, "PURCHASE_AGREEMENT", "draft", payload.warehouse_id, normalized, supplier_id=payload.supplier_id, details_json=json.dumps(details))
    result = agreement_data(db, user, row)
    record_audit(db, user, row.id, "CREATE_PURCHASE_AGREEMENT", result)
    complete_request(record, result)
    db.commit()
    return result


def agreement_action(db, user, identifier, action, payload, key):
    record, cached = claim_request(db, user.company_id, f"purchase_agreement.{action}:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    row = document(db, user, "PURCHASE_AGREEMENT", identifier)
    if row.version != payload.version or (action == "approve" and row.status != "draft") or (action == "close" and row.status not in ("draft", "active")):
        raise HTTPException(409, "El acuerdo cambió o la acción no corresponde a su estado.")
    if not ({"purchases:approve", "approvals:manage", "organization:manage"} & set(user.permissions)):
        raise HTTPException(403, "Aprobar o cerrar acuerdos requiere autorización de compras o administración.")
    row.status, row.version = ("active" if action == "approve" else "closed"), row.version + 1
    details = json.loads(row.details_json)
    details.setdefault("history", []).append({"action": action, "reason": payload.reason, "actor": user.email, "date": business_date(db, user.company_id).isoformat()})
    row.details_json = json.dumps(details)
    result = agreement_data(db, user, row)
    record_audit(db, user, row.id, "PURCHASE_AGREEMENT_ACTION", {"action": action, "reason": payload.reason, "version": row.version})
    complete_request(record, result)
    db.commit()
    return result


def release_agreement(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"purchase_agreement.release:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    row = document(db, user, "PURCHASE_AGREEMENT", identifier)
    data = agreement_data(db, user, row)
    if row.version != payload.version or not data["can_release"]:
        raise HTTPException(409, "El acuerdo cambió, está cerrado o no está vigente.")
    details = data["details"]
    if not details["valid_from"] <= payload.delivery_date.isoformat() <= details["valid_until"] or payload.delivery_date < business_date(db, user.company_id):
        raise HTTPException(422, "La entrega debe ser futura o de hoy y estar dentro de la vigencia del acuerdo.")
    balances = {UUID(item["product_id"]): item for item in data["lines"]}
    taxes = {UUID(item["product_id"]): Decimal(item["tax_rate"]) for item in details["commercial_lines"]}
    seen, lines, commercial, total, subtotal = set(), [], [], Decimal("0"), Decimal("0")
    for item in payload.items:
        source = balances.get(item.product_id)
        if source is None or item.product_id in seen or item.quantity > Decimal(source["available_quantity"]):
            raise HTTPException(409, "La liberación contiene cantidades repetidas, ajenas o superiores al saldo del acuerdo.")
        seen.add(item.product_id)
        product(db, user.company_id, item.product_id)
        net = (item.quantity * Decimal(source["unit_cost"])).quantize(Decimal("0.000001"))
        tax = (net * taxes[item.product_id]).quantize(Decimal("0.000001"))
        subtotal, total = subtotal + net, total + net + tax
        lines.append(StockLine(product_id=item.product_id, quantity=item.quantity, unit_cost=source["unit_cost"]))
        commercial.append({"product_id": str(item.product_id), "unit_list_cost": source["unit_cost"], "discount_percentage": "0", "tax_rate": str(taxes[item.product_id]), "subtotal": str(net), "tax_amount": str(tax), "total": str(net + tax)})
    if data["available_amount"] is not None and total > Decimal(data["available_amount"]):
        raise HTTPException(409, "La liberación supera el importe disponible del acuerdo.")
    release_details = {"currency": details["currency"], "payment_terms_days": details["payment_terms_days"], "delivery_date": payload.delivery_date.isoformat(), "notes": payload.notes, "commercial_lines": commercial, "subtotal": str(subtotal), "tax_total": str(total - subtotal), "total": str(total), "purchase_agreement_id": str(row.id), "agreement_version": row.version, "agreement_reference": details["reference"]}
    order = create_document(db, user, "PURCHASE_ORDER", "submitted", row.warehouse_id, lines, supplier_id=row.supplier_id, parent_id=row.id, details_json=json.dumps(release_details))
    row.version += 1
    capture_revision(db, user, order, "RELEASE_AGREEMENT", f"Liberación del acuerdo {details['reference']}")
    result = response(order)
    record_audit(db, user, row.id, "RELEASE_PURCHASE_AGREEMENT", {"purchase_order_id": str(order.id), "total": str(total), "agreement_version": row.version})
    complete_request(record, result)
    db.commit()
    return result
