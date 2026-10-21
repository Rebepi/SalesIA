import json
from datetime import datetime, timezone
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.finanzas.application.saldos_pago import payment_balances
from salesia.modules.finanzas.application.auxiliares.ensure_default_methods import ensure_default_methods
from salesia.modules.finanzas.application.contracts.pagos import (
    PaymentAllocationRequest,
    PaymentCreateRequest,
    PaymentDisputeRequest,
    PaymentReversalRequest,
    ProofOfTransferRequest,
    ProofOfTransferVerifyRequest,
)
from salesia.modules.finanzas.infrastructure_models import (
    PaymentAllocationModel,
    PaymentDisputeModel,
    PaymentIntentModel,
    PaymentMethodConfigModel,
    PaymentReversalModel,
    TransferProofModel,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainForbiddenException
from salesia.shared.infrastructure.models import (
    CashSessionModel,
    CustomerModel,
    OutboxEventModel,
    PaymentModel,
    SaleModel,
)
from salesia.shared.infrastructure.transactions import RefundModel, claim_request, complete_request


def create_payment(payload: PaymentCreateRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: str):
    record, cached = claim_request(
        db, current_user.company_id, "payments.create", idempotency_key, payload.model_dump(mode="json")
    )

    if cached is not None:
        return cached

    if payload.is_advance and (payload.installment_targets or payload.schedule_version is not None):
        raise HTTPException(422, "Un anticipo sin aplicar no cancela cuotas. Distribúyelo al aplicar el saldo a una deuda.")
    from salesia.modules.organizacion.application.periodos import business_date, require_open_period
    require_open_period(db, current_user.company_id, business_date(db, current_user.company_id))
    ensure_default_methods(db, current_user.company_id)

    method_code = payload.payment_method.upper()
    if method_code == "CASH":
        from salesia.modules.organizacion.application.perfil_operativo import require_area
        require_area(db, current_user.company_id, "cash")
        require_open_period(db, current_user.company_id, business_date(db, current_user.company_id), ["treasury"])

    cfg = db.scalar(
        select(PaymentMethodConfigModel).where(
            PaymentMethodConfigModel.company_id == current_user.company_id, PaymentMethodConfigModel.code == method_code
        )
    )

    if cfg and not cfg.is_active:
        raise HTTPException(422, "El método de pago está desactivado.")

    if method_code in ("RETURN_CREDIT", "EXCHANGE_CREDIT", "STORE_CREDIT"):
        raise HTTPException(422, "Los ajustes de devolución se generan únicamente al liquidar su expediente.")

    if method_code == "CREDIT":
        raise HTTPException(422, "El crédito comercial se registra al confirmar la venta y no es un medio de cobro.")

    sale = db.scalar(
        select(SaleModel)
        .where(SaleModel.company_id == current_user.company_id, SaleModel.id == payload.sale_id)
        .with_for_update()
    )

    if not sale:
        other = db.scalar(select(SaleModel.id).where(SaleModel.id == payload.sale_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Venta no encontrada.")

    if sale.status != "confirmed":
        raise HTTPException(409, "Solo se pueden cobrar ventas confirmadas con saldo pendiente.")

    pending_recon = db.scalar(
        select(PaymentIntentModel.id).where(
            PaymentIntentModel.company_id == current_user.company_id,
            PaymentIntentModel.sale_id == sale.id,
            PaymentIntentModel.status == "pending_reconciliation",
        )
    )

    if pending_recon:
        raise HTTPException(409, "Existe una transacción pendiente de conciliación; consulte al proveedor.")

    amount = payload.amount.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    if amount <= 0 or amount != payload.amount:
        raise HTTPException(422, "Importe inválido o precisión superior a seis decimales.")

    effective_amount = amount

    if payload.currency.upper() != sale.currency:
        if payload.exchange_rate is None or payload.exchange_rate <= 0:
            raise HTTPException(422, "La moneda del pago debe coincidir con la venta o incluir tipo de cambio.")

        effective_amount = (amount * payload.exchange_rate).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    if cfg and cfg.requires_reference and not payload.reference_code:
        raise HTTPException(422, "Este método requiere referencia obligatoria.")

    if method_code in ("TRANSFER", "BANK_TRANSFER") and not payload.reference_code:
        raise HTTPException(422, "La transferencia requiere referencia bancaria.")

    change = Decimal("0.000000")

    if method_code == "CASH" and payload.cash_tendered is not None:
        tendered = payload.cash_tendered.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

        if tendered < amount:
            raise HTTPException(422, "El efectivo recibido no cubre el importe.")

        change = (tendered - amount).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    cash_session_id = payload.cash_session_id

    if method_code == "CASH" and cash_session_id is None and payload.require_cash_session:
        cash_session_id = db.scalar(
            select(CashSessionModel.id)
            .where(
                CashSessionModel.company_id == current_user.company_id,
                CashSessionModel.branch_id == sale.branch_id,
                CashSessionModel.user_id == current_user.user_id,
                CashSessionModel.currency == payload.currency.upper(),
                CashSessionModel.status == "open",
            )
            .order_by(CashSessionModel.opened_at.desc())
        )

        if cash_session_id is None:
            raise HTTPException(
                409,
                "No existe un turno de caja abierto para este usuario y sucursal. Abra un turno antes de recibir efectivo.",
            )

    if cash_session_id is not None and method_code != "CASH":
        raise HTTPException(422, "Un medio de cobro distinto de efectivo no debe incrementar el efectivo de una caja.")
    if cash_session_id is not None:
        cs = db.scalar(
            select(CashSessionModel)
            .where(
                CashSessionModel.company_id == current_user.company_id,
                CashSessionModel.id == cash_session_id,
                CashSessionModel.branch_id == sale.branch_id,
            )
            .with_for_update()
        )

        if not cs:
            raise HTTPException(404, "Sesión de caja no encontrada.")

        if cs.status != "open":
            raise HTTPException(409, "La sesión de caja está cerrada.")

        if cs.currency != payload.currency.upper():
            raise HTTPException(422, "La moneda del efectivo debe coincidir con la moneda de la sesión de caja.")
        if cs.user_id != current_user.user_id and not ({"organization:manage", "approvals:manage"} & set(current_user.permissions)):
            raise HTTPException(403, "El cobro debe registrarlo el responsable de caja o un supervisor autorizado.")
        cs.expected_cash = (cs.expected_cash + amount).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

        movs = json.loads(cs.movements_json)

        movs.append(
            {
                "movement_id": str(uuid4()),
                "movement_type": "DEPOSIT",
                "amount": str(amount),
                "currency": cs.currency,
                "sale_currency": sale.currency,
                "sale_amount": str(effective_amount),
                "reason": f"Cobro venta {sale.id}",
                "balance_after": str(cs.expected_cash),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "actor_id": str(current_user.user_id),
            }
        )

        cs.movements_json = json.dumps(movs)

    if not payload.is_advance:
        if sale.paid_amount + effective_amount > sale.total_amount:
            raise HTTPException(409, "El pago supera el saldo pendiente o la venta cambió.")

        if sale.is_credit:
            cust = db.scalar(
                select(CustomerModel)
                .where(CustomerModel.id == sale.customer_id, CustomerModel.company_id == current_user.company_id)
                .with_for_update()
            )

            if cust:
                cust.current_balance = max(Decimal("0.000000"), cust.current_balance - effective_amount).quantize(
                    Decimal("0.000001"), rounding=ROUND_HALF_EVEN
                )

        changed = db.execute(
            update(SaleModel)
            .where(
                SaleModel.id == sale.id,
                SaleModel.status == "confirmed",
                SaleModel.paid_amount + effective_amount <= SaleModel.total_amount,
            )
            .values(paid_amount=SaleModel.paid_amount + effective_amount, version=SaleModel.version + 1)
        )

        if changed.rowcount != 1:
            raise HTTPException(409, "El pago supera el saldo pendiente o la venta cambió.")

        db.refresh(sale)

        if sale.paid_amount == sale.total_amount:
            sale.status = "paid"

    status_str = "confirmed"

    payment = PaymentModel(
        id=uuid4(),
        company_id=current_user.company_id,
        sale_id=sale.id,
        payment_method=method_code,
        amount=effective_amount,
        currency=sale.currency,
        reference_code=payload.reference_code,
        status=status_str,
    )

    db.add(payment)

    db.flush()

    if not payload.is_advance:
        alloc = PaymentAllocationModel(
            id=uuid4(),
            company_id=current_user.company_id,
            payment_id=payment.id,
            sale_id=sale.id,
            allocated_amount=effective_amount,
        )

        db.add(alloc)
        from salesia.modules.finanzas.application.cuotas_cobranza import assign_installments
        assign_installments(db, current_user, sale, alloc, payload.installment_targets, payload.schedule_version)

    db.add(
        OutboxEventModel(
            id=uuid4(),
            company_id=current_user.company_id,
            event_type="PAYMENT_RECEIVED",
            aggregate_type="Payment",
            aggregate_id=payment.id,
            payload_json=json.dumps(
                {"payment_id": str(payment.id), "sale_id": str(sale.id), "amount": str(effective_amount)}
            ),
            status="PENDING",
        )
    )

    db.flush()

    response = {
        "id": str(payment.id),
        "sale_id": str(sale.id),
        "payment_method": method_code,
        "amount": str(effective_amount),
        "currency": sale.currency,
        "reference_code": payload.reference_code,
        "change": str(change),
        "remaining_due": str(
            (sale.total_amount - sale.paid_amount).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
        ),
        "sale_status": sale.status,
        "status": payment.status,
        "created_at": payment.created_at.isoformat(),
    }

    record_audit_event(
        db,
        company_id=current_user.company_id,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        action="PAYMENT_RECEIVED",
        entity_type="Payment",
        entity_id=payment.id,
        diff={
            "sale_id": str(sale.id),
            "amount": str(effective_amount),
            "payment_method": method_code,
            "reference_code": payload.reference_code,
        },
        reason="Cobro registrado para venta",
        category="FINANCIAL",
        fail_critical=True,
    )

    complete_request(record, response)

    from salesia.modules.finanzas.application.acuerdos_cobranza import synchronize_company_agreements
    synchronize_company_agreements(db, current_user)
    db.commit()

    return response


def list_payments(
    search: Optional[str], refundable: bool, limit: int, offset: int, current_user: AuthenticatedUser, db: Session
):
    filters = [PaymentModel.company_id == current_user.company_id]

    if refundable:
        refunded = (
            select(func.coalesce(func.sum(RefundModel.amount), 0))
            .where(RefundModel.company_id == current_user.company_id, RefundModel.payment_id == PaymentModel.id)
            .correlate(PaymentModel)
            .scalar_subquery()
        )

        reversed_amount = (
            select(func.coalesce(func.sum(PaymentReversalModel.amount), 0))
            .where(PaymentReversalModel.company_id == current_user.company_id, PaymentReversalModel.payment_id == PaymentModel.id)
            .correlate(PaymentModel)
            .scalar_subquery()
        )
        filters.extend(
            [
                PaymentModel.status.in_(["confirmed", "partially_refunded"]),
                PaymentModel.amount > refunded + reversed_amount,
                PaymentModel.payment_method.notin_(("RETURN_CREDIT", "EXCHANGE_CREDIT", "STORE_CREDIT")),
                SaleModel.status.in_(["confirmed", "paid"]),
            ]
        )

    if search:
        term = f"%{search.strip()}%"

        filters.append(
            PaymentModel.reference_code.ilike(term)
            | SaleModel.series.ilike(term)
            | CustomerModel.legal_name.ilike(term)
            | CustomerModel.doc_number.ilike(term)
        )

    base = (
        select(PaymentModel, SaleModel, CustomerModel)
        .join(SaleModel, (SaleModel.id == PaymentModel.sale_id) & (SaleModel.company_id == PaymentModel.company_id))
        .join(
            CustomerModel,
            (CustomerModel.id == SaleModel.customer_id) & (CustomerModel.company_id == SaleModel.company_id),
        )
        .where(*filters)
    )

    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0

    rows = db.execute(base.order_by(PaymentModel.created_at.desc()).offset(offset).limit(limit)).all()

    return {
        "items": [
            {
                "id": str(payment.id),
                "sale_id": str(payment.sale_id),
                "sale_number": f"{sale.series}-{sale.number:08d}",
                "customer_name": customer.legal_name,
                "customer_document": customer.doc_number,
                "payment_method": payment.payment_method,
                "amount": str(payment.amount),
                "currency": payment.currency,
                "reference_code": payment.reference_code,
                "status": payment.status,
                "created_at": payment.created_at.isoformat(),
            }
            for payment, sale, customer in rows
        ],
        "total_count": total,
        "limit": limit,
        "offset": offset,
    }


def get_payment(payment_id: UUID, current_user: AuthenticatedUser, db: Session):
    payment = db.scalar(
        select(PaymentModel).where(PaymentModel.company_id == current_user.company_id, PaymentModel.id == payment_id)
    )

    if not payment:
        other = db.scalar(select(PaymentModel.id).where(PaymentModel.id == payment_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"type": "NOT_FOUND", "title": "Pago no encontrado"}
        )

    allocations = db.scalars(
        select(PaymentAllocationModel).where(
            PaymentAllocationModel.payment_id == payment.id,
            PaymentAllocationModel.company_id == current_user.company_id,
        )
    ).all()

    refunds = db.scalars(
        select(RefundModel).where(
            RefundModel.payment_id == payment.id, RefundModel.company_id == current_user.company_id
        )
    ).all()

    reversals = db.scalars(
        select(PaymentReversalModel).where(
            PaymentReversalModel.payment_id == payment.id, PaymentReversalModel.company_id == current_user.company_id
        )
    ).all()

    return {
        "id": str(payment.id),
        "sale_id": str(payment.sale_id),
        "payment_method": payment.payment_method,
        "amount": str(payment.amount),
        "currency": payment.currency,
        "reference_code": payment.reference_code,
        "status": payment.status,
        "allocations": [
            {"allocation_id": str(a.id), "sale_id": str(a.sale_id), "amount": str(a.allocated_amount)}
            for a in allocations
        ],
        "refunded_amount": str(sum((row.amount for row in refunds), Decimal("0"))),
        "refundable_amount": str(max(Decimal("0"), payment.amount - sum((row.amount for row in refunds), Decimal("0")) - sum((row.amount for row in reversals), Decimal("0"))))
        if payment.status in ("confirmed", "partially_refunded") and payment.payment_method not in ("RETURN_CREDIT", "EXCHANGE_CREDIT", "STORE_CREDIT")
        else "0",
        "refunds": [
            {
                "refund_id": str(r.id),
                "amount": str(r.amount),
                "reason": r.reason,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
            }
            for r in refunds
        ],
        "reversals": [{"reversal_id": str(rv.id), "amount": str(rv.amount), "reason": rv.reason} for rv in reversals],
        "created_at": payment.created_at.isoformat(),
    }


def allocate_payment(payment_id: UUID, payload: PaymentAllocationRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: str):
    record, cached = claim_request(db, current_user.company_id, f"payment.allocate:{payment_id}", idempotency_key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    from salesia.modules.organizacion.application.periodos import business_date, require_open_period
    require_open_period(db, current_user.company_id, business_date(db, current_user.company_id))
    payment = db.scalar(
        select(PaymentModel)
        .where(PaymentModel.id == payment_id, PaymentModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if not payment:
        other = db.scalar(select(PaymentModel.id).where(PaymentModel.id == payment_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Pago no encontrado.")

    if payment.payment_method in ("RETURN_CREDIT", "EXCHANGE_CREDIT", "STORE_CREDIT"):
        raise HTTPException(409, "Los ajustes no monetarios solo se aplican desde su expediente de origen.")

    if payment.status != "confirmed":
        raise HTTPException(409, "El pago debe estar confirmado para aplicarse.")

    target_sale = db.scalar(
        select(SaleModel)
        .where(SaleModel.id == payload.sale_id, SaleModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if not target_sale:
        other_s = db.scalar(select(SaleModel.id).where(SaleModel.id == payload.sale_id))

        if other_s:
            raise DomainForbiddenException("Venta de otra empresa no permitida.")

        raise HTTPException(404, "Venta destino no encontrada.")

    source_sale = db.scalar(select(SaleModel).where(SaleModel.company_id == current_user.company_id, SaleModel.id == payment.sale_id))
    if source_sale is None or source_sale.customer_id != target_sale.customer_id:
        raise HTTPException(409, "El pago y la venta destino deben pertenecer al mismo cliente.")
    if target_sale.status != "confirmed" or target_sale.currency != payment.currency:
        raise HTTPException(409, "La venta destino debe estar confirmada y usar la moneda del pago.")

    alloc_amount = payload.allocated_amount.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    if alloc_amount <= 0:
        raise HTTPException(422, "El importe a aplicar debe ser positivo.")

    reservation = None
    if payload.reservation_id:
        from salesia.modules.finanzas.infrastructure.models.devoluciones_credito import CustomerCreditReservationModel
        from salesia.modules.finanzas.application.libro_credito_cliente import instant
        reservation = db.scalar(select(CustomerCreditReservationModel).where(CustomerCreditReservationModel.company_id == current_user.company_id, CustomerCreditReservationModel.id == payload.reservation_id, CustomerCreditReservationModel.payment_id == payment.id, CustomerCreditReservationModel.sale_id == target_sale.id).with_for_update())
        if reservation is None or reservation.status != "active" or instant(reservation.expires_at) <= datetime.now(timezone.utc) or alloc_amount > reservation.amount:
            raise HTTPException(409, "La reserva del anticipo no está disponible para esta venta e importe.")
    usable_balance = payment_balances(db, current_user.company_id, payment, payload.reservation_id)["unapplied"]

    if alloc_amount > usable_balance:
        raise HTTPException(409, "El importe a aplicar supera el saldo utilizable del pago.")

    sale_pending = target_sale.total_amount - target_sale.paid_amount

    if alloc_amount > sale_pending:
        raise HTTPException(409, "El importe a aplicar supera el saldo pendiente de la venta.")

    alloc = PaymentAllocationModel(
        id=uuid4(),
        company_id=current_user.company_id,
        payment_id=payment.id,
        sale_id=target_sale.id,
        allocated_amount=alloc_amount,
    )

    db.add(alloc)

    if reservation:
        reservation.amount -= alloc_amount
        reservation.status = "applied" if reservation.amount == 0 else "active"
        reservation.version += 1

    target_sale.paid_amount = (target_sale.paid_amount + alloc_amount).quantize(
        Decimal("0.000001"), rounding=ROUND_HALF_EVEN
    )

    if target_sale.paid_amount == target_sale.total_amount:
        target_sale.status = "paid"
    target_sale.version += 1
    if target_sale.is_credit:
        customer = db.scalar(select(CustomerModel).where(CustomerModel.company_id == current_user.company_id, CustomerModel.id == target_sale.customer_id).with_for_update())
        if customer:
            customer.current_balance = max(Decimal("0"), customer.current_balance - alloc_amount)
    from salesia.modules.finanzas.application.cuotas_cobranza import assign_installments
    assign_installments(db, current_user, target_sale, alloc, payload.installment_targets, payload.schedule_version)

    from salesia.modules.finanzas.application.acuerdos_cobranza import synchronize_company_agreements
    synchronize_company_agreements(db, current_user)
    result = {
        "allocation_id": str(alloc.id),
        "payment_id": str(payment.id),
        "sale_id": str(target_sale.id),
        "allocated_amount": str(alloc_amount),
        "remaining_unallocated": str(usable_balance - alloc_amount),
        "status": "allocated",
    }
    record_audit_event(db, company_id=current_user.company_id, actor_id=current_user.user_id, actor_email=current_user.email, action="ALLOCATE_UNAPPLIED_PAYMENT", entity_type="Payment", entity_id=payment.id, diff={"reservation_id": str(payload.reservation_id) if payload.reservation_id else None, **result, "currency": payment.currency, "customer_id": str(target_sale.customer_id)})
    complete_request(record, result)
    db.commit()
    return result


def submit_proof_of_transfer(payload: ProofOfTransferRequest, current_user: AuthenticatedUser, db: Session):
    sale = db.scalar(
        select(SaleModel).where(SaleModel.id == payload.sale_id, SaleModel.company_id == current_user.company_id)
    )

    if not sale:
        raise HTTPException(404, "Venta no encontrada.")

    amount = payload.amount.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    payment = PaymentModel(
        id=uuid4(),
        company_id=current_user.company_id,
        sale_id=sale.id,
        payment_method="TRANSFER",
        amount=amount,
        currency=payload.currency,
        reference_code=payload.reference_code,
        status="pending",
    )

    db.add(payment)

    db.flush()

    proof = TransferProofModel(
        id=uuid4(),
        company_id=current_user.company_id,
        payment_id=payment.id,
        document_url=payload.document_url,
        reference_code=payload.reference_code,
        verified=False,
    )

    db.add(proof)

    from salesia.modules.finanzas.application.acuerdos_cobranza import synchronize_company_agreements
    synchronize_company_agreements(db, current_user)
    db.commit()

    return {
        "proof_id": str(proof.id),
        "payment_id": str(payment.id),
        "sale_id": str(sale.id),
        "status": payment.status,
        "verified": proof.verified,
    }


def verify_proof_of_transfer(
    payment_id: UUID, payload: ProofOfTransferVerifyRequest, current_user: AuthenticatedUser, db: Session
):
    payment = db.scalar(
        select(PaymentModel)
        .where(PaymentModel.id == payment_id, PaymentModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if not payment:
        raise HTTPException(404, "Pago no encontrado.")

    proof = db.scalar(
        select(TransferProofModel)
        .where(TransferProofModel.payment_id == payment.id, TransferProofModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if not proof:
        raise HTTPException(404, "Comprobante no encontrado.")

    sale = db.scalar(
        select(SaleModel)
        .where(SaleModel.id == payment.sale_id, SaleModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if proof.verified and payload.approved:
        return {"payment_id": str(payment.id), "status": payment.status, "verified": proof.verified}
    if payment.status != "pending":
        raise HTTPException(409, "El comprobante ya fue resuelto; no se puede volver a modificar el saldo.")
    if payload.approved:
        if sale.status not in ("confirmed", "paid") or payment.amount > sale.total_amount - sale.paid_amount:
            raise HTTPException(409, "El comprobante supera el saldo pendiente actual de la venta.")
        proof.verified = True

        proof.verified_by = current_user.user_id

        proof.verified_at = datetime.now(timezone.utc)

        payment.status = "confirmed"

        sale.paid_amount = (sale.paid_amount + payment.amount).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

        if sale.paid_amount >= sale.total_amount:
            sale.status = "paid"
        sale.version += 1
        alloc = PaymentAllocationModel(id=uuid4(), company_id=current_user.company_id, payment_id=payment.id, sale_id=sale.id, allocated_amount=payment.amount)
        db.add(alloc)
        from salesia.modules.finanzas.application.cuotas_cobranza import assign_installments
        assign_installments(db, current_user, sale, alloc)

    else:
        payment.status = "failed"

    from salesia.modules.finanzas.application.acuerdos_cobranza import synchronize_company_agreements
    synchronize_company_agreements(db, current_user)
    db.commit()

    return {"payment_id": str(payment.id), "status": payment.status, "verified": proof.verified}


def reverse_payment(payment_id: UUID, payload: PaymentReversalRequest, current_user: AuthenticatedUser, db: Session):
    payment = db.scalar(
        select(PaymentModel)
        .where(PaymentModel.id == payment_id, PaymentModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if not payment:
        other = db.scalar(select(PaymentModel.id).where(PaymentModel.id == payment_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Pago no encontrado.")

    if payment.payment_method in ("RETURN_CREDIT", "EXCHANGE_CREDIT", "STORE_CREDIT"):
        raise HTTPException(409, "El ajuste pertenece a una liquidación de devolución y no admite reversión como cobro monetario.")
    prior_refund = db.scalar(select(RefundModel.id).where(RefundModel.company_id == current_user.company_id, RefundModel.payment_id == payment.id).limit(1))
    prior_reversal = db.scalar(select(PaymentReversalModel.id).where(PaymentReversalModel.company_id == current_user.company_id, PaymentReversalModel.payment_id == payment.id).limit(1))
    if prior_refund or prior_reversal:
        raise HTTPException(409, "El pago tiene reembolsos o una reversión previa. Concilie esos movimientos antes de otra corrección.")

    balances = payment_balances(db, current_user.company_id, payment)
    if balances["reserved"] > 0:
        raise HTTPException(409, "Libere las reservas del anticipo antes de corregir su pago.")
    outside = db.scalar(select(PaymentAllocationModel.id).where(PaymentAllocationModel.company_id == current_user.company_id, PaymentAllocationModel.payment_id == payment.id, PaymentAllocationModel.sale_id != payment.sale_id).limit(1))
    if outside or balances["allocated"] != payment.amount:
        raise HTTPException(409, "El pago tiene anticipos o asignaciones a otras ventas. Devuelva su dinero libre desde el libro del cliente o concilie las asignaciones antes de revertirlo.")
    if payment.payment_method == "CASH":
        raise HTTPException(409, "Corrija el efectivo mediante un reembolso con caja y referencia de entrega, para registrar su salida física.")

    sale = db.scalar(
        select(SaleModel)
        .where(SaleModel.id == payment.sale_id, SaleModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if sale is None or sale.paid_amount < payment.amount:
        raise HTTPException(409, "El pago no coincide con el importe aplicado a su venta original.")

    rev = PaymentReversalModel(
        id=uuid4(),
        company_id=current_user.company_id,
        payment_id=payment.id,
        sale_id=sale.id,
        amount=payment.amount,
        reason=payload.reason,
        reference_code=payload.reference_code,
        reversed_by=current_user.user_id,
    )

    db.add(rev)

    sale.paid_amount = (sale.paid_amount - payment.amount).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
    sale.version += 1
    if sale.is_credit:
        customer = db.scalar(select(CustomerModel).where(CustomerModel.company_id == current_user.company_id, CustomerModel.id == sale.customer_id).with_for_update())
        if customer:
            customer.current_balance += payment.amount

    if sale.paid_amount < sale.total_amount:
        sale.status = "confirmed"

    db.flush()
    record_audit_event(db, company_id=current_user.company_id, actor_id=current_user.user_id, actor_email=current_user.email, action="REVERSE_APPLIED_PAYMENT", entity_type="Payment", entity_id=payment.id, diff={"reversal_id": str(rev.id), "sale_id": str(sale.id), "amount": str(payment.amount), "currency": payment.currency, "reason": payload.reason})

    from salesia.modules.finanzas.application.acuerdos_cobranza import synchronize_company_agreements
    synchronize_company_agreements(db, current_user)
    db.commit()

    return {
        "reversal_id": str(rev.id),
        "payment_id": str(payment.id),
        "amount": str(rev.amount),
        "sale_paid_amount": str(sale.paid_amount),
        "sale_status": sale.status,
    }


def create_payment_dispute(
    payment_id: UUID, payload: PaymentDisputeRequest, current_user: AuthenticatedUser, db: Session
):
    payment = db.scalar(
        select(PaymentModel).where(PaymentModel.id == payment_id, PaymentModel.company_id == current_user.company_id)
    )

    if not payment:
        raise HTTPException(404, "Pago no encontrado.")

    disp = PaymentDisputeModel(
        id=uuid4(),
        company_id=current_user.company_id,
        payment_id=payment.id,
        sale_id=payment.sale_id,
        amount=payload.amount,
        reason=payload.reason,
        evidence_url=payload.evidence_url,
        deadline_at=payload.deadline_at,
        status="under_review",
    )

    db.add(disp)

    from salesia.modules.finanzas.application.acuerdos_cobranza import synchronize_company_agreements
    synchronize_company_agreements(db, current_user)
    db.commit()

    return {
        "dispute_id": str(disp.id),
        "payment_id": str(payment.id),
        "amount": str(disp.amount),
        "status": disp.status,
    }
