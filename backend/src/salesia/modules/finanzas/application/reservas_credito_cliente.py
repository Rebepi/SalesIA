import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.finanzas.application.credito_tienda import get_customer_store_credit
from salesia.modules.finanzas.application.libro_credito_cliente import credit_book, instant
from salesia.modules.finanzas.infrastructure.models.devoluciones_credito import CustomerCreditReservationModel
from salesia.modules.organizacion.application.periodos import business_date, require_open_period
from salesia.shared.infrastructure.models import PaymentModel, SaleModel
from salesia.modules.finanzas.application.saldos_pago import payment_balances
from salesia.shared.infrastructure.transactions import claim_request, complete_request


class ReserveCreditRequest(BaseModel):
    payment_id: UUID | None = None
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=6)
    source_ids: list[UUID] = Field(default_factory=list, max_length=100)
    duration_hours: int = Field(default=168, ge=1, le=2160)
    expected_sale_version: int = Field(ge=1)
    reason: str = Field(min_length=5, max_length=2000)


class ReleaseCreditRequest(BaseModel):
    expected_version: int = Field(ge=1)
    reason: str = Field(min_length=5, max_length=2000)


def reserve_credit(db, user, sale_id, payload, key):
    required = "payments:write" if payload.payment_id else "sales:write"
    if required not in user.permissions:
        raise HTTPException(403, f"La reserva requiere el permiso {required}.")
    record, cached = claim_request(db, user.company_id, f"credit.reserve:{sale_id}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    sale = db.scalar(select(SaleModel).where(SaleModel.id == sale_id, SaleModel.company_id == user.company_id).with_for_update())
    if sale is None:
        raise HTTPException(404, "Venta no encontrada en la empresa activa.")
    if sale.status != "confirmed" or sale.version != payload.expected_sale_version:
        raise HTTPException(409, "La venta cambió o no admite reservas. Actualice sus datos.")
    now = datetime.now(timezone.utc)
    reservations = db.scalars(select(CustomerCreditReservationModel).where(CustomerCreditReservationModel.company_id == user.company_id, CustomerCreditReservationModel.sale_id == sale.id, CustomerCreditReservationModel.status == "active", CustomerCreditReservationModel.expires_at > now)).all()
    reserved = sum((row.amount for row in reservations), Decimal("0"))
    if payload.amount + reserved > sale.total_amount - sale.paid_amount:
        raise HTTPException(409, "La suma reservada supera la deuda actual de la venta.")
    expires = now + timedelta(hours=payload.duration_hours)
    allocations = []
    if payload.payment_id:
        if payload.source_ids:
            raise HTTPException(422, "Una reserva de anticipo no puede incluir créditos de tienda.")
        payment = db.scalar(select(PaymentModel).where(PaymentModel.company_id == user.company_id, PaymentModel.id == payload.payment_id).with_for_update())
        if payment is None or payment.status != "confirmed" or payment.currency != sale.currency or payment.payment_method in ("RETURN_CREDIT", "EXCHANGE_CREDIT", "STORE_CREDIT"):
            raise HTTPException(409, "El pago no admite reservas de dinero en esta moneda y estado.")
        original = db.scalar(select(SaleModel).where(SaleModel.company_id == user.company_id, SaleModel.id == payment.sale_id))
        if original is None or original.customer_id != sale.customer_id:
            raise HTTPException(409, "El anticipo y la deuda deben corresponder al mismo cliente.")
        if payload.amount > payment_balances(db, user.company_id, payment)["unapplied"]:
            raise HTTPException(409, "El dinero libre del anticipo no cubre la reserva solicitada.")
    else:
        book = credit_book(db, user.company_id, sale.customer_id, sale.currency)
        if book["warnings"]:
            raise HTTPException(409, " ".join(book["warnings"]))
        sources = [item for item in book["sources"] if item["currency"] == sale.currency and Decimal(item["available_amount"]) > 0]
        if payload.source_ids:
            requested = {str(identifier) for identifier in payload.source_ids}
            if not requested.issubset({item["id"] for item in sources}):
                raise HTTPException(409, "Uno de los créditos elegidos dejó de estar disponible.")
            sources = [item for item in sources if item["id"] in requested]
        if sum((Decimal(item["available_amount"]) for item in sources), Decimal("0")) < payload.amount:
            raise HTTPException(409, "El saldo libre de esta moneda no cubre la reserva.")
        sources.sort(key=lambda item: (instant(datetime.fromisoformat(item["expires_at"])) if item["expires_at"] else datetime.max.replace(tzinfo=timezone.utc), instant(datetime.fromisoformat(item["created_at"])), item["id"]))
        needed = payload.amount
        for item in sources:
            amount = min(needed, Decimal(item["available_amount"]))
            allocations.append({"credit_id": item["id"], "amount": str(amount)})
            if item["expires_at"]:
                expires = min(expires, instant(datetime.fromisoformat(item["expires_at"])))
            needed -= amount
            if needed == 0:
                break
    row = CustomerCreditReservationModel(company_id=user.company_id, customer_id=sale.customer_id, sale_id=sale.id, payment_id=payload.payment_id, currency=sale.currency, amount=payload.amount, sources_json=json.dumps(allocations), expires_at=expires, reason=payload.reason, created_by=user.user_id, version=1, status="active")
    db.add(row)
    db.flush()
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="RESERVE_CUSTOMER_CREDIT", entity_type="CustomerCreditReservation", entity_id=row.id, diff={"sale_id": str(sale.id), "payment_id": str(payload.payment_id) if payload.payment_id else None, "amount": str(payload.amount), "currency": sale.currency, "expires_at": expires.isoformat(), "sources": allocations, "reason": payload.reason})
    result = get_customer_store_credit(sale.customer_id, user, db)
    complete_request(record, result)
    db.commit()
    return result


