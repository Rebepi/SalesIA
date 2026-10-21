from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
import json
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.finanzas.application.saldos_pago import payment_balances
from salesia.modules.finanzas.application.contracts.reembolsos import RefundCreateRequest, RefundStatusUpdateRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainForbiddenException
from salesia.shared.infrastructure.models import CashSessionModel, CustomerModel, OutboxEventModel, PaymentModel, SaleModel
from salesia.modules.finanzas.infrastructure.models.devoluciones_credito import ReturnModel
from salesia.modules.finanzas.infrastructure.models.pagos import PaymentAllocationModel, PaymentReversalModel
from salesia.modules.organizacion.application.periodos import business_date, require_open_period
from salesia.modules.finanzas.application.liquidaciones_devolucion import credit_sale, initial_settlement, scoped_return, settlement_data, use_value
from salesia.shared.infrastructure.transactions import RefundModel, claim_request, complete_request


def create_refund(payload: RefundCreateRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: str):
    record, cached = claim_request(
        db, current_user.company_id, "payments.refund", idempotency_key, payload.model_dump(mode="json")
    )

    if cached is not None:
        return cached

    require_open_period(db, current_user.company_id, business_date(db, current_user.company_id))
    payment = db.scalar(select(PaymentModel).where(PaymentModel.company_id == current_user.company_id, PaymentModel.id == payload.payment_id).with_for_update())
    if payment is None:
        raise HTTPException(404, "Pago no encontrado en la empresa activa.")
    sale = db.scalar(select(SaleModel).where(SaleModel.company_id == current_user.company_id, SaleModel.id == payment.sale_id).with_for_update())
    if sale is None or (not payload.unapplied_only and sale.status not in ("confirmed", "paid")):
        raise HTTPException(409, "La venta no admite reembolso en su estado actual.")
    if payment.payment_method in ("RETURN_CREDIT", "EXCHANGE_CREDIT", "STORE_CREDIT"):
        raise HTTPException(409, "Un ajuste de devolución o saldo a favor no es un desembolso monetario reembolsable.")
    if payment.status != "confirmed" or payment.currency != sale.currency:
        raise HTTPException(409, "El pago debe estar confirmado y conciliado en la moneda de la venta antes del reembolso.")
    if not payload.payout_reference.strip():
        raise HTTPException(422, "Registre la referencia del desembolso o acta de devolución del dinero.")
    allocations = db.scalars(select(PaymentAllocationModel).where(PaymentAllocationModel.company_id == current_user.company_id, PaymentAllocationModel.payment_id == payment.id)).all()
    if not payload.unapplied_only and any(item.sale_id != sale.id for item in allocations):
        raise HTTPException(409, "El pago tiene aplicaciones en otras ventas. Resuelva esas aplicaciones antes de reembolsar el origen.")
    refunded, reversed_amount, remaining = payment_availability(db, current_user, payment)
    ret = None
    balances = payment_balances(db, current_user.company_id, payment)
    available = balances["original_applied"]
    if payload.unapplied_only:
        if payload.return_id:
            raise HTTPException(422, "Un anticipo sin aplicar no se liquida como devolución de mercadería.")
        available = balances["unapplied"]
    elif payload.return_id:
        ret = scoped_return(db, current_user, payload.return_id, True)
        if ret.status != "accepted" or ret.sale_id != sale.id or ret.customer_id != sale.customer_id:
            raise HTTPException(409, "La devolución debe estar aceptada y corresponder a la misma venta y cliente del pago.")
        initial_settlement(db, current_user, ret, "CREDIT_NOTE")
        settlement = settlement_data(db, current_user, ret)
        if not settlement["can_settle"]:
            raise HTTPException(409, "Concilie las aplicaciones históricas de esta devolución antes de reembolsarla.")
        available = min(available, Decimal(settlement["available_amount"]))
    elif db.scalar(select(ReturnModel.id).where(ReturnModel.company_id == current_user.company_id, ReturnModel.sale_id == sale.id, ReturnModel.status == "accepted").limit(1)):
        raise HTTPException(409, "La venta tiene devoluciones aceptadas. Vincule el reembolso a su expediente para respetar retenciones, cambios y saldos ya aplicados.")
    amount = payload.amount if payload.amount is not None else available
    if amount <= 0 or amount > available or amount != amount.quantize(Decimal("0.000001")):
        raise HTTPException(409, "El importe supera el saldo del pago o el valor disponible de la devolución.")
    if not payload.unapplied_only and amount > sale.paid_amount:
        raise HTTPException(409, "El reembolso supera el importe aplicado a la venta. Revise los anticipos y aplicaciones antes de continuar.")
    session = None
    if payment.payment_method == "CASH":
        if "cash:register:manage" not in current_user.permissions or not payload.cash_session_id:
            raise HTTPException(422, "Seleccione una caja abierta y autorizada para registrar la salida física del efectivo.")
        session = db.scalar(select(CashSessionModel).where(CashSessionModel.company_id == current_user.company_id, CashSessionModel.id == payload.cash_session_id, CashSessionModel.branch_id == sale.branch_id, CashSessionModel.currency == payment.currency, CashSessionModel.status == "open").with_for_update())
        if session is None or session.expected_cash < amount:
            raise HTTPException(409, "La caja no está disponible en esta sede y moneda o no cubre el reembolso.")
        if session.user_id != current_user.user_id and not ({"approvals:manage", "organization:manage"} & set(current_user.permissions)):
            raise HTTPException(403, "El retiro debe registrarlo el responsable de caja o un supervisor autorizado.")
    elif payload.cash_session_id:
        raise HTTPException(422, "El reembolso de otro medio no debe retirar efectivo de una caja.")
    refund = RefundModel(id=uuid4(), unapplied_only=payload.unapplied_only, company_id=current_user.company_id, payment_id=payment.id, return_id=ret.id if ret else None, cash_session_id=session.id if session else None, amount=amount, reason=payload.reason, currency=payment.currency, provider_reference=payload.payout_reference.strip(), status="confirmed")
    db.add(refund)
    if not payload.unapplied_only:
        sale.paid_amount -= amount
        sale.version += 1
        sale.status = "paid" if sale.paid_amount == sale.total_amount else "confirmed"
        if sale.is_credit:
            customer = db.scalar(select(CustomerModel).where(CustomerModel.company_id == current_user.company_id, CustomerModel.id == sale.customer_id).with_for_update())
            if customer:
                customer.current_balance += amount
    payment.status = "refunded" if refunded + reversed_amount + amount == payment.amount else "confirmed"
    if session:
        session.expected_cash -= amount
        movements = json.loads(session.movements_json or "[]")
        movements.append({"movement_id": str(uuid4()), "movement_type": "WITHDRAWAL", "amount": str(amount), "currency": payment.currency, "category": "REFUND", "refund_id": str(refund.id), "return_id": str(ret.id) if ret else None, "reason": f"Reembolso {refund.id}: {payload.reason}", "balance_after": str(session.expected_cash), "timestamp": business_timestamp(), "actor_id": str(current_user.user_id)})
        session.movements_json = json.dumps(movements)
    db.flush()
    if ret:
        credit = credit_sale(db, current_user, ret, sale, amount, f"RETURN-REFUND-{refund.id}")
        use_value(db, current_user, ret, "refund", refund.id, amount, {"payment_id": str(payment.id), "credit_payment_id": str(credit.id), "payout_reference": payload.payout_reference.strip(), "cash_session_id": str(session.id) if session else None})
    db.add(OutboxEventModel(id=uuid4(), company_id=current_user.company_id, event_type="PAYMENT_REFUNDED", aggregate_type="Payment", aggregate_id=payment.id, payload_json=json.dumps({"refund_id": str(refund.id), "return_id": str(ret.id) if ret else None, "amount": str(amount), "reason": payload.reason}), status="PENDING"))
    response = {"refund_id": str(refund.id), "payment_id": str(payment.id), "return_id": str(ret.id) if ret else None, "amount": str(amount), "currency": payment.currency, "reason": payload.reason, "status": refund.status, "unapplied_only": payload.unapplied_only, "remaining_payment_amount": str(remaining - amount), "settlement": settlement_data(db, current_user, ret) if ret else None}
    record_audit_event(db, company_id=current_user.company_id, actor_id=current_user.user_id, actor_email=current_user.email, action="REFUND_ISSUED", entity_type="Refund", entity_id=refund.id, diff=response, reason=payload.reason, category="FINANCIAL", fail_critical=True)
    complete_request(record, response)
    from salesia.modules.finanzas.application.acuerdos_cobranza import synchronize_company_agreements
    synchronize_company_agreements(db, current_user)
    db.commit()
    return response


