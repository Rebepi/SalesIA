import json
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import String, func, select

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.finanzas.application.libro_credito_cliente import accrue_credit
from salesia.modules.finanzas.application.politicas_devolucion import return_valuation
from salesia.modules.finanzas.infrastructure.models.devoluciones_credito import CreditNoteModel, CustomerCreditMovementModel, ReturnModel
from salesia.modules.finanzas.infrastructure.models.liquidaciones_devolucion import ReturnSettlementMovementModel
from salesia.modules.finanzas.infrastructure.models.pagos import PaymentAllocationModel
from salesia.shared.infrastructure.models import CustomerModel, PaymentModel, SaleModel
from salesia.shared.infrastructure.transactions import RefundModel, claim_request, complete_request
from salesia.modules.organizacion.application.periodos import business_date, require_open_period

SCALE = Decimal("0.000001")


def scoped_return(db, user, identifier, lock=False):
    query = select(ReturnModel).where(ReturnModel.company_id == user.company_id, ReturnModel.id == identifier)
    row = db.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise HTTPException(404, "Devolución no encontrada en la empresa activa.")
    return row


def original_sale(db, user, ret, lock=False):
    query = select(SaleModel).where(SaleModel.company_id == user.company_id, SaleModel.id == ret.sale_id)
    row = db.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise HTTPException(409, "La devolución debe tener una venta original identificada para liquidarla.")
    return row


def settlement_data(db, user, ret):
    db.flush()
    sale = original_sale(db, user, ret)
    valuation = return_valuation(ret)
    total = Decimal(valuation["refundable_total"])
    rows = db.scalars(select(ReturnSettlementMovementModel).where(ReturnSettlementMovementModel.company_id == user.company_id, ReturnSettlementMovementModel.return_id == ret.id).order_by(ReturnSettlementMovementModel.created_at, ReturnSettlementMovementModel.id)).all()
    entries = [{"id": str(row.id), "kind": row.kind, "reference_id": str(row.reference_id), "amount": str(row.amount), "currency": row.currency, "details": json.loads(row.details_json), "created_at": row.created_at.isoformat(), "legacy": False} for row in rows]
    warnings = []
    references = {(row.kind, row.reference_id) for row in rows}
    if not json.loads(ret.details_json or "{}").get("settlement_version"):
        unlinked = db.scalar(select(RefundModel.id).join(PaymentModel, PaymentModel.id == RefundModel.payment_id).where(RefundModel.company_id == user.company_id, PaymentModel.company_id == user.company_id, PaymentModel.sale_id == sale.id, RefundModel.return_id.is_(None), RefundModel.unapplied_only.is_(False)).limit(1))
        if unlinked:
            warnings.append("La venta tiene reembolsos históricos sin devolución identificada; concilie sus aplicaciones antes de disponer de más valor.")
        if ret.credit_note_id:
            credits = db.scalars(select(CustomerCreditMovementModel).where(CustomerCreditMovementModel.company_id == user.company_id, CustomerCreditMovementModel.reference_type == "CREDIT_NOTE", CustomerCreditMovementModel.reference_id == ret.credit_note_id, CustomerCreditMovementModel.amount_delta > 0)).all()
            for credit in credits:
                if ("store_credit", credit.id) not in references:
                    entries.append({"id": str(credit.id), "kind": "store_credit", "reference_id": str(credit.id), "amount": str(credit.amount_delta), "currency": sale.currency, "details": {"historical_source": "customer_credit_movement"}, "created_at": credit.created_at.isoformat(), "legacy": True})
        if ret.exchange_sale_id and ("exchange", ret.exchange_sale_id) not in references:
            exchange = db.scalar(select(SaleModel).where(SaleModel.company_id == user.company_id, SaleModel.id == ret.exchange_sale_id))
            note = db.scalar(select(CreditNoteModel).where(CreditNoteModel.company_id == user.company_id, CreditNoteModel.id == ret.credit_note_id)) if ret.credit_note_id else None
            if exchange and note and exchange.currency == sale.currency:
                amount = min(note.total_amount, exchange.total_amount)
                if amount > 0:
                    entries.append({"id": str(exchange.id), "kind": "exchange", "reference_id": str(exchange.id), "amount": str(amount), "currency": sale.currency, "details": {"historical_source": "exchange_sale"}, "created_at": exchange.created_at.isoformat(), "legacy": True})
            else:
                warnings.append("El cambio histórico requiere revisar su importe y moneda antes de otra liquidación.")
        refunds = db.scalars(select(RefundModel).where(RefundModel.company_id == user.company_id, RefundModel.return_id == ret.id)).all()
        for refund in refunds:
            if ("refund", refund.id) in references:
                continue
            if refund.currency != sale.currency:
                warnings.append("Existe un reembolso histórico en otra moneda que requiere conciliación previa.")
            else:
                entries.append({"id": str(refund.id), "kind": "refund", "reference_id": str(refund.id), "amount": str(refund.amount), "currency": refund.currency, "details": {"historical_source": "payment_refund", "status": refund.status}, "created_at": refund.created_at.isoformat(), "legacy": True})
    applied = sum((Decimal(item["amount"]) for item in entries), Decimal("0"))
    if applied > total:
        warnings.append("Las aplicaciones históricas superan la valoración. Se requiere conciliar antes de continuar.")
    return {"return_id": str(ret.id), "sale_id": str(sale.id), "currency": sale.currency, "can_grant_store_credit": True, "valuation": valuation, "available_amount": str(max(Decimal("0"), total - applied)), "applied_amount": str(applied), "movements": entries, "warnings": warnings, "can_settle": ret.status == "accepted" and not warnings, "sale_balance": str(max(Decimal("0"), sale.total_amount - sale.paid_amount)), "debt_to_offset": str(min(max(Decimal("0"), total - applied), max(Decimal("0"), sale.total_amount - sale.paid_amount))), "remaining_financial_amount": str(max(Decimal("0"), total - applied - max(Decimal("0"), sale.total_amount - sale.paid_amount)))}


