import json
from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select

from salesia.modules.pedidos.application.auxiliares.audit import audit
from salesia.modules.pedidos.application.auxiliares.price_lines import price_lines
from salesia.modules.pedidos.application.auxiliares.quotation_response import quotation_response
from salesia.modules.pedidos.application.contracts.pedidos_registro import DocumentLine
from salesia.shared.infrastructure.models import QuotationModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


class QuotationReviewRequest(BaseModel):
    version: int = Field(ge=1)
    reason: str = Field(min_length=3, max_length=2000)
    action: Literal["negotiate", "reject", "renew"]
    valid_until: Optional[datetime] = None
    keep_prices: bool = True

    @model_validator(mode="after")
    def validate_expiration(self):
        if self.action == "renew" and (self.valid_until is None or self.valid_until.tzinfo is None or self.valid_until <= datetime.now(timezone.utc)):
            raise ValueError("La renovación requiere un vencimiento futuro con zona horaria.")
        return self


def quotation(db, user, identifier, lock=False):
    statement = select(QuotationModel).where(QuotationModel.company_id == user.company_id, QuotationModel.id == identifier)
    row = db.scalar(statement.with_for_update() if lock else statement)
    if row is None:
        raise HTTPException(404, "Cotización no encontrada.")
    return row


def list_versions(db, user, identifier):
    row = quotation(db, user, identifier)
    rows = db.scalars(select(QuotationModel).where(QuotationModel.company_id == user.company_id, QuotationModel.quotation_number == row.quotation_number).order_by(QuotationModel.version)).all()
    return [quotation_response(item) for item in rows]


def compare_versions(db, user, left_id, right_id):
    left, right = quotation(db, user, left_id), quotation(db, user, right_id)
    if left.quotation_number != right.quotation_number:
        raise HTTPException(422, "Selecciona versiones de la misma cotización.")
    fields = ("currency", "valid_until", "payment_terms_days", "delivery_terms", "notes", "special_conditions", "subtotal_amount", "tax_amount", "total_amount")
    changes = [{"field": field, "before": str(getattr(left, field)) if getattr(left, field) is not None else None, "after": str(getattr(right, field)) if getattr(right, field) is not None else None} for field in fields if getattr(left, field) != getattr(right, field)]
    def indexed(lines):
        counts, result = {}, {}
        for line in lines:
            product_id = line["product_id"]
            counts[product_id] = counts.get(product_id, 0) + 1
            result[(product_id, counts[product_id])] = line
        return result
    before, after = indexed(json.loads(left.lines_json)), indexed(json.loads(right.lines_json))
    lines = []
    for key in sorted(set(before) | set(after)):
        previous, current = before.get(key), after.get(key)
        if previous == current:
            continue
        lines.append({"product_id": key[0], "occurrence": key[1], "name": (current or previous).get("name"), "change": "added" if previous is None else "removed" if current is None else "modified", "before": previous, "after": current})
    return {"number": left.quotation_number, "before_version": left.version, "after_version": right.version, "changes": changes, "lines": lines}


def review_quotation(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"quotations.review:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    row = quotation(db, user, identifier, True)
    if row.version != payload.version or row.status in ("converted", "superseded") or row.converted_order_id:
        raise HTTPException(409, "La cotización cambió o ya no admite esta revisión.")
    if payload.action == "renew":
        existing = db.scalar(select(QuotationModel.id).where(QuotationModel.company_id == user.company_id, QuotationModel.quotation_number == row.quotation_number, QuotationModel.version > row.version))
        if existing:
            raise HTTPException(409, "Solo se renueva la versión más reciente.")
        lines = json.loads(row.lines_json)
        if payload.keep_prices:
            subtotal, tax, total = row.subtotal_amount, row.tax_amount, row.total_amount
        else:
            requested = [DocumentLine(product_id=line["product_id"], quantity=line["quantity"], discount_pct=line.get("discount_pct", "0")) for line in lines]
            lines, subtotal, tax, total = price_lines(db, user.company_id, requested)
        new_row = QuotationModel(company_id=user.company_id, branch_id=row.branch_id, customer_id=row.customer_id, quotation_number=row.quotation_number, version=row.version + 1, status="pending", currency=row.currency, subtotal_amount=subtotal, tax_amount=tax, total_amount=total, valid_until=payload.valid_until.isoformat(), payment_terms_days=row.payment_terms_days, delivery_terms=row.delivery_terms, notes=row.notes, special_conditions=row.special_conditions, seller_id=row.seller_id, lines_json=json.dumps(lines))
        row.status = "superseded"
        db.add(new_row)
        db.flush()
        audit(db, user, "RENEW", "Quotation", new_row.id, {"previous_id": str(row.id), "reason": payload.reason, "kept_prices": payload.keep_prices})
        result = quotation_response(new_row)
    else:
        if row.status not in ("draft", "pending", "negotiating", "rejected"):
            raise HTTPException(409, "La cotización no admite este cambio de negociación.")
        row.status = "negotiating" if payload.action == "negotiate" else "rejected"
        log = json.loads(row.communication_log_json or "[]")
        log.append({"event": payload.action.upper(), "reason": payload.reason, "actor": user.email, "at": datetime.now(timezone.utc).isoformat()})
        row.communication_log_json = json.dumps(log)
        audit(db, user, payload.action.upper(), "Quotation", row.id, {"reason": payload.reason})
        result = quotation_response(row)
    complete_request(record, result)
    db.commit()
    return result
