import json
from datetime import datetime, timezone
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.finanzas.infrastructure_models import (
    CreditNoteLineModel,
    CreditNoteModel,
    CustomerCreditMovementModel,
)
from salesia.modules.inventario.application.contracts.comunes import StockLine
from salesia.modules.inventario.application.contracts.devoluciones_operaciones import (
    ExchangeCreateRequest,
    ReturnAcceptRequest,
    ReturnCancelRequest,
    ReturnCreateRequest,
    ReturnRejectRequest,
    ReturnWithoutReceiptRequest,
)
from salesia.modules.inventario.infrastructure_models import InventoryQuarantine, SupplyDocument, SupplyLine
from salesia.modules.inventario.service import (
    create_document,
    document,
    move_stock,
    product,
    record_audit,
    response,
    transition,
    warehouse,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainForbiddenException
from salesia.shared.infrastructure.models import CustomerModel, PaymentModel, SaleLineModel, SaleModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request, next_number


def create_return(payload: ReturnCreateRequest, current_user: AuthenticatedUser, db: Session):
    sale = db.scalar(
        select(SaleModel).where(SaleModel.id == payload.sale_id, SaleModel.company_id == current_user.company_id)
    )

    if not sale:
        other = db.scalar(select(SaleModel.id).where(SaleModel.id == payload.sale_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Venta no encontrada.")

    if sale.status not in ("confirmed", "paid"):
        raise HTTPException(409, "La venta no admite devolución en este estado.")

    if sale.warehouse_id != payload.warehouse_id:
        raise HTTPException(409, "La venta no admite devolución en este almacén.")

    ref_date = sale.confirmed_at or sale.created_at or datetime.now(timezone.utc)

    if ref_date.tzinfo is None:
        ref_date = ref_date.replace(tzinfo=timezone.utc)

    sale_age = datetime.now(timezone.utc) - ref_date

    if sale_age.days > 30 and not payload.authorized_exception:
        raise HTTPException(
            422, "Plazo comercial vencido para devolución (máximo 30 días sin autorización de administración)."
        )

    sold = {line.product_id: line.quantity for line in sale.lines}

    sale_lines_map = {line.product_id: line for line in sale.lines}

    returned = dict(
        db.execute(
            select(SupplyLine.product_id, func.coalesce(func.sum(SupplyLine.quantity), Decimal("0")))
            .join(SupplyDocument, SupplyDocument.id == SupplyLine.document_id)
            .where(
                SupplyDocument.company_id == current_user.company_id,
                SupplyDocument.kind == "RETURN",
                SupplyDocument.sale_id == sale.id,
                SupplyDocument.status.in_(("pending_inspection", "accepted")),
            )
            .group_by(SupplyLine.product_id)
        ).all()
    )

    req_totals = {}

    for item in payload.items:
        if item.product_id not in sold:
            raise HTTPException(409, "El producto no forma parte de la venta original.")

        req_totals[item.product_id] = req_totals.get(item.product_id, Decimal("0")) + item.quantity

        if returned.get(item.product_id, Decimal("0")) + req_totals[item.product_id] > sold[item.product_id]:
            raise HTTPException(409, "La devolución supera la cantidad vendida.")

    lines = []

    for item in payload.items:
        sl = sale_lines_map[item.product_id]

        lines.append(StockLine(product_id=item.product_id, quantity=item.quantity, unit_cost=sl.unit_cost_snapshot))

    dispositions_map = {str(item.product_id): item.disposition for item in payload.items}

    details = {
        "reason": payload.reason,
        "reason_code": payload.reason_code or "CUSTOMER_RETURN",
        "dispositions": dispositions_map,
        "authorized_exception": payload.authorized_exception,
        "exception_reason": payload.exception_reason,
        "evidence_urls": payload.evidence_urls,
        "requested_by": str(current_user.user_id),
        "requested_at": datetime.now(timezone.utc).isoformat(),
    }

    row = create_document(
        db,
        current_user,
        "RETURN",
        "pending_inspection",
        payload.warehouse_id,
        lines,
        sale_id=sale.id,
        details_json=json.dumps(details),
    )

    record_audit(db, current_user, row.id, "CREATE_RETURN_REQUEST", details)

    db.commit()

    return response(row)


def accept_return(
    return_id: UUID,
    payload: Optional[ReturnAcceptRequest],
    current_user: AuthenticatedUser,
    db: Session,
    idempotency_key: str,
):
    body_dump = payload.model_dump(mode="json") if payload else {}

    body_dump["return_id"] = str(return_id)

    record, cached = claim_request(db, current_user.company_id, "return.accept", idempotency_key, body_dump)

    if cached is not None:
        return cached

    row = document(db, current_user, "RETURN", return_id)

    if row.status == "accepted":
        raise HTTPException(409, "El retorno ya fue aceptado previamente.")

    if row.status != "pending_inspection":
        raise HTTPException(409, f"El retorno no está pendiente de inspección (estado actual: {row.status}).")

    if not transition(db, row, {"pending_inspection"}, "accepted"):
        raise HTTPException(409, "Transición de estado inválida para el retorno.")

    existing_details = json.loads(row.details_json or "{}")

    dispositions = dict(existing_details.get("dispositions", {}))

    if payload and payload.inspections:
        for insp in payload.inspections:
            dispositions[str(insp.product_id)] = insp.disposition

    for line in row.lines:
        disp = dispositions.get(str(line.product_id), "QUARANTINE")

        if disp == "RESTOCK":
            move_stock(
                db,
                row.company_id,
                row.warehouse_id,
                line.product_id,
                line.quantity,
                line.unit_cost,
                row.id,
                "DEVOLUCION_APTA",
            )

        elif disp in ("QUARANTINE", "SCRAP", "DISCARD"):
            db.add(
                InventoryQuarantine(
                    id=uuid4(),
                    company_id=row.company_id,
                    warehouse_id=row.warehouse_id,
                    product_id=line.product_id,
                    quantity=line.quantity,
                    reason="CUSTOMER_RETURN",
                    status="IN_QUARANTINE",
                    reference_doc_type="RETURN",
                    reference_doc_id=row.id,
                )
            )

            if disp in ("SCRAP", "DISCARD"):
                line.damaged_quantity = line.quantity

        line.processed_quantity = line.quantity

    credit_note_info = None

    store_credit_accrued = Decimal("0.000000")

    if row.sale_id:
        sale = db.scalar(
            select(SaleModel)
            .where(SaleModel.id == row.sale_id, SaleModel.company_id == row.company_id)
            .with_for_update()
        )

        if sale:
            sale_lines_by_prod = {sl.product_id: sl for sl in sale.lines}

            cn_lines = []

            cn_subtotal = Decimal("0.000000")

            cn_tax = Decimal("0.000000")

            cn_total = Decimal("0.000000")

            line_idx = 1

            for line in row.lines:
                sl = sale_lines_by_prod.get(line.product_id)

                if sl and sl.quantity > 0:
                    unit_ratio = line.quantity / sl.quantity

                    l_subtotal = (sl.subtotal_amount * unit_ratio).quantize(
                        Decimal("0.000001"), rounding=ROUND_HALF_EVEN
                    )

                    l_tax = (sl.tax_amount * unit_ratio).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

                    l_total = (sl.total_amount * unit_ratio).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

                    u_price = sl.unit_price_snapshot

                    u_disc = (sl.discount_amount * unit_ratio).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

                    t_rate = sl.tax_rate_snapshot

                else:
                    l_subtotal = (line.quantity * line.unit_cost).quantize(
                        Decimal("0.000001"), rounding=ROUND_HALF_EVEN
                    )

                    l_tax = (l_subtotal * Decimal("0.1800")).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

                    l_total = l_subtotal + l_tax

                    u_price = line.unit_cost

                    u_disc = Decimal("0.000000")

                    t_rate = Decimal("0.1800")

                cn_subtotal += l_subtotal

                cn_tax += l_tax

                cn_total += l_total

                cn_lines.append(
                    CreditNoteLineModel(
                        id=uuid4(),
                        product_id=line.product_id,
                        sale_line_id=sl.id if sl else None,
                        line_number=line_idx,
                        quantity=line.quantity,
                        unit_price=u_price,
                        discount_amount=u_disc,
                        tax_rate=t_rate,
                        subtotal_amount=l_subtotal,
                        tax_amount=l_tax,
                        total_amount=l_total,
                    )
                )

                line_idx += 1

            cn_number = next_number(db, row.company_id, "NC01") or 1

            credit_note = CreditNoteModel(
                id=uuid4(),
                company_id=row.company_id,
                branch_id=sale.branch_id,
                customer_id=sale.customer_id,
                sale_id=sale.id,
                return_id=row.id,
                series="NC01",
                number=cn_number,
                currency=sale.currency,
                subtotal_amount=cn_subtotal,
                tax_amount=cn_tax,
                total_amount=cn_total,
                reason_code=payload.reason_code if payload and payload.reason_code else "02_DEVOLUCION",
                reason_description=existing_details.get("reason", "Devolución de mercadería"),
                status="issued",
                issued_by=current_user.user_id,
                lines=cn_lines,
            )

            db.add(credit_note)

            credit_action = payload.credit_action if payload else "CREDIT_NOTE"

            if credit_action == "STORE_CREDIT":
                prev_balance = db.scalar(
                    select(
                        func.coalesce(func.sum(CustomerCreditMovementModel.amount_delta), Decimal("0.000000"))
                    ).where(
                        CustomerCreditMovementModel.company_id == row.company_id,
                        CustomerCreditMovementModel.customer_id == sale.customer_id,
                        CustomerCreditMovementModel.currency == sale.currency,
                    )
                ) or Decimal("0.000000")

                new_bal = prev_balance + cn_total

                store_credit_accrued = cn_total

                db.add(
                    CustomerCreditMovementModel(
                        id=uuid4(),
                        company_id=row.company_id,
                        customer_id=sale.customer_id,
                        currency=sale.currency,
                        movement_type="ACCRUAL",
                        amount_delta=cn_total,
                        resulting_balance=new_bal,
                        reference_type="CREDIT_NOTE",
                        reference_id=credit_note.id,
                        notes=f"Saldo a favor por devolución {row.id}",
                    )
                )

            credit_note_info = {
                "id": str(credit_note.id),
                "series": credit_note.series,
                "number": credit_note.number,
                "total_amount": str(credit_note.total_amount),
                "subtotal_amount": str(credit_note.subtotal_amount),
                "tax_amount": str(credit_note.tax_amount),
                "status": credit_note.status,
            }

    existing_details["approved_by"] = str(current_user.user_id)

    existing_details["approved_at"] = datetime.now(timezone.utc).isoformat()

    existing_details["dispositions"] = dispositions

    row.details_json = json.dumps(existing_details)

    record_audit(
        db,
        current_user,
        row.id,
        "ACCEPT_RETURN",
        {
            "return_id": str(row.id),
            "dispositions": dispositions,
            "credit_note": credit_note_info,
            "store_credit_accrued": str(store_credit_accrued),
        },
    )

    db.flush()

    result = response(row)

    if credit_note_info:
        result["credit_note"] = credit_note_info

        result["store_credit_accrued"] = str(store_credit_accrued)

    complete_request(record, result)

    db.commit()

    return result


def reject_return(return_id: UUID, payload: ReturnRejectRequest, current_user: AuthenticatedUser, db: Session):
    row = document(db, current_user, "RETURN", return_id)

    if row.status != "pending_inspection":
        raise HTTPException(
            409, f"Solo se pueden rechazar retornos pendientes de inspección (estado actual: {row.status})."
        )

    row.status = "rejected"

    details = json.loads(row.details_json or "{}")

    details["rejected_by"] = str(current_user.user_id)

    details["rejected_at"] = datetime.now(timezone.utc).isoformat()

    details["rejection_reason"] = payload.reason

    details["rejection_criterion"] = payload.criterion or "POLICY_VIOLATION"

    row.details_json = json.dumps(details)

    record_audit(db, current_user, row.id, "REJECT_RETURN", details)

    db.commit()

    res = response(row)

    res["details"] = details

    return res


def cancel_return(return_id: UUID, payload: ReturnCancelRequest, current_user: AuthenticatedUser, db: Session):
    row = document(db, current_user, "RETURN", return_id)

    if row.status == "accepted":
        raise HTTPException(
            409,
            "No se puede anular un retorno ya aceptado con efectos físicos o financieros ejecutados. Requiere proceso compensatorio.",
        )

    if row.status == "cancelled":
        raise HTTPException(409, "El retorno ya se encuentra anulado.")

    row.status = "cancelled"

    details = json.loads(row.details_json or "{}")

    details["cancelled_by"] = str(current_user.user_id)

    details["cancelled_at"] = datetime.now(timezone.utc).isoformat()

    details["cancellation_reason"] = payload.reason

    row.details_json = json.dumps(details)

    record_audit(db, current_user, row.id, "CANCEL_RETURN", details)

    db.commit()

    res = response(row)

    res["details"] = details

    return res


def exchange_return(
    return_id: UUID, payload: ExchangeCreateRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: str
):
    record, cached = claim_request(
        db,
        current_user.company_id,
        "return.exchange",
        idempotency_key,
        {"return_id": str(return_id), "items": [item.model_dump(mode="json") for item in payload.replacement_items]},
    )

    if cached is not None:
        return cached

    row = document(db, current_user, "RETURN", return_id)

    if row.status != "accepted":
        raise HTTPException(409, "El cambio de producto requiere que la devolución esté aceptada previamente.")

    orig_sale = db.scalar(
        select(SaleModel).where(SaleModel.id == row.sale_id, SaleModel.company_id == current_user.company_id)
    )

    if not orig_sale:
        raise HTTPException(404, "Venta original no encontrada.")

    cn = db.scalar(
        select(CreditNoteModel).where(
            CreditNoteModel.return_id == row.id, CreditNoteModel.company_id == current_user.company_id
        )
    )

    return_credit = cn.total_amount if cn else Decimal("0.000000")

    branch_id = payload.branch_id or orig_sale.branch_id

    warehouse_id = payload.warehouse_id or orig_sale.warehouse_id

    warehouse(db, current_user.company_id, warehouse_id)

    new_sale_id = uuid4()

    sale_series = "BV01"

    sale_number = next_number(db, current_user.company_id, sale_series) or 1

    new_lines = []

    subtotal = Decimal("0.000000")

    tax = Decimal("0.000000")

    total = Decimal("0.000000")

    line_nr = 1

    for item in payload.replacement_items:
        prod = product(db, current_user.company_id, item.product_id)

        u_price = prod.unit_price

        u_cost = prod.unit_cost

        t_rate = prod.tax_rate

        l_sub = (item.quantity * u_price).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

        l_tax = (l_sub * t_rate).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

        l_tot = l_sub + l_tax

        subtotal += l_sub

        tax += l_tax

        total += l_tot

        new_lines.append(
            SaleLineModel(
                id=uuid4(),
                company_id=current_user.company_id,
                sale_id=new_sale_id,
                product_id=prod.id,
                line_number=line_nr,
                sku_snapshot=prod.sku,
                name_snapshot=prod.name,
                unit_of_measure_snapshot="NIU",
                quantity=item.quantity,
                unit_price_snapshot=u_price,
                unit_cost_snapshot=u_cost,
                discount_amount=Decimal("0.000000"),
                tax_rate_snapshot=t_rate,
                subtotal_amount=l_sub,
                tax_amount=l_tax,
                total_amount=l_tot,
            )
        )

        line_nr += 1

    paid_from_credit = min(total, return_credit)

    is_fully_covered = paid_from_credit >= total

    new_sale = SaleModel(
        id=new_sale_id,
        company_id=current_user.company_id,
        branch_id=branch_id,
        customer_id=orig_sale.customer_id,
        sales_rep_id=orig_sale.sales_rep_id,
        warehouse_id=warehouse_id,
        version=1,
        is_credit=False,
        series=sale_series,
        number=sale_number,
        status="paid" if is_fully_covered else "confirmed",
        currency=orig_sale.currency,
        subtotal_amount=subtotal,
        tax_amount=tax,
        total_amount=total,
        paid_amount=paid_from_credit,
        confirmed_at=datetime.now(timezone.utc),
        lines=new_lines,
    )

    db.add(new_sale)

    if paid_from_credit > 0:
        db.add(
            PaymentModel(
                id=uuid4(),
                company_id=current_user.company_id,
                sale_id=new_sale.id,
                payment_method="RETURN_CREDIT",
                amount=paid_from_credit,
                currency=orig_sale.currency,
                reference_code=f"EXCHANGE-RET-{row.id.hex[:8]}",
                status="confirmed",
            )
        )

    diff = total - return_credit

    if diff < 0:
        favorable_balance = abs(diff)

        prev_balance = db.scalar(
            select(func.coalesce(func.sum(CustomerCreditMovementModel.amount_delta), Decimal("0.000000"))).where(
                CustomerCreditMovementModel.company_id == current_user.company_id,
                CustomerCreditMovementModel.customer_id == orig_sale.customer_id,
                CustomerCreditMovementModel.currency == orig_sale.currency,
            )
        ) or Decimal("0.000000")

        db.add(
            CustomerCreditMovementModel(
                id=uuid4(),
                company_id=current_user.company_id,
                customer_id=orig_sale.customer_id,
                currency=orig_sale.currency,
                movement_type="ACCRUAL",
                amount_delta=favorable_balance,
                resulting_balance=prev_balance + favorable_balance,
                reference_type="EXCHANGE_DIFF",
                reference_id=new_sale.id,
                notes=f"Saldo remanente por cambio de producto con retorno {row.id}",
            )
        )

    for line in new_lines:
        move_stock(
            db,
            current_user.company_id,
            warehouse_id,
            line.product_id,
            -line.quantity,
            line.unit_cost_snapshot,
            new_sale.id,
            "VENTA_CAMBIO",
        )

    exchange_details = {
        "return_id": str(row.id),
        "original_sale_id": str(orig_sale.id),
        "exchange_sale_id": str(new_sale.id),
        "return_credit": str(return_credit),
        "exchange_total": str(total),
        "difference": str(diff),
        "status": "completed",
    }

    record_audit(db, current_user, new_sale.id, "PRODUCT_EXCHANGE", exchange_details)

    db.commit()

    result = {
        "return_id": str(row.id),
        "original_sale_id": str(orig_sale.id),
        "exchange_sale_id": str(new_sale.id),
        "exchange_series": new_sale.series,
        "exchange_number": new_sale.number,
        "exchange_total": str(total),
        "return_credit_applied": str(paid_from_credit),
        "difference": str(diff),
        "exchange_sale_status": new_sale.status,
    }

    complete_request(record, result)

    db.commit()

    return result


def create_return_without_receipt(
    payload: ReturnWithoutReceiptRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: str
):
    record, cached = claim_request(
        db, current_user.company_id, "return.without_receipt", idempotency_key, payload.model_dump(mode="json")
    )

    if cached is not None:
        return cached

    warehouse(db, current_user.company_id, payload.warehouse_id)

    cust = db.scalar(
        select(CustomerModel).where(
            CustomerModel.id == payload.customer_id, CustomerModel.company_id == current_user.company_id
        )
    )

    if not cust:
        raise HTTPException(404, "Cliente no encontrado.")

    if payload.manual_valuation_total > Decimal("200.00") and current_user.role not in ("company_admin", "manager"):
        if not payload.manager_approval_code:
            raise HTTPException(
                403, "Devolución sin comprobante que supera el límite de 200 USD requiere aprobación gerencial."
            )

    lines = []

    for item in payload.items:
        prod = product(db, current_user.company_id, item.product_id)

        lines.append(StockLine(product_id=prod.id, quantity=item.quantity, unit_cost=prod.unit_cost))

    details = {
        "reason": payload.reason,
        "is_without_receipt": True,
        "manual_valuation_total": str(payload.manual_valuation_total),
        "manager_approval_code": payload.manager_approval_code,
        "dispositions": {str(item.product_id): item.disposition for item in payload.items},
        "requested_by": str(current_user.user_id),
    }

    row = create_document(
        db,
        current_user,
        "RETURN",
        "pending_inspection",
        payload.warehouse_id,
        lines,
        sale_id=None,
        details_json=json.dumps(details),
    )

    record_audit(db, current_user, row.id, "RETURN_WITHOUT_RECEIPT", details)

    result = response(row)

    complete_request(record, result)

    db.commit()

    return result