def adopt_legacy(db, user, ret):
    if json.loads(ret.details_json or "{}").get("settlement_version"):
        return
    data = settlement_data(db, user, ret)
    if data["warnings"]:
        raise HTTPException(409, " ".join(data["warnings"]))
    for item in data["movements"]:
        if item["legacy"]:
            db.add(ReturnSettlementMovementModel(company_id=user.company_id, return_id=ret.id, kind=item["kind"], reference_id=UUID(item["reference_id"]), amount=Decimal(item["amount"]), currency=data["currency"], details_json=json.dumps(item["details"]), created_by=user.user_id))
    details = json.loads(ret.details_json or "{}")
    details["settlement_version"] = 1
    ret.details_json = json.dumps(details)
    db.flush()


def use_value(db, user, ret, kind, reference_id, amount, details=None):
    adopt_legacy(db, user, ret)
    data = settlement_data(db, user, ret)
    if not data["can_settle"] or amount <= 0 or amount > Decimal(data["available_amount"]):
        raise HTTPException(409, "El importe supera el valor disponible de la devolución después de retenciones y aplicaciones previas.")
    row = ReturnSettlementMovementModel(company_id=user.company_id, return_id=ret.id, kind=kind, reference_id=reference_id, amount=amount, currency=data["currency"], details_json=json.dumps(details or {}), created_by=user.user_id)
    db.add(row)
    db.flush()
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="APPLY_RETURN_VALUE", entity_type="Return", entity_id=ret.id, diff={"movement_id": str(row.id), "kind": kind, "amount": str(amount), "currency": data["currency"], "reference_id": str(reference_id)})
    return row


def credit_sale(db, user, ret, sale, amount, reference):
    if amount <= 0:
        return None
    if sale.paid_amount + amount > sale.total_amount:
        raise HTTPException(409, "El ajuste de devolución supera la deuda disponible de la venta.")
    payment = PaymentModel(id=uuid4(), company_id=user.company_id, sale_id=sale.id, payment_method="RETURN_CREDIT", amount=amount, currency=sale.currency, reference_code=reference, status="confirmed")
    db.add(payment)
    db.flush()
    allocation = PaymentAllocationModel(company_id=user.company_id, payment_id=payment.id, sale_id=sale.id, allocated_amount=amount)
    db.add(allocation)
    sale.paid_amount += amount
    sale.version += 1
    sale.status = "paid" if sale.paid_amount == sale.total_amount else "confirmed"
    if sale.is_credit:
        customer = db.scalar(select(CustomerModel).where(CustomerModel.company_id == user.company_id, CustomerModel.id == sale.customer_id).with_for_update())
        if customer:
            customer.current_balance = max(Decimal("0"), customer.current_balance - amount)
    from salesia.modules.finanzas.application.cuotas_cobranza import assign_installments
    assign_installments(db, user, sale, allocation)
    return payment


