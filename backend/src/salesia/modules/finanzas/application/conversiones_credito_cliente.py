import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP, localcontext
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.finanzas.application.credito_tienda import scoped_customer
from salesia.modules.finanzas.application.libro_credito_cliente import accrue_credit, consume_credit, credit_book, instant
from salesia.modules.finanzas.infrastructure.models.devoluciones_credito import CustomerCreditAllocationModel, CustomerCreditConversionModel, CustomerCreditMovementModel
from salesia.modules.organizacion.application.periodos import business_date, require_open_period
from salesia.shared.infrastructure.transactions import claim_request, complete_request


class CreditConversionRequest(BaseModel):
    source_currency: str = Field(pattern=r"^[A-Z]{3}$")
    target_currency: str = Field(pattern=r"^[A-Z]{3}$")
    source_amount: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    rate: Decimal = Field(gt=0, max_digits=20, decimal_places=10)
    rate_reference: str = Field(min_length=5, max_length=255)
    reason: str = Field(min_length=5, max_length=2000)
    source_ids: list[UUID] = Field(default_factory=list, max_length=100)
    valid_hours: int = Field(default=24, ge=1, le=168)


class CreditConversionReview(BaseModel):
    expected_version: int = Field(ge=1)
    action: Literal["approve", "reject", "cancel"]
    reason: str = Field(min_length=5, max_length=2000)


def conversion_data(row):
    expired = row.status == "pending" and instant(row.expires_at) <= datetime.now(timezone.utc)
    return {"id": str(row.id), "customer_id": str(row.customer_id), "source_currency": row.source_currency, "target_currency": row.target_currency, "source_amount": str(row.source_amount), "target_amount": str(row.target_amount), "rate": str(row.rate), "rounding": "HALF_UP_6_DECIMALS", "rate_reference": row.rate_reference, "reason": row.reason, "status": "expired" if expired else row.status, "expires_at": row.expires_at.isoformat(), "created_by": str(row.created_by), "reviewed_by": str(row.reviewed_by) if row.reviewed_by else None, "review_reason": row.review_reason, "source_ids": json.loads(row.source_ids_json), "debit_id": str(row.debit_id) if row.debit_id else None, "credit_id": str(row.credit_id) if row.credit_id else None, "version": row.version, "created_at": row.created_at.isoformat()}


def list_conversions(db, user, customer_id, limit=20, offset=0):
    scoped_customer(db, user, customer_id)
    query = select(CustomerCreditConversionModel).where(CustomerCreditConversionModel.company_id == user.company_id, CustomerCreditConversionModel.customer_id == customer_id)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.order_by(CustomerCreditConversionModel.created_at.desc(), CustomerCreditConversionModel.id).limit(limit).offset(offset)).all()
    return {"total_count": total, "items": [conversion_data(row) for row in rows], "actor_id": str(user.user_id)}


def propose_conversion(db, user, customer_id, payload, key):
    record, cached = claim_request(db, user.company_id, f"credit.convert:{customer_id}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    scoped_customer(db, user, customer_id)
    if payload.source_currency == payload.target_currency:
        raise HTTPException(422, "La conversión requiere dos monedas distintas.")
    with localcontext() as context:
        context.prec = 50
        target = (payload.source_amount * payload.rate).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    if target <= 0 or target >= Decimal("100000000000000"):
        raise HTTPException(422, "El importe convertido no cabe en la precisión del libro de créditos.")
    book = credit_book(db, user.company_id, customer_id, payload.source_currency)
    if book["warnings"]:
        raise HTTPException(409, " ".join(book["warnings"]))
    sources = [item for item in book["sources"] if item["currency"] == payload.source_currency and Decimal(item["available_amount"]) > 0]
    if payload.source_ids:
        selected = {str(identifier) for identifier in payload.source_ids}
        if not selected.issubset({item["id"] for item in sources}):
            raise HTTPException(409, "Los créditos elegidos no están disponibles en la moneda de origen.")
        sources = [item for item in sources if item["id"] in selected]
    if sum((Decimal(item["available_amount"]) for item in sources), Decimal("0")) < payload.source_amount:
        raise HTTPException(409, "El crédito libre no cubre la conversión solicitada.")
    row = CustomerCreditConversionModel(company_id=user.company_id, customer_id=customer_id, source_currency=payload.source_currency, target_currency=payload.target_currency, source_amount=payload.source_amount, target_amount=target, rate=payload.rate, rate_reference=payload.rate_reference, reason=payload.reason, source_ids_json=json.dumps([str(identifier) for identifier in payload.source_ids]), expires_at=datetime.now(timezone.utc) + timedelta(hours=payload.valid_hours), status="pending", created_by=user.user_id, version=1)
    db.add(row)
    db.flush()
    result = conversion_data(row)
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="PROPOSE_CUSTOMER_CREDIT_CONVERSION", entity_type="CustomerCreditConversion", entity_id=row.id, diff=result)
    complete_request(record, result)
    db.commit()
    return result


