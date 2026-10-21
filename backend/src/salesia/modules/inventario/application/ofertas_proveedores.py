import json
from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from salesia.modules.inventario.application.auxiliares.purchase_line_values import purchase_line_values
from salesia.modules.inventario.application.compras_saldos import capture_revision
from salesia.modules.inventario.application.homologacion_proveedor import supplier_qualified
from salesia.modules.inventario.application.contracts.comunes import PurchaseStockLine
from salesia.modules.inventario.infrastructure_models import Supplier, SupplyDocument
from salesia.modules.inventario.service import create_document, document, product, record_audit, response
from salesia.modules.organizacion.application.periodos import business_date
from salesia.shared.infrastructure.models import CompanyModel, ProductModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request, next_number


class SupplierOfferLine(PurchaseStockLine):
    minimum_quantity: Decimal = Field(default=1, gt=0, max_digits=20, decimal_places=6)
    order_multiple: Decimal = Field(default=1, gt=0, max_digits=20, decimal_places=6)


class SupplierOfferRequest(BaseModel):
    supplier_id: UUID
    supplier_reference: str = Field(min_length=1, max_length=128)
    currency: str = Field(pattern="^[A-Z]{3}$")
    valid_until: date
    lead_time_days: int = Field(ge=0, le=3650)
    warranty_months: int = Field(default=0, ge=0, le=1200)
    shipping_cost: Decimal = Field(default=0, ge=0, max_digits=20, decimal_places=6)
    payment_terms_days: int = Field(default=30, ge=0, le=365)
    notes: str = Field(default="", max_length=4000)
    items: list[SupplierOfferLine] = Field(min_length=1, max_length=500)


class SelectSupplierOfferRequest(BaseModel):
    version: int = Field(ge=1)
    reason: str = Field(min_length=5, max_length=2000)


def serialize_offer(db, user, row):
    data = response(row)
    supplier = db.scalar(select(Supplier).where(Supplier.company_id == user.company_id, Supplier.id == row.supplier_id))
    data["supplier_name"] = supplier.legal_name if supplier else "Proveedor"
    details = data["details"]
    data["is_current"] = row.status == "offered" and details.get("valid_until", "") >= business_date(db, user.company_id).isoformat() and bool(supplier and supplier_qualified(supplier, business_date(db, user.company_id)))
    return data