def release_credit(db, user, reservation_id, payload, key):
    record, cached = claim_request(db, user.company_id, f"credit.release:{reservation_id}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    row = db.scalar(select(CustomerCreditReservationModel).where(CustomerCreditReservationModel.company_id == user.company_id, CustomerCreditReservationModel.id == reservation_id).with_for_update())
    if row is None:
        raise HTTPException(404, "Reserva no encontrada en la empresa activa.")
    required = "payments:write" if row.payment_id else "sales:write"
    if required not in user.permissions:
        raise HTTPException(403, f"La liberación requiere el permiso {required}.")
    if row.status != "active" or row.version != payload.expected_version:
        raise HTTPException(409, "La reserva cambió o ya fue aplicada o liberada. Actualice el libro.")
    row.status = "released"
    row.version += 1
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="RELEASE_CUSTOMER_CREDIT", entity_type="CustomerCreditReservation", entity_id=row.id, diff={"amount": str(row.amount), "currency": row.currency, "reason": payload.reason})
    db.flush()
    result = get_customer_store_credit(row.customer_id, user, db)
    complete_request(record, result)
    db.commit()
    return result


def reconcile_sale_reservations(db, user, sale, cancelled=False):
    db.flush()
    rows = db.scalars(select(CustomerCreditReservationModel).where(CustomerCreditReservationModel.company_id == user.company_id, CustomerCreditReservationModel.sale_id == sale.id, CustomerCreditReservationModel.status == "active").order_by(CustomerCreditReservationModel.created_at, CustomerCreditReservationModel.id).with_for_update()).all()
    allowance = Decimal("0") if cancelled else max(Decimal("0"), sale.total_amount - sale.paid_amount)
    now = datetime.now(timezone.utc)
    for row in rows:
        if instant(row.expires_at) <= now:
            continue
        keep = min(allowance, row.amount)
        allowance -= keep
        if keep == row.amount:
            continue
        previous = row.amount
        row.amount = keep
        row.status = "released" if keep == 0 else "active"
        row.version += 1
        needed = keep
        sources = []
        for item in json.loads(row.sources_json):
            amount = min(needed, Decimal(item["amount"]))
            if amount > 0:
                sources.append({"credit_id": item["credit_id"], "amount": str(amount)})
                needed -= amount
        row.sources_json = json.dumps(sources)
        record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="ADJUST_CUSTOMER_CREDIT_RESERVATION", entity_type="CustomerCreditReservation", entity_id=row.id, diff={"sale_id": str(sale.id), "previous_amount": str(previous), "remaining_amount": str(keep), "released_amount": str(previous - keep), "reason": "Venta anulada" if cancelled else "Reducción de deuda por aplicación de un abono"})