def business_timestamp():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def payment_availability(db, user, payment):
    refunded = db.scalar(select(func.coalesce(func.sum(RefundModel.amount), 0)).where(RefundModel.company_id == user.company_id, RefundModel.payment_id == payment.id)) or Decimal("0")
    reversed_amount = db.scalar(select(func.coalesce(func.sum(PaymentReversalModel.amount), 0)).where(PaymentReversalModel.company_id == user.company_id, PaymentReversalModel.payment_id == payment.id)) or Decimal("0")
    return refunded, reversed_amount, max(Decimal("0"), payment.amount - refunded - reversed_amount)


def refund_options(payment_id, user, db):
    payment = db.scalar(select(PaymentModel).where(PaymentModel.company_id == user.company_id, PaymentModel.id == payment_id))
    if payment is None:
        raise HTTPException(404, "Pago no encontrado.")
    sale = db.scalar(select(SaleModel).where(SaleModel.company_id == user.company_id, SaleModel.id == payment.sale_id))
    if sale is None:
        raise HTTPException(409, "La venta original no está disponible.")
    refunded, reversed_amount, available = payment_availability(db, user, payment)
    if payment.payment_method in ("RETURN_CREDIT", "EXCHANGE_CREDIT", "STORE_CREDIT") or payment.status != "confirmed" or payment.currency != sale.currency:
        available = Decimal("0")
    returns = db.scalars(select(ReturnModel).where(ReturnModel.company_id == user.company_id, ReturnModel.sale_id == sale.id, ReturnModel.status == "accepted").order_by(ReturnModel.created_at.desc())).all()
    balances = payment_balances(db, user.company_id, payment)
    applied_available = min(available, balances["original_applied"])
    choices = []
    for ret in returns:
        data = settlement_data(db, user, ret)
        debt = min(Decimal(data["available_amount"]), max(Decimal("0"), sale.total_amount - sale.paid_amount))
        cap = max(Decimal("0"), min(applied_available, Decimal(data["available_amount"]) - debt, sale.paid_amount)) if data["can_settle"] else Decimal("0")
        choices.append({"id": str(ret.id), "created_at": ret.created_at.isoformat(), "currency": data["currency"], "available_amount": str(cap), "retained_total": data["valuation"]["retained_total"], "applied_amount": data["applied_amount"], "warnings": data["warnings"], "movements": data["movements"]})
    sessions = db.scalars(select(CashSessionModel).where(CashSessionModel.company_id == user.company_id, CashSessionModel.branch_id == sale.branch_id, CashSessionModel.currency == payment.currency, CashSessionModel.status == "open").order_by(CashSessionModel.opened_at.desc())).all() if payment.payment_method == "CASH" and "cash:register:manage" in user.permissions else []
    return {"unapplied_amount": str(min(available, balances["unapplied"])), "payment_id": str(payment.id), "currency": payment.currency, "payment_method": payment.payment_method, "refunded_amount": str(refunded), "reversed_amount": str(reversed_amount), "available_amount": str(min(applied_available, sale.paid_amount)), "requires_return": bool(returns), "returns": choices, "cash_sessions": [{"id": str(row.id), "terminal_code": row.terminal_code, "balance": str(row.expected_cash)} for row in sessions if row.user_id == user.user_id or {"approvals:manage", "organization:manage"} & set(user.permissions)]}