def create_offer(db, user, requisition_id, payload, key):
    record, cached = claim_request(db, user.company_id, f"supplier_offer.create:{requisition_id}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    requisition = document(db, user, "PURCHASE_REQUISITION", requisition_id)
    if requisition.status != "approved":
        raise HTTPException(409, "Compara ofertas de una requisición aprobada que todavía no se haya convertido.")
    if payload.valid_until < business_date(db, user.company_id):
        raise HTTPException(422, "La oferta ya está vencida.")
    supplier = db.scalar(select(Supplier).where(Supplier.company_id == user.company_id, Supplier.id == payload.supplier_id, Supplier.is_active.is_(True)))
    if supplier is None:
        raise HTTPException(422, "Selecciona un proveedor activo.")
    expected = {line.product_id: line.quantity for line in requisition.lines}
    if len({item.product_id for item in payload.items}) != len(payload.items) or expected != {item.product_id: item.quantity for item in payload.items}:
        raise HTTPException(422, "La oferta debe cubrir los mismos artículos y cantidades de la requisición para compararse.")
    offers = db.scalars(select(SupplyDocument).where(SupplyDocument.company_id == user.company_id, SupplyDocument.kind == "SUPPLIER_OFFER", SupplyDocument.parent_id == requisition_id, SupplyDocument.supplier_id == supplier.id)).all()
    if any(json.loads(row.details_json).get("supplier_reference", "").strip().casefold() == payload.supplier_reference.strip().casefold() for row in offers):
        raise HTTPException(409, "Esta referencia del proveedor ya fue registrada para la requisición.")
    normalized, totals = purchase_line_values(payload.items)
    for item in payload.items:
        product(db, user.company_id, item.product_id)
    details = {**payload.model_dump(mode="json", exclude={"items", "supplier_id"}), **totals, "total_with_shipping": str(Decimal(totals["total"]) + payload.shipping_cost), "conditions": [{"product_id": str(item.product_id), "minimum_quantity": str(item.minimum_quantity), "order_multiple": str(item.order_multiple)} for item in payload.items], "requisition_version": requisition.version, "offer_number": f"OFP-{next_number(db, user.company_id, 'OFP'):08d}"}
    row = create_document(db, user, "SUPPLIER_OFFER", "offered", requisition.warehouse_id, normalized, supplier_id=supplier.id, parent_id=requisition_id, details_json=json.dumps(details))
    result = serialize_offer(db, user, row)
    record_audit(db, user, row.id, "REGISTER_SUPPLIER_OFFER", result)
    complete_request(record, result)
    db.commit()
    return result


def compare_offers(db, user, requisition_id):
    requisition = document(db, user, "PURCHASE_REQUISITION", requisition_id, lock=False)
    offers = db.scalars(select(SupplyDocument).where(SupplyDocument.company_id == user.company_id, SupplyDocument.parent_id == requisition_id, SupplyDocument.kind == "SUPPLIER_OFFER").order_by(SupplyDocument.created_at.desc())).all()
    groups = {}
    results = []
    for offer in offers:
        item = serialize_offer(db, user, offer)
        conditions = {condition["product_id"]: condition for condition in item["details"].get("conditions", [])}
        errors = []
        for line in offer.lines:
            condition = conditions.get(str(line.product_id), {})
            minimum, multiple = Decimal(condition.get("minimum_quantity", "1")), Decimal(condition.get("order_multiple", "1"))
            if line.quantity < minimum or line.quantity % multiple != 0:
                errors.append(f"El artículo {line.product_id} no cumple el mínimo o múltiplo del proveedor.")
        if item["details"].get("requisition_version") != requisition.version:
            errors.append("La requisición cambió desde que se registró la oferta.")
        item["selection_errors"] = errors
        eligible = item["is_current"] and not errors
        item["can_select"] = eligible and requisition.status == "approved"
        currency = item["details"]["currency"]
        if eligible:
            total = Decimal(item["details"]["total_with_shipping"])
            groups[currency] = min(groups.get(currency, total), total)
        results.append(item)
    for item in results:
        item["lowest_in_currency"] = item["can_select"] and Decimal(item["details"]["total_with_shipping"]) == groups.get(item["details"]["currency"])
    requisition_data = response(requisition)
    for line in requisition_data["lines"]:
        item = db.scalar(select(ProductModel).where(ProductModel.company_id == user.company_id, ProductModel.id == UUID(line["product_id"])))
        line["sku"], line["name"] = (item.sku, item.name) if item else ("", "Producto")
    return {"requisition": requisition_data, "offers": results, "lowest_by_currency": {currency: str(total) for currency, total in groups.items()}, "comparison_rule": "Los importes se comparan solo dentro de la misma moneda; la elección debe justificar precio, plazo, garantía y condiciones."}


def select_offer(db, user, offer_id, payload, key):
    record, cached = claim_request(db, user.company_id, f"supplier_offer.select:{offer_id}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    db.scalar(select(CompanyModel).where(CompanyModel.id == user.company_id).with_for_update())
    offer = document(db, user, "SUPPLIER_OFFER", offer_id)
    if offer.version != payload.version:
        raise HTTPException(409, "La oferta cambió; vuelve a consultar las condiciones.")
    requisition = document(db, user, "PURCHASE_REQUISITION", offer.parent_id)
    comparison = compare_offers(db, user, requisition.id)
    selected = next(item for item in comparison["offers"] if item["id"] == str(offer.id))
    if not selected["can_select"]:
        raise HTTPException(409, "La oferta no está vigente o la requisición ya fue convertida.")
    details = json.loads(offer.details_json)
    for line in offer.lines:
        product(db, user.company_id, line.product_id)
    order_details = {"currency": details["currency"], "payment_terms_days": details["payment_terms_days"], "delivery_date": None, "notes": details.get("notes", ""), "commercial_lines": details["commercial_lines"], "subtotal": details["subtotal"], "tax_total": details["tax_total"], "total": details["total"], "shipping_cost_agreed": details["shipping_cost"], "total_with_shipping": details["total_with_shipping"], "supplier_offer_id": str(offer.id), "supplier_offer_snapshot": selected, "selection_reason": payload.reason, "comparison_snapshot": comparison["offers"], "source_requisition_id": str(requisition.id)}
    from datetime import timedelta
    order_details["delivery_date"] = (business_date(db, user.company_id) + timedelta(days=details["lead_time_days"])).isoformat()
    order = create_document(db, user, "PURCHASE_ORDER", "submitted", requisition.warehouse_id, offer.lines, supplier_id=offer.supplier_id, parent_id=requisition.id, details_json=json.dumps(order_details))
    requisition.status, requisition.version = "converted", requisition.version + 1
    requisition.details_json = json.dumps({**json.loads(requisition.details_json or "{}"), "purchase_order_id": str(order.id)})
    offer.status, offer.version = "selected", offer.version + 1
    details["purchase_order_id"], details["selection_reason"] = str(order.id), payload.reason
    offer.details_json = json.dumps(details)
    capture_revision(db, user, order, "SELECT_OFFER", payload.reason)
    record_audit(db, user, order.id, "SELECT_SUPPLIER_OFFER", {"offer_id": str(offer.id), "reason": payload.reason, "lowest_in_currency": selected["lowest_in_currency"], "alternatives": [item["id"] for item in comparison["offers"]]})
    result = response(order)
    complete_request(record, result)
    db.commit()
    return result