def initial_settlement(db, user, ret, action):
    sale = original_sale(db, user, ret, True)
    adopt_legacy(db, user, ret)
    available = Decimal(settlement_data(db, user, ret)["available_amount"])
    unpaid = max(Decimal("0"), sale.total_amount - sale.paid_amount)
    offset = min(available, unpaid)
    if offset > 0:
        credit = credit_sale(db, user, ret, sale, offset, f"RETURN-DEBT-{ret.id}")
        use_value(db, user, ret, "debt_offset", credit.id, offset)
    if action == "STORE_CREDIT":
        amount = Decimal(settlement_data(db, user, ret)["available_amount"])
        if amount > 0:
            movement = accrue_credit(db, user.company_id, sale.customer_id, sale.currency, amount, "RETURN", ret.id, f"Valor disponible de devolución {ret.id}")
            use_value(db, user, ret, "store_credit", movement.id, amount)
    return settlement_data(db, user, ret)


class SettlementRequest(BaseModel):
    expected_available: Decimal = Field(ge=0, max_digits=20, decimal_places=6)
    reason: str = Field(min_length=5, max_length=2000)


class StoreCreditRequest(SettlementRequest):
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=6)


def grant_store_credit(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"return.store_credit:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    ret = scoped_return(db, user, identifier, True)
    if ret.status != "accepted":
        raise HTTPException(409, "La devolución debe estar aceptada antes de disponer de su valor.")
    data = settlement_data(db, user, ret)
    if Decimal(data["available_amount"]) != payload.expected_available:
        raise HTTPException(409, "La disponibilidad de la devolución cambió. Consulte su liquidación antes de continuar.")
    initial_settlement(db, user, ret, "CREDIT_NOTE")
    sale = original_sale(db, user, ret)
    movement = accrue_credit(db, user.company_id, sale.customer_id, sale.currency, payload.amount, "RETURN", ret.id, payload.reason)
    use_value(db, user, ret, "store_credit", movement.id, payload.amount, {"reason": payload.reason})
    result = settlement_data(db, user, ret)
    complete_request(record, result)
    db.commit()
    return result


def list_settlements(db, user, search=None, limit=25, offset=0):
    query = select(ReturnModel).join(SaleModel, SaleModel.id == ReturnModel.sale_id).where(ReturnModel.company_id == user.company_id, SaleModel.company_id == user.company_id, ReturnModel.status == "accepted")
    if search:
        term = f"%{search.strip()}%"
        query = query.where(ReturnModel.id.cast(String).ilike(term) | SaleModel.series.ilike(term) | ReturnModel.reason.ilike(term))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.order_by(ReturnModel.created_at.desc(), ReturnModel.id).limit(limit).offset(offset)).all()
    items = []
    for ret in rows:
        sale = original_sale(db, user, ret)
        data = settlement_data(db, user, ret)
        data["document_number"] = f"{sale.series}-{sale.number:08d}"
        data["reason"] = ret.reason
        data["created_at"] = ret.created_at.isoformat()
        items.append(data)
    return {"items": items, "total_count": total}


def settle_debt(db, user, identifier, payload, key):
    record, cached = claim_request(db, user.company_id, f"return.settle_debt:{identifier}", key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, user.company_id, business_date(db, user.company_id))
    ret = scoped_return(db, user, identifier, True)
    data = settlement_data(db, user, ret)
    if Decimal(data["available_amount"]) != payload.expected_available or ret.status != "accepted":
        raise HTTPException(409, "La disponibilidad cambió o la devolución no está aceptada.")
    result = initial_settlement(db, user, ret, "CREDIT_NOTE")
    record_audit_event(db, company_id=user.company_id, actor_id=user.user_id, actor_email=user.email, action="SETTLE_RETURN_DEBT", entity_type="Return", entity_id=ret.id, diff={"reason": payload.reason, "available_amount": result["available_amount"]})
    complete_request(record, result)
    db.commit()
    return result