def review_conversion(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"credit.convert.review:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    row = db.scalar(select(CustomerCreditConversionModel).where(CustomerCreditConversionModel.company_id == user.company_id, CustomerCreditConversionModel.id == identifier).with_for_update())
    if row is None:
        raise HTTPException(404, "Conversión no encontrada en la empresa activa.")
    if row.status != "pending" or row.version != payload.expected_version:
        raise HTTPException(409, "La conversión cambió o ya fue resuelta. Actualice su historial.")
    if payload.action == "cancel":
        if row.created_by != user.user_id and not ({"organization:manage", "approvals:manage"} & set(user.permissions)):
            raise HTTPException(403, "Solo quien solicitó la conversión o un supervisor puede cancelarla.")
        row.status = "cancelled"
    else:
        from salesia.modules.seguridad.application.separacion_funciones import enforce
        enforce(db, user, "credit_conversion", [row.created_by], "CustomerCreditConversion", row.id)
        if row.created_by == user.user_id:
            raise HTTPException(403, "La revisión de la conversión debe realizarla otra persona autorizada.")
        if payload.action == "approve":
            if instant(row.expires_at) <= datetime.now(timezone.utc):
                raise HTTPException(409, "La propuesta venció. Registre una nueva tasa y solicite otra conversión.")
            debit = consume_credit(db, user.company_id, row.customer_id, row.source_currency, row.source_amount, None, None, f"Conversión documentada {row.id}: {payload.reason}", source_ids=[UUID(value) for value in json.loads(row.source_ids_json)], reference_type="CURRENCY_CONVERSION", reference_id=row.id)
            deadlines = db.scalars(select(CustomerCreditMovementModel.expires_at).join(CustomerCreditAllocationModel, CustomerCreditAllocationModel.credit_id == CustomerCreditMovementModel.id).where(CustomerCreditAllocationModel.company_id == user.company_id, CustomerCreditAllocationModel.debit_id == debit.id, CustomerCreditMovementModel.company_id == user.company_id, CustomerCreditMovementModel.expires_at.is_not(None))).all()
            credit = accrue_credit(db, user.company_id, row.customer_id, row.target_currency, row.target_amount, "CURRENCY_CONVERSION", row.id, f"Conversión de {row.source_amount} {row.source_currency} a tasa {row.rate}: {row.rate_reference}", expires_at=min((instant(value) for value in deadlines), default=None))
            row.debit_id = debit.id
            row.credit_id = credit.id
            row.status = "approved"
        else:
            row.status = "rejected"
    row.reviewed_by = user.user_id
    row.review_reason = payload.reason
    row.version += 1
    db.flush()
    result = conversion_data(row)
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="REVIEW_CUSTOMER_CREDIT_CONVERSION", entity_type="CustomerCreditConversion", entity_id=row.id, diff=result)
    complete_request(record, result)
    db.commit()
    return result
