from decimal import Decimal
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import String, case, func, select

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.finanzas.application.libro_credito_cliente import credit_book
from salesia.modules.finanzas.infrastructure_models import CustomerCreditMovementModel
from salesia.modules.finanzas.infrastructure.models.pagos import PaymentAllocationModel, PaymentReversalModel
from salesia.modules.finanzas.infrastructure.models.devoluciones_credito import CustomerCreditReservationModel
from salesia.modules.organizacion.application.periodos import business_date, require_open_period
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import CustomerModel, PaymentModel, SaleModel
from salesia.shared.infrastructure.transactions import RefundModel, claim_request, complete_request


def scoped_customer(db, user, customer_id):
    row = db.scalar(select(CustomerModel).where(CustomerModel.id == customer_id, CustomerModel.company_id == user.company_id))
    if row is None:
        raise HTTPException(404, "Cliente no encontrado en la empresa activa.")
    return row


def get_customer_store_credit(customer_id: UUID, current_user: AuthenticatedUser, db, currency=None):
    scoped_customer(db, current_user, customer_id)
    book = credit_book(db, current_user.company_id, customer_id, currency)
    matching = [row for row in book["balances"] if currency is None or row["currency"] == currency]
    selected_currency = currency or (matching[0]["currency"] if len(matching) == 1 else None)
    unapplied = unapplied_payments(db, current_user, customer_id, currency)
    return {
        "customer_id": str(customer_id),
        "currency": selected_currency,
        "available_balance": next((item["available_balance"] for item in matching if item["currency"] == selected_currency), "0") if selected_currency else None,
        "balances": matching,
        "can_apply": book["can_apply"],
        "warnings": book["warnings"],
        "sources": book["sources"],
        "reservations": book["reservations"],
        "unapplied_payments": unapplied,
        "unapplied_balances": [{"currency": value, "available_amount": str(sum((Decimal(item["available_amount"]) for item in unapplied if item["currency"] == value), Decimal("0"))), "reserved_amount": str(sum((Decimal(item["reserved_amount"]) for item in unapplied if item["currency"] == value), Decimal("0")))} for value in sorted({item["currency"] for item in unapplied})],
        "allocations": book["allocations"],
        "movements": [{"id": str(row.id), "movement_type": row.movement_type, "currency": row.currency, "amount_delta": str(row.amount_delta), "balance_at_recording": str(row.resulting_balance), "reference_type": row.reference_type, "reference_id": str(row.reference_id) if row.reference_id else None, "payment_id": str(row.payment_id) if row.payment_id else None, "notes": row.notes, "expires_at": row.expires_at.isoformat() if row.expires_at else None, "created_at": row.created_at.isoformat(), "updated_at": row.updated_at.isoformat()} for row in reversed(book["rows"]) if currency is None or row.currency == currency or row.currency is None],
    }