def update_refund_status(
    refund_id: UUID, payload: RefundStatusUpdateRequest, current_user: AuthenticatedUser, db: Session
):
    ref = db.scalar(
        select(RefundModel)
        .where(RefundModel.id == refund_id, RefundModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if not ref:
        raise HTTPException(404, "Reembolso no encontrado.")

    current_st = ref.status or "confirmed"

    new_st = payload.status

    valid_transitions = {
        "requested": {"approved", "failed", "cancelled", "solicitado", "aprobado", "fallido"},
        "approved": {"sent", "failed", "enviado", "fallido"},
        "sent": {
            "pending",
            "confirmed",
            "failed",
            "requires_reconciliation",
            "pendiente",
            "confirmado",
            "fallido",
            "requiere_conciliacion",
        },
        "pending": {"confirmed", "failed", "requires_reconciliation", "confirmado", "fallido", "requiere_conciliacion"},
        "requires_reconciliation": {"confirmed", "failed", "confirmado", "fallido"},
        "solicitado": {"aprobado", "fallido", "approved", "failed"},
        "aprobado": {"enviado", "fallido", "sent", "failed"},
        "enviado": {
            "pendiente",
            "confirmado",
            "fallido",
            "requiere_conciliacion",
            "pending",
            "confirmed",
            "failed",
            "requires_reconciliation",
        },
        "pendiente": {
            "confirmado",
            "fallido",
            "requiere_conciliacion",
            "confirmed",
            "failed",
            "requires_reconciliation",
        },
        "requiere_conciliacion": {"confirmado", "fallido", "confirmed", "failed"},
        "confirmed": set(),
        "confirmado": set(),
        "failed": {"requires_reconciliation", "requiere_conciliacion"},
        "fallido": {"requires_reconciliation", "requiere_conciliacion"},
    }

    if new_st not in valid_transitions.get(current_st, set()) and current_st != new_st:
        raise HTTPException(409, f"Transición de estado de reembolso inválida de '{current_st}' a '{new_st}'.")

    ref.status = new_st

    if payload.failure_reason:
        ref.failure_reason = payload.failure_reason

    if payload.provider_reference:
        ref.provider_reference = payload.provider_reference

    from salesia.modules.finanzas.application.acuerdos_cobranza import synchronize_company_agreements
    synchronize_company_agreements(db, current_user)
    db.commit()

    return {
        "refund_id": str(ref.id),
        "status": ref.status,
        "provider_reference": ref.provider_reference,
        "failure_reason": ref.failure_reason,
    }


def list_refunds(status: Optional[str], payment_id: Optional[UUID], current_user: AuthenticatedUser, db: Session, search: str | None = None, currency: str | None = None, date_from: date | None = None, date_to: date | None = None, linked_return: bool | None = None):
    stmt = select(RefundModel).where(RefundModel.company_id == current_user.company_id)

    if status:
        stmt = stmt.where(RefundModel.status == status)

    if payment_id:
        stmt = stmt.where(RefundModel.payment_id == payment_id)

    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="La fecha inicial no puede ser posterior a la fecha final.")
    if currency:
        stmt = stmt.where(RefundModel.currency == currency)
    if linked_return is not None:
        stmt = stmt.where(RefundModel.return_id.is_not(None) if linked_return else RefundModel.return_id.is_(None))
    if date_from:
        start = datetime.combine(date_from, time.min, ZoneInfo("America/Lima")).astimezone(timezone.utc)
        stmt = stmt.where(RefundModel.created_at >= start)
    if date_to:
        end = datetime.combine(date_to, time.min, ZoneInfo("America/Lima")).astimezone(timezone.utc) + timedelta(days=1)
        stmt = stmt.where(RefundModel.created_at < end)
    if search and search.strip():
        term = search.strip()
        matches = [column.icontains(term, autoescape=True) for column in [cast(RefundModel.id, String), cast(RefundModel.payment_id, String), RefundModel.provider_reference, RefundModel.reason]]
        try:
            identifier = UUID(term)
            matches.extend([RefundModel.id == identifier, RefundModel.payment_id == identifier])
        except ValueError:
            pass
        stmt = stmt.where(or_(*matches))

    stmt = stmt.order_by(RefundModel.created_at.desc())

    rows = db.scalars(stmt).all()

    return [
        {
            "id": str(r.id),
            "payment_id": str(r.payment_id),
            "amount": str(r.amount),
            "currency": r.currency,
            "reason": r.reason,
            "status": r.status,
            "provider_reference": r.provider_reference,
            "failure_reason": r.failure_reason,
            "return_id": str(r.return_id) if r.return_id else None,
            "cash_session_id": str(r.cash_session_id) if r.cash_session_id else None,
            "unapplied_only": r.unapplied_only,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


def get_refund(refund_id: UUID, current_user: AuthenticatedUser, db: Session):
    ref = db.scalar(
        select(RefundModel).where(RefundModel.id == refund_id, RefundModel.company_id == current_user.company_id)
    )

    if not ref:
        other = db.scalar(select(RefundModel.id).where(RefundModel.id == refund_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Reembolso no encontrado.")

    return {
        "id": str(ref.id),
        "payment_id": str(ref.payment_id),
        "amount": str(ref.amount),
        "currency": ref.currency,
        "reason": ref.reason,
        "status": ref.status,
        "provider_reference": ref.provider_reference,
        "failure_reason": ref.failure_reason,
        "return_id": str(ref.return_id) if ref.return_id else None,
        "cash_session_id": str(ref.cash_session_id) if ref.cash_session_id else None,
        "unapplied_only": ref.unapplied_only,
        "created_at": ref.created_at.isoformat(),
    }
