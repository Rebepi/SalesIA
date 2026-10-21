from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.finanzas.application.contracts.pagos_elegibles import StoreCreditApplyRequest
from salesia.modules.finanzas.application.libro_credito_cliente import consume_credit
from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.finanzas.infrastructure_models import PaymentAllocationModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainForbiddenException
from salesia.shared.infrastructure.models import CustomerModel, PaymentModel, SaleModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def apply_store_credit(
    sale_id: UUID, payload: StoreCreditApplyRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: str
):
    record, cached = claim_request(
        db,
        current_user.company_id,
        "sales.apply_store_credit",
        idempotency_key,
        {"sale_id": str(sale_id), **payload.model_dump(mode="json")},
    )

    if cached is not None:
        return cached

    from salesia.modules.organizacion.application.periodos import business_date, require_open_period
    require_open_period(db, current_user.company_id, business_date(db, current_user.company_id))
    sale = db.scalar(
        select(SaleModel)
        .where(SaleModel.id == sale_id, SaleModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if not sale:
        other = db.scalar(select(SaleModel.id).where(SaleModel.id == sale_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Venta no encontrada.")

    if sale.status != "confirmed":
        raise HTTPException(409, "La venta ya está pagada o no admite abonos de saldo.")

    unpaid = sale.total_amount - sale.paid_amount

    if payload.amount <= 0 or payload.amount > unpaid:
        raise HTTPException(409, "El importe a aplicar excede el saldo pendiente de la venta.")

    payment = PaymentModel(id=uuid4(), company_id=current_user.company_id, sale_id=sale.id, payment_method="STORE_CREDIT", amount=payload.amount, currency=sale.currency, reference_code=f"STORE-CREDIT-{sale.id.hex[:8]}", status="confirmed")
    db.add(payment)
    db.flush()
    movement = consume_credit(db, current_user.company_id, sale.customer_id, sale.currency, payload.amount, sale.id, payment.id, f"Aplicación a venta {sale.series}-{sale.number}", payload.source_ids, payload.reservation_id)
    new_credit = movement.resulting_balance
    allocation = PaymentAllocationModel(company_id=current_user.company_id, payment_id=payment.id, sale_id=sale.id, allocated_amount=payload.amount)
    db.add(allocation)

    sale.paid_amount += payload.amount
    sale.version += 1
    if sale.is_credit:
        customer = db.scalar(select(CustomerModel).where(CustomerModel.company_id == current_user.company_id, CustomerModel.id == sale.customer_id).with_for_update())
        if customer:
            customer.current_balance = max(Decimal("0"), customer.current_balance - payload.amount)
    from salesia.modules.finanzas.application.cuotas_cobranza import assign_installments
    assign_installments(db, current_user, sale, allocation)

    if sale.paid_amount >= sale.total_amount:
        sale.status = "paid"

    from salesia.modules.finanzas.application.acuerdos_cobranza import synchronize_company_agreements
    synchronize_company_agreements(db, current_user)

    result = {
        "sale_id": str(sale.id),
        "applied_amount": str(payload.amount),
        "sale_paid_amount": str(sale.paid_amount),
        "sale_status": sale.status,
        "remaining_customer_credit": str(new_credit),
        "currency": sale.currency,
        "movement_id": str(movement.id),
        "payment_id": str(payment.id),
    }

    record_audit_event(db, company_id=current_user.company_id, actor_id=current_user.user_id, actor_email=current_user.email, action="APPLY_CUSTOMER_CREDIT", entity_type="Sale", entity_id=sale.id, diff=result)
    complete_request(record, result)

    db.commit()

    return result