def unapplied_payments(db, user, customer_id, currency=None):
    allocated = select(PaymentAllocationModel.payment_id.label("payment_id"), func.sum(PaymentAllocationModel.allocated_amount).label("amount")).where(PaymentAllocationModel.company_id == user.company_id).group_by(PaymentAllocationModel.payment_id).subquery()
    refunded = select(RefundModel.payment_id.label("payment_id"), func.sum(RefundModel.amount).label("amount"), func.sum(case((RefundModel.unapplied_only.is_(True), RefundModel.amount), else_=0)).label("unapplied_amount")).where(RefundModel.company_id == user.company_id).group_by(RefundModel.payment_id).subquery()
    reversed_rows = select(PaymentReversalModel.payment_id.label("payment_id"), func.sum(PaymentReversalModel.amount).label("amount")).where(PaymentReversalModel.company_id == user.company_id).group_by(PaymentReversalModel.payment_id).subquery()
    held = select(CustomerCreditReservationModel.payment_id.label("payment_id"), func.sum(CustomerCreditReservationModel.amount).label("amount")).where(CustomerCreditReservationModel.company_id == user.company_id, CustomerCreditReservationModel.payment_id.is_not(None), CustomerCreditReservationModel.status == "active", CustomerCreditReservationModel.expires_at > datetime.now(timezone.utc)).group_by(CustomerCreditReservationModel.payment_id).subquery()
    query = select(PaymentModel, SaleModel, func.coalesce(allocated.c.amount, 0), func.coalesce(refunded.c.amount, 0), func.coalesce(reversed_rows.c.amount, 0), func.coalesce(refunded.c.unapplied_amount, 0), func.coalesce(held.c.amount, 0)).join(SaleModel, SaleModel.id == PaymentModel.sale_id).outerjoin(allocated, allocated.c.payment_id == PaymentModel.id).outerjoin(refunded, refunded.c.payment_id == PaymentModel.id).outerjoin(reversed_rows, reversed_rows.c.payment_id == PaymentModel.id).outerjoin(held, held.c.payment_id == PaymentModel.id).where(PaymentModel.company_id == user.company_id, SaleModel.company_id == user.company_id, SaleModel.customer_id == customer_id, PaymentModel.status == "confirmed", PaymentModel.payment_method.notin_(("RETURN_CREDIT", "EXCHANGE_CREDIT", "STORE_CREDIT")))
    if currency:
        query = query.where(PaymentModel.currency == currency)
    items = []
    for payment, sale, assigned, refunds, reversals, unapplied_refunds, reserved in db.execute(query.order_by(PaymentModel.created_at, PaymentModel.id)).all():
        available = max(Decimal("0"), min(payment.amount - refunds - reversals, payment.amount - assigned - unapplied_refunds - reversals) - reserved)
        if available > 0 or reserved > 0:
            items.append({"id": str(payment.id), "sale_id": str(sale.id), "document_number": f"{sale.series}-{sale.number:08d}", "currency": payment.currency, "amount": str(payment.amount), "allocated_amount": str(assigned), "refunded_amount": str(refunds), "available_amount": str(available), "reserved_amount": str(reserved), "payment_method": payment.payment_method, "reference_code": payment.reference_code, "created_at": payment.created_at.isoformat()})
    return items


def eligible_credit_sales(db, user, customer_id, currency, search=None, limit=20, offset=0):
    scoped_customer(db, user, customer_id)
    query = select(SaleModel).where(SaleModel.company_id == user.company_id, SaleModel.customer_id == customer_id, SaleModel.currency == currency, SaleModel.status == "confirmed", SaleModel.paid_amount < SaleModel.total_amount)
    if search:
        term = f"%{search.strip()}%"
        query = query.where(SaleModel.series.ilike(term) | SaleModel.number.cast(String).ilike(term))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.order_by(SaleModel.created_at, SaleModel.id).limit(limit).offset(offset)).all()
    return {"total_count": total, "items": [{"id": str(row.id), "document_number": f"{row.series}-{row.number:08d}", "currency": row.currency, "unpaid_amount": str(row.total_amount - row.paid_amount), "version": row.version} for row in rows]}


class CreditCurrencyRequest(BaseModel):
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    expected_amount: Decimal = Field(max_digits=20, decimal_places=6)
    reason: str = Field(min_length=10, max_length=2000)
    evidence_reference: str = Field(min_length=5, max_length=255)


def identify_credit_currency(db, user, customer_id, movement_id, payload, key):
    record, cached = claim_request(db, user.company_id, f"credit.identify_currency:{movement_id}", key, {"customer_id": str(customer_id), **payload.model_dump(mode="json")})
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    scoped_customer(db, user, customer_id)
    movement = db.scalar(select(CustomerCreditMovementModel).where(CustomerCreditMovementModel.id == movement_id, CustomerCreditMovementModel.company_id == user.company_id, CustomerCreditMovementModel.customer_id == customer_id).with_for_update())
    if movement is None:
        raise HTTPException(404, "Movimiento no encontrado en el cliente activo.")
    if movement.currency is not None or movement.amount_delta != payload.expected_amount:
        raise HTTPException(409, "El movimiento cambió o ya tiene una moneda identificada. Actualice el libro.")
    movement.currency = payload.currency
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="IDENTIFY_CUSTOMER_CREDIT_CURRENCY", entity_type="CustomerCreditMovement", entity_id=movement.id, diff={"currency": payload.currency, "amount": str(movement.amount_delta), "reason": payload.reason, "evidence_reference": payload.evidence_reference})
    db.flush()
    result = get_customer_store_credit(customer_id, user, db)
    complete_request(record, result)
    db.commit()
    return result
