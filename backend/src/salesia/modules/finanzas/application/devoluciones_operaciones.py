import json
from datetime import datetime, timezone
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.finanzas.application.auxiliares.get_sale_eligible_lines import _get_sale_eligible_lines
from salesia.modules.finanzas.application.auxiliares.serialize_return import _serialize_return
from salesia.modules.finanzas.application.politicas_devolucion import assess, require_policy, return_valuation
from salesia.modules.organizacion.application.periodos import business_date, require_open_period
from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.finanzas.application.contracts.devoluciones_operaciones import (
    ReturnAcceptRequest,
    ReturnCancelRequest,
    ReturnCreateRequest,
    ReturnExchangeRequest,
    ReturnRejectRequest,
)
from salesia.modules.finanzas.infrastructure_models import (
    CreditNoteLineModel,
    CreditNoteModel,
    ReturnLineModel,
    ReturnModel,
)
from salesia.modules.inventario.infrastructure_models import InventoryQuarantine, InventorySerial
from salesia.modules.catalogo.infrastructure_models import ProductProfileModel
from salesia.modules.inventario.service import move_stock
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainForbiddenException
from salesia.shared.infrastructure.models import CompanyModel, SaleModel, WarehouseModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request, next_number


def get_credit_note(credit_note_id: UUID, current_user: AuthenticatedUser, db: Session):
    cn = db.scalar(
        select(CreditNoteModel).where(
            CreditNoteModel.id == credit_note_id, CreditNoteModel.company_id == current_user.company_id
        )
    )

    if not cn:
        other = db.scalar(select(CreditNoteModel.id).where(CreditNoteModel.id == credit_note_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Nota de crédito no encontrada.")

    return {
        "id": str(cn.id),
        "company_id": str(cn.company_id),
        "branch_id": str(cn.branch_id) if cn.branch_id else None,
        "customer_id": str(cn.customer_id),
        "sale_id": str(cn.sale_id),
        "return_id": str(cn.return_id) if cn.return_id else None,
        "series": cn.series,
        "number": cn.number,
        "currency": cn.currency,
        "subtotal_amount": str(cn.subtotal_amount),
        "tax_amount": str(cn.tax_amount),
        "total_amount": str(cn.total_amount),
        "reason_code": cn.reason_code,
        "reason_description": cn.reason_description,
        "status": cn.status,
        "created_at": cn.created_at.isoformat(),
        "lines": [
            {
                "id": str(credit_line.id),
                "product_id": str(credit_line.product_id),
                "line_number": credit_line.line_number,
                "quantity": str(credit_line.quantity),
                "unit_price": str(credit_line.unit_price),
                "discount_amount": str(credit_line.discount_amount),
                "tax_rate": str(credit_line.tax_rate),
                "subtotal_amount": str(credit_line.subtotal_amount),
                "tax_amount": str(credit_line.tax_amount),
                "total_amount": str(credit_line.total_amount),
            }
            for credit_line in cn.lines
        ],
    }


def list_credit_notes(
    sale_id: Optional[UUID], customer_id: Optional[UUID], current_user: AuthenticatedUser, db: Session
):
    query = select(CreditNoteModel).where(CreditNoteModel.company_id == current_user.company_id)

    if sale_id:
        query = query.where(CreditNoteModel.sale_id == sale_id)

    if customer_id:
        query = query.where(CreditNoteModel.customer_id == customer_id)

    query = query.order_by(CreditNoteModel.created_at.desc())

    cns = db.scalars(query).all()

    return [
        {
            "id": str(cn.id),
            "series": cn.series,
            "number": cn.number,
            "sale_id": str(cn.sale_id),
            "customer_id": str(cn.customer_id),
            "return_id": str(cn.return_id) if cn.return_id else None,
            "total_amount": str(cn.total_amount),
            "status": cn.status,
            "created_at": cn.created_at.isoformat(),
        }
        for cn in cns
    ]


def get_eligible_return_lines(sale_id: UUID, current_user: AuthenticatedUser, db: Session):
    sale, lines = _get_sale_eligible_lines(db, sale_id, current_user.company_id)

    from salesia.modules.seguridad.application.separacion_funciones import current
    separation = current(db, current_user.company_id)
    return {
        "independent_review_required": separation["enabled"]["return_acceptance"],
        "sale_id": str(sale_id),
        "sale_status": sale.status,
        "currency": sale.currency,
        "business_date": business_date(db, current_user.company_id).isoformat(),
        "can_authorize_exception": "approvals:manage" in current_user.permissions,
        "can_grant_store_credit": True,
        "lines": [
            {
                "unit_of_measure": ln["unit_of_measure"],
                "allow_fractions": ln["allow_fractions"],
                "return_policy": ln["return_policy"],
                "policy_evaluation": ln["policy_evaluation"],
                "product_id": str(ln["product_id"]),
                "sale_line_id": str(ln["sale_line_id"]),
                "sku": ln["sku"],
                "product_name": ln["product_name"],
                "unit_price": str(ln["net_unit_price"]),
                "tax_rate_snapshot": str(ln["tax_rate_snapshot"]),
                "original_quantity": str(ln["sold_quantity"]),
                "serial_numbers": ln["serial_numbers"],
                "sold_quantity": str(ln["sold_quantity"]),
                "returned_quantity": str(ln["returned_quantity"]),
                "eligible_quantity": str(ln["eligible_quantity"]),
                "unit_price_snapshot": str(ln["unit_price_snapshot"]),
                "prorated_discount_per_unit": str(ln["prorated_discount_per_unit"]),
                "net_unit_price": str(ln["net_unit_price"]),
            }
            for ln in lines
        ],
    }


def create_return(payload: ReturnCreateRequest, current_user: AuthenticatedUser, db: Session, idempotency_key=None):
    record, cached = claim_request(db, current_user.company_id, "returns.create", idempotency_key, payload.model_dump(mode="json"))
    if cached is not None:
        return cached
    require_open_period(db, current_user.company_id, business_date(db, current_user.company_id))
    sale, eligible_lines = _get_sale_eligible_lines(db, payload.sale_id, current_user.company_id)

    eligible_by_id = {line["sale_line_id"]: line for line in eligible_lines}
    selected = {}
    assessments = {}
    for item in payload.items:
        if item.sale_line_id is None:
            matches = [line for line in eligible_lines if line["product_id"] == item.product_id]
            if len(matches) != 1:
                raise HTTPException(422, "Selecciona la línea exacta de la venta para devolver este producto.")
            item.sale_line_id = matches[0]["sale_line_id"]
        eligible = eligible_by_id.get(item.sale_line_id)
        if not eligible or eligible["product_id"] != item.product_id:
            raise HTTPException(422, "La línea no pertenece al producto de la venta.")
        if item.sale_line_id in selected:
            raise HTTPException(422, "Agrupa la devolución de una misma línea en un solo registro.")
        if item.quantity > eligible["eligible_quantity"]:
            raise HTTPException(409, "La devolución supera las unidades entregadas que siguen siendo elegibles.")
        if not eligible.get("allow_fractions", True) and item.quantity != item.quantity.to_integral_value():
            raise HTTPException(422, "La unidad del producto no admite fracciones. Ingresa una cantidad entera para devolver.")
        serials = item.serial_numbers
        if eligible["serial_numbers"]:
            if item.quantity != item.quantity.to_integral_value() or len(serials) != int(item.quantity) or len(set(serials)) != len(serials) or not set(serials) <= set(eligible["serial_numbers"]):
                raise HTTPException(422, "Selecciona una serie elegible y distinta por cada unidad devuelta.")
        elif serials:
            raise HTTPException(422, "La línea no tiene esas series disponibles para devolución.")
        assessment = assess(eligible["return_policy"], business_date(db, current_user.company_id), item.condition, item.packaging, item.evidence_note, payload.evidence_urls)
        require_policy(assessment, payload, current_user)
        assessments[str(item.sale_line_id)] = assessment
        selected[item.sale_line_id] = eligible

    wh = db.scalar(
        select(WarehouseModel).where(
            WarehouseModel.id == payload.warehouse_id,
            WarehouseModel.company_id == current_user.company_id,
            WarehouseModel.is_active.is_(True),
        )
    )

    if not wh:
        raise HTTPException(422, "Almacen no encontrado o de otra empresa.")

    ret = ReturnModel(
        id=uuid4(),
        company_id=current_user.company_id,
        sale_id=payload.sale_id,
        customer_id=sale.customer_id,
        warehouse_id=payload.warehouse_id,
        status="requested",
        reason=payload.reason,
        is_without_receipt=False,
        authorized_exception=payload.authorized_exception,
        exception_reason=payload.exception_reason,
        requested_by=current_user.user_id,
        evidence_urls_json=json.dumps(payload.evidence_urls or []),
        details_json=json.dumps({"policy_assessments": assessments, "waive_retention": payload.waive_retention, "exception_actor_id": str(current_user.user_id) if payload.authorized_exception or payload.waive_retention else None}),
    )

    db.add(ret)

    db.flush()

    for item in payload.items:
        el = selected[item.sale_line_id]

        db.add(
            ReturnLineModel(
                id=uuid4(),
                return_id=ret.id,
                sale_line_id=item.sale_line_id,
                serial_numbers_json=json.dumps(item.serial_numbers),
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price_snapshot=el["unit_price_snapshot"],
                unit_cost_snapshot=el["unit_cost_snapshot"],
                discount_per_unit=el["prorated_discount_per_unit"],
                tax_rate_snapshot=el["tax_rate_snapshot"],
                disposition=item.disposition,
            )
        )

    db.flush()
    response = _serialize_return(ret)
    record_audit_event(db, company_id=current_user.company_id, actor_id=current_user.user_id, actor_email=current_user.email, action="REQUEST_SALES_RETURN", entity_type="Return", entity_id=ret.id, diff={"sale_id": str(sale.id), "policy_assessments": assessments, "exception_reason": payload.exception_reason})
    complete_request(record, response)
    db.commit()
    return response


def list_returns(
    sale_id: Optional[UUID],
    customer_id: Optional[UUID],
    status_filter: Optional[str],
    current_user: AuthenticatedUser,
    db: Session,
):
    q = select(ReturnModel).where(ReturnModel.company_id == current_user.company_id)

    if sale_id:
        q = q.where(ReturnModel.sale_id == sale_id)

    if customer_id:
        q = q.where(ReturnModel.customer_id == customer_id)

    if status_filter:
        q = q.where(ReturnModel.status == status_filter)

    q = q.order_by(ReturnModel.created_at.desc())

    rets = db.scalars(q).all()

    return [_serialize_return(r) for r in rets]


def get_return(return_id: UUID, current_user: AuthenticatedUser, db: Session):
    ret = db.scalar(
        select(ReturnModel).where(ReturnModel.id == return_id, ReturnModel.company_id == current_user.company_id)
    )

    if not ret:
        other = db.scalar(select(ReturnModel.id).where(ReturnModel.id == return_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Devolucion no encontrada.")

    return _serialize_return(ret)


def reject_return(return_id: UUID, payload: ReturnRejectRequest, current_user: AuthenticatedUser, db: Session):
    ret = db.scalar(
        select(ReturnModel)
        .where(ReturnModel.id == return_id, ReturnModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if not ret:
        other = db.scalar(select(ReturnModel.id).where(ReturnModel.id == return_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Devolucion no encontrada.")

    if ret.status != "requested":
        raise HTTPException(
            409, f"Solo se puede rechazar una devolucion en estado requested. Estado actual: {ret.status}."
        )

    ret.status = "rejected"

    ret.rejection_reason = payload.reason

    ret.rejection_criterion = payload.criterion

    db.commit()

    return _serialize_return(ret)


def cancel_return(return_id: UUID, payload: ReturnCancelRequest, current_user: AuthenticatedUser, db: Session):
    ret = db.scalar(
        select(ReturnModel)
        .where(ReturnModel.id == return_id, ReturnModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if not ret:
        other = db.scalar(select(ReturnModel.id).where(ReturnModel.id == return_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Devolucion no encontrada.")

    if ret.status != "requested":
        raise HTTPException(
            409, f"Solo se puede cancelar una devolucion en estado requested. Estado actual: {ret.status}."
        )

    ret.status = "cancelled"

    details = json.loads(ret.details_json) if ret.details_json else {}

    details["cancellation_reason"] = payload.reason

    ret.details_json = json.dumps(details)

    db.commit()

    return _serialize_return(ret)


def accept_return(
    return_id: UUID, payload: ReturnAcceptRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: str
):
    record, cached = claim_request(
        db,
        current_user.company_id,
        "returns.accept",
        idempotency_key,
        {
            "return_id": str(return_id),
            "create_credit_note": payload.create_credit_note,
            "credit_action": payload.credit_action,
            "inspections": [item.model_dump(mode="json") for item in payload.inspections or []],
        },
    )

    if cached is not None:
        return cached

    require_open_period(db, current_user.company_id, business_date(db, current_user.company_id))
    ret = db.scalar(
        select(ReturnModel)
        .where(ReturnModel.id == return_id, ReturnModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if not ret:
        other = db.scalar(select(ReturnModel.id).where(ReturnModel.id == return_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Devolucion no encontrada.")

    if ret.status != "requested":
        raise HTTPException(409, f"La devolucion ya fue procesada (estado: {ret.status}).")

    from salesia.modules.seguridad.application.separacion_funciones import enforce
    enforce(db, current_user, "return_acceptance", [ret.requested_by], "Return", ret.id)
    inspection_map = {}

    if payload.inspections:
        for ins in payload.inspections:
            inspection_map[(ins.product_id, ins.sale_line_id)] = ins.disposition

    for ln in ret.lines:
        final_disposition = inspection_map.get((ln.product_id, ln.sale_line_id), inspection_map.get((ln.product_id, None), ln.disposition))
        if final_disposition not in ("RESTOCK", "QUARANTINE", "DISPOSE"):
            raise HTTPException(422, "El destino de inspección no es válido.")
        ln.disposition = final_disposition
        serial_numbers = json.loads(ln.serial_numbers_json or "[]")
        if serial_numbers:
            serials = db.scalars(select(InventorySerial).where(InventorySerial.company_id == current_user.company_id, InventorySerial.product_id == ln.product_id, InventorySerial.serial_number.in_(serial_numbers), InventorySerial.status == "SOLD").with_for_update()).all()
            if len(serials) != len(serial_numbers):
                raise HTTPException(409, "Una serie ya fue devuelta o cambió de estado.")
            for serial in serials:
                serial.status = "IN_STOCK" if final_disposition == "RESTOCK" else "IN_QUARANTINE" if final_disposition == "QUARANTINE" else "SCRAPPED"
                serial.warehouse_id, serial.location_id, serial.current_doc_type, serial.current_doc_id = ret.warehouse_id, None, "RETURN", ret.id
        profile = db.scalar(select(ProductProfileModel).where(ProductProfileModel.company_id == current_user.company_id, ProductProfileModel.product_id == ln.product_id))
        if profile and (profile.product_type == "service" or not profile.track_inventory):
            continue

        if final_disposition == "RESTOCK":
            move_stock(
                db,
                current_user.company_id,
                ret.warehouse_id,
                ln.product_id,
                ln.quantity,
                ln.unit_cost_snapshot,
                ret.id,
                "DEVOLUCION_RESTOCK",
                allow_negative=True,
            )

        elif final_disposition == "QUARANTINE":
            db.add(
                InventoryQuarantine(
                    id=uuid4(),
                    company_id=current_user.company_id,
                    warehouse_id=ret.warehouse_id,
                    product_id=ln.product_id,
                    quantity=ln.quantity,
                    reason=f"Devolucion {ret.id}: {ret.reason}",
                    status="IN_QUARANTINE",
                    reference_doc_type="RETURN",
                    reference_doc_id=ret.id,
                )
            )

    ret.status = "accepted"

    ret.approved_by = current_user.user_id

    valuation = return_valuation(ret)
    result = {"id": str(ret.id), "status": "accepted", "valuation": valuation}
    details = json.loads(ret.details_json or "{}")
    details["accepted_at"] = datetime.now(timezone.utc).isoformat()
    details["settlement_credit_action"] = payload.credit_action or "CREDIT_NOTE"
    details["valuation"] = valuation
    if ret.sale_id:
        details["settlement_version"] = 1
    ret.details_json = json.dumps(details)

    if payload.create_credit_note or payload.credit_action == "STORE_CREDIT":
        sale = db.scalar(
            select(SaleModel).where(SaleModel.id == ret.sale_id, SaleModel.company_id == current_user.company_id)
        )

        if not sale:
            raise HTTPException(409, "Venta original no encontrada para generar nota de credito.")

        valued_lines = {item["line_id"]: item for item in valuation["lines"]}
        line_items = [
            {
                "product_id": ln.product_id,
                "sale_line_id": ln.sale_line_id,
                "quantity": ln.quantity,
                "unit_price": (Decimal(valued_lines[str(ln.id)]["refundable_net"]) / ln.quantity).quantize(Decimal("0.000001")),
                "subtotal": Decimal(valued_lines[str(ln.id)]["refundable_net"]),
                "tax": Decimal(valued_lines[str(ln.id)]["refundable_tax"]),
                "discount_amount": ln.discount_per_unit * ln.quantity + Decimal(valued_lines[str(ln.id)]["retained_net"]),
                "tax_rate": ln.tax_rate_snapshot,
                "unit_cost": ln.unit_cost_snapshot,
            }
            for ln in ret.lines
        ]

        total_subtotal = sum((item["subtotal"] for item in line_items), Decimal("0"))
        total_tax = sum((item["tax"] for item in line_items), Decimal("0"))

        total_amount = (total_subtotal + total_tax).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

        cn_number = next_number(db, current_user.company_id, "NC01")

        cn = CreditNoteModel(
            id=uuid4(),
            company_id=current_user.company_id,
            branch_id=sale.branch_id,
            customer_id=sale.customer_id,
            sale_id=sale.id,
            return_id=ret.id,
            series="NC01",
            number=cn_number,
            currency=sale.currency,
            subtotal_amount=total_subtotal,
            tax_amount=total_tax,
            total_amount=total_amount,
            reason_code="02_DEVOLUCION",
            reason_description=ret.reason,
            status="issued",
            issued_by=current_user.user_id,
        )

        db.add(cn)

        db.flush()

        for i, it in enumerate(line_items, 1):
            sub = it["subtotal"]

            tax = it["tax"]

            db.add(
                CreditNoteLineModel(
                    id=uuid4(),
                    credit_note_id=cn.id,
                    sale_line_id=it["sale_line_id"],
                    product_id=it["product_id"],
                    line_number=i,
                    quantity=it["quantity"],
                    unit_price=it["unit_price"],
                    discount_amount=it["discount_amount"],
                    tax_rate=it["tax_rate"],
                    subtotal_amount=sub,
                    tax_amount=tax,
                    total_amount=sub + tax,
                )
            )

        ret.credit_note_id = cn.id

        result["credit_note"] = {
            "id": str(cn.id),
            "series": cn.series,
            "number": cn_number,
            "subtotal_amount": str(cn.subtotal_amount),
            "tax_amount": str(cn.tax_amount),
            "total_amount": str(cn.total_amount),
        }

    from salesia.modules.finanzas.application.liquidaciones_devolucion import initial_settlement
    if ret.sale_id:
        result["settlement"] = initial_settlement(db, current_user, ret, payload.credit_action or "CREDIT_NOTE")
    else:
        result["settlement"] = {"requires_original_sale": True, "available_amount": "0", "valuation": valuation}

    complete_request(record, result)

    db.commit()

    return result


def exchange_return(
    return_id: UUID, payload: ReturnExchangeRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: str
):
    record, cached = claim_request(
        db, current_user.company_id, "returns.exchange", idempotency_key, {"return_id": str(return_id), **payload.model_dump(mode="json")}
    )

    if cached is not None:
        return cached

    require_open_period(db, current_user.company_id, business_date(db, current_user.company_id))
    ret = db.scalar(
        select(ReturnModel)
        .where(ReturnModel.id == return_id, ReturnModel.company_id == current_user.company_id)
        .with_for_update()
    )

    if not ret:
        other = db.scalar(select(ReturnModel.id).where(ReturnModel.id == return_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Devolucion no encontrada.")

    if ret.status != "accepted":
        raise HTTPException(409, "La devolucion debe estar aceptada para iniciar un cambio.")

    if ret.exchange_sale_id:
        raise HTTPException(409, "Esta devolucion ya tiene un cambio de producto registrado.")

    from salesia.modules.finanzas.application.liquidaciones_devolucion import adopt_legacy, initial_settlement, settlement_data, use_value
    adopt_legacy(db, current_user, ret)
    initial_settlement(db, current_user, ret, "CREDIT_NOTE")
    available = settlement_data(db, current_user, ret)
    if not available["can_settle"] or Decimal(available["available_amount"]) <= 0:
        raise HTTPException(409, "La devolución no tiene valor disponible para aplicar al cambio.")
    return_credit = Decimal(available["available_amount"])

    wh = db.scalar(
        select(WarehouseModel).where(
            WarehouseModel.id == payload.warehouse_id,
            WarehouseModel.company_id == current_user.company_id,
            WarehouseModel.is_active.is_(True),
        )
    )

    if not wh:
        raise HTTPException(422, "Almacen de destino no encontrado o de otra empresa.")

    sale_orig = db.scalar(select(SaleModel).where(SaleModel.id == ret.sale_id, SaleModel.company_id == current_user.company_id))
    from salesia.modules.catalogo.application.catalogo.unidades import validate_unit_fraction
    company = db.scalar(select(CompanyModel).where(CompanyModel.id == current_user.company_id))
    if sale_orig is None or company.base_currency != sale_orig.currency:
        raise HTTPException(409, "El cambio directo requiere la moneda base. Los cambios con otra moneda deben usar una venta con precio y conversión documentados.")
    if wh.branch_id != sale_orig.branch_id:
        raise HTTPException(422, "El almacén del cambio debe corresponder a la sede de la venta.")

    from salesia.shared.infrastructure.models import ProductModel as PM
    from salesia.shared.infrastructure.models import SaleLineModel as SLM

    new_total = Decimal("0.000000")

    new_lines_data = []

    for item in payload.replacement_items:
        prod = db.scalar(
            select(PM).where(PM.id == item.product_id, PM.company_id == current_user.company_id, PM.is_active.is_(True))
        )

        if not prod:
            raise HTTPException(422, f"Producto de reemplazo {item.product_id} no encontrado.")

        profile = db.scalar(select(ProductProfileModel).where(ProductProfileModel.company_id == current_user.company_id, ProductProfileModel.product_id == prod.id))
        if profile and (profile.status != "active" or profile.is_kit or profile.tracking_mode in ("SERIAL", "LOT")):
            raise HTTPException(409, "Este artículo requiere un cambio mediante el flujo de venta con sus componentes, lotes o series identificados.")
        validate_unit_fraction(db, current_user.company_id, prod.unit_of_measure, item.quantity)
        subtotal = (item.quantity * prod.unit_price).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

        tax = (subtotal * prod.tax_rate).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

        new_lines_data.append({"prod": prod, "profile": profile, "quantity": item.quantity, "subtotal": subtotal, "tax": tax})

        new_total += subtotal + tax

        if profile is None or (profile.product_type != "service" and profile.track_inventory):
            move_stock(
                db,
                current_user.company_id,
                payload.warehouse_id,
                item.product_id,
                -item.quantity,
                prod.unit_cost,
                ret.id,
                "CAMBIO_PRODUCTO",
                allow_negative=False,
            )

    new_sale_id = uuid4()

    currency = sale_orig.currency if sale_orig else "USD"

    branch_id = sale_orig.branch_id if sale_orig else None

    customer_id = ret.customer_id

    new_subtotal = sum(d["subtotal"] for d in new_lines_data)

    new_tax = sum(d["tax"] for d in new_lines_data)

    diff = new_total - return_credit

    new_sale = SaleModel(
        id=new_sale_id,
        company_id=current_user.company_id,
        branch_id=branch_id,
        warehouse_id=payload.warehouse_id,
        customer_id=customer_id,
        version=1,
        is_credit=False,
        series="BV01",
        number=next_number(db, current_user.company_id, "BV01"),
        status="paid" if min(return_credit, new_total) == new_total else "confirmed",
        fulfillment_status="delivered",
        currency=currency,
        subtotal_amount=new_subtotal,
        tax_amount=new_tax,
        total_amount=new_total,
        paid_amount=min(return_credit, new_total),
        confirmed_at=datetime.now(timezone.utc),
    )

    db.add(new_sale)

    db.flush()

    for i, d in enumerate(new_lines_data, 1):
        db.add(
            SLM(
                id=uuid4(),
                company_id=current_user.company_id,
                sale_id=new_sale_id,
                product_id=d["prod"].id,
                line_number=i,
                sku_snapshot=d["prod"].sku,
                name_snapshot=d["prod"].name,
                unit_of_measure_snapshot=d["prod"].unit_of_measure,
                quantity=d["quantity"],
                fulfilled_quantity=d["quantity"],
                delivered_at=new_sale.confirmed_at,
                warranty_months_snapshot=d["profile"].warranty_period_months if d["profile"] else 0,
                warranty_policy_snapshot=d["profile"].warranty_policy if d["profile"] else None,
                unit_price_snapshot=d["prod"].unit_price,
                unit_cost_snapshot=d["prod"].unit_cost,
                discount_amount=Decimal("0.000000"),
                tax_rate_snapshot=d["prod"].tax_rate,
                subtotal_amount=d["subtotal"],
                tax_amount=d["tax"],
                total_amount=d["subtotal"] + d["tax"],
            )
        )

    db.flush()
    from salesia.modules.finanzas.application.politicas_devolucion import freeze_sale_policies
    freeze_sale_policies(db, new_sale)
    from salesia.modules.ventas.application.participacion_comercial import freeze_commission
    freeze_commission(db, new_sale)
    applied_credit = min(return_credit, new_total)
    if applied_credit > 0:
        from salesia.modules.finanzas.infrastructure.models.pagos import PaymentAllocationModel, PaymentModel
        payment = PaymentModel(id=uuid4(), company_id=current_user.company_id, sale_id=new_sale_id, payment_method="EXCHANGE_CREDIT", amount=applied_credit, currency=currency, reference_code=f"RETURN-EXCHANGE-{ret.id}", status="confirmed")
        db.add(payment)
        db.flush()
        db.add(PaymentAllocationModel(company_id=current_user.company_id, payment_id=payment.id, sale_id=new_sale_id, allocated_amount=applied_credit))
        use_value(db, current_user, ret, "exchange", new_sale_id, applied_credit, {"payment_id": str(payment.id)})
    ret.exchange_sale_id = new_sale_id

    result = {
        "return_id": str(ret.id),
        "original_sale_id": str(ret.sale_id),
        "exchange_sale_id": str(new_sale_id),
        "return_credit_applied": str(applied_credit),
        "remaining_return_value": settlement_data(db, current_user, ret)["available_amount"],
        "new_sale_total": str(new_total),
        "difference": str(diff),
    }

    complete_request(record, result)

    db.commit()

    return result
