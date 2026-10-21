import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.catalogo.infrastructure_models import (
    CouponModel,
    ProductKitItemModel,
    ProductProfileModel,
    PromotionModel,
)
from salesia.modules.inventario.infrastructure_models import InventorySerial
from salesia.modules.operaciones.infrastructure_models import SalesRepresentative
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.ventas.application.auxiliares.prepare_lines import prepare_lines
from salesia.modules.ventas.application.auxiliares.response_for import response_for
from salesia.modules.ventas.application.auxiliares.scoped_sale import scoped_sale
from salesia.modules.ventas.application.auxiliares.validate_context import validate_context
from salesia.modules.ventas.application.auxiliares.payment_terms import resolve_payment_terms, set_sale_due_date
from salesia.modules.ventas.application.validacion import sale_validation
from salesia.modules.ventas.application.pedidos_facturacion import synchronize_order_fulfillment, validate_sale_source
from salesia.modules.ventas.application.contracts.ventas_operaciones import (
    AnnulSaleRequest,
    ConfirmSaleRequest,
    CorrectSaleRequest,
    CreateSaleDraftRequest,
    LineItemRequest,
    UpdateSaleDraftRequest,
)
from salesia.shared.infrastructure.models import (
    AuditLogModel,
    BranchModel,
    CompanyModel,
    CustomerModel,
    CustomerProfileModel,
    InventoryStockModel,
    KardexMovementModel,
    OutboxEventModel,
    ProductModel,
    SaleModel,
)
from salesia.shared.infrastructure.transactions import CompanySettings, claim_request, complete_request, next_number


def create_draft(payload: CreateSaleDraftRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: str):
    record, cached = claim_request(
        db, current_user.company_id, "sales.create", idempotency_key, payload.model_dump(mode="json")
    )

    if cached is not None:
        return cached

    warehouse = validate_context(db, payload, current_user.company_id)

    representative = db.scalar(
        select(SalesRepresentative).where(
            SalesRepresentative.company_id == current_user.company_id,
            SalesRepresentative.user_id == current_user.user_id,
            SalesRepresentative.is_active.is_(True),
        )
    )

    sale_id = uuid4()

    lines, explanations = prepare_lines(db, payload, current_user.company_id, sale_id)

    series = "F001" if payload.document_type == "INVOICE" else "B001"

    requested_rep = (
        db.scalar(
            select(SalesRepresentative).where(
                SalesRepresentative.id == payload.sales_rep_id,
                SalesRepresentative.company_id == current_user.company_id,
                SalesRepresentative.is_active.is_(True),
            )
        )
        if payload.sales_rep_id
        else representative
    )

    if payload.sales_rep_id and not requested_rep:
        raise HTTPException(422, "El vendedor seleccionado no está activo o no pertenece a la empresa.")

    sale = SaleModel(
        id=sale_id,
        company_id=current_user.company_id,
        branch_id=payload.branch_id,
        customer_id=payload.customer_id,
        warehouse_id=warehouse.id,
        sales_rep_id=requested_rep.id if requested_rep else None,
        version=1,
        is_credit=payload.is_credit,
        payment_terms_days=resolve_payment_terms(db, current_user.company_id, payload.customer_id, payload.payment_terms_days),
        order_id=payload.order_id,
        series=series,
        number=next_number(db, current_user.company_id, series),
        status="draft",
        currency=payload.currency.upper(),
        exchange_rate=payload.exchange_rate,
        coupon_code=payload.coupon_code.strip().upper() if payload.coupon_code else None,
        notes=payload.notes,
        delivery_address=payload.delivery_address,
        internal_observations=payload.internal_observations,
        pricing_explanation_json=json.dumps(explanations),
        subtotal_amount=sum(line.subtotal_amount for line in lines),
        tax_amount=sum(line.tax_amount for line in lines),
        total_amount=sum(line.total_amount for line in lines),
        paid_amount=Decimal("0"),
        lines=lines,
    )

    db.add(sale)

    db.flush()

    response = response_for(sale)

    complete_request(record, response)

    db.commit()

    return response


def update_draft(
    sale_id: UUID, payload: UpdateSaleDraftRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: str
):
    record, cached = claim_request(
        db,
        current_user.company_id,
        "sales.update",
        idempotency_key,
        {"sale_id": str(sale_id), **payload.model_dump(mode="json")},
    )

    if cached is not None:
        return cached

    sale = scoped_sale(db, sale_id, current_user, lock=True)

    if sale.status != "draft" or sale.version != payload.version:
        raise HTTPException(409, "El borrador cambió o ya no es editable.")
    if sale.order_id:
        if payload.order_id and payload.order_id != sale.order_id:
            raise HTTPException(409, "No se puede trasladar la venta a otro pedido.")
        payload.order_id = sale.order_id
        if payload.payment_terms_days is None:
            payload.payment_terms_days = sale.payment_terms_days
        previous_lines = sorted(sale.lines, key=lambda line: line.line_number)
        for index, requested_line in enumerate(payload.lines):
            if requested_line.order_line_number is None and index < len(previous_lines) and requested_line.product_id == previous_lines[index].product_id:
                requested_line.order_line_number = previous_lines[index].order_line_number

    warehouse = validate_context(db, payload, current_user.company_id)

    changed = db.execute(
        update(SaleModel)
        .where(SaleModel.id == sale.id, SaleModel.version == payload.version, SaleModel.status == "draft")
        .values(version=SaleModel.version + 1)
    )

    if changed.rowcount != 1:
        raise HTTPException(409, "Edición concurrente; recargue la venta.")

    sale.lines.clear()

    db.flush()

    sale.lines, explanations = prepare_lines(db, payload, current_user.company_id, sale.id)

    sale.branch_id = payload.branch_id

    sale.customer_id = payload.customer_id

    sale.warehouse_id = warehouse.id

    sale.currency = payload.currency.upper()

    sale.is_credit = payload.is_credit

    sale.payment_terms_days = resolve_payment_terms(db, current_user.company_id, payload.customer_id, payload.payment_terms_days)
    sale.order_id = payload.order_id

    if payload.sales_rep_id:
        requested_rep = db.scalar(
            select(SalesRepresentative).where(
                SalesRepresentative.id == payload.sales_rep_id,
                SalesRepresentative.company_id == current_user.company_id,
                SalesRepresentative.is_active.is_(True),
            )
        )

        if not requested_rep:
            raise HTTPException(422, "El vendedor seleccionado no está activo o no pertenece a la empresa.")

        sale.sales_rep_id = requested_rep.id

    sale.exchange_rate = payload.exchange_rate

    sale.coupon_code = payload.coupon_code.strip().upper() if payload.coupon_code else None

    sale.notes = payload.notes

    sale.delivery_address = payload.delivery_address

    sale.internal_observations = payload.internal_observations

    sale.pricing_explanation_json = json.dumps(explanations)

    sale.subtotal_amount = sum(line.subtotal_amount for line in sale.lines)

    sale.tax_amount = sum(line.tax_amount for line in sale.lines)

    sale.total_amount = sum(line.total_amount for line in sale.lines)

    db.flush()

    response = response_for(sale)

    complete_request(record, response)

    db.commit()

    return response


def confirm_sale(
    sale_id: UUID,
    payload: Optional[ConfirmSaleRequest],
    idempotency_key: str,
    current_user: AuthenticatedUser,
    db: Session,
):
    body = {
        "sale_id": str(sale_id),
        "is_credit_sale": payload.is_credit_sale if payload else None,
        "version": payload.version if payload else None,
    }

    record, cached = claim_request(db, current_user.company_id, "sales.confirm", idempotency_key, body)

    if cached is not None:
        return cached

    sale = scoped_sale(db, sale_id, current_user, lock=True)

    if payload and payload.version and sale.version != payload.version:
        raise HTTPException(409, "Versión de borrador obsoleta; recargue la venta antes de confirmar.")

    if sale.status in ("confirmed", "paid"):
        if payload and payload.is_credit_sale != sale.is_credit:
            raise HTTPException(409, "No se pueden cambiar las condiciones de una venta confirmada.")

        response = response_for(sale)

        complete_request(record, response)

        db.commit()

        return response

    if sale.status != "draft" or not sale.lines or not sale.warehouse_id:
        raise HTTPException(409, "La venta no se puede confirmar; revise estado, líneas y almacén.")

    if payload and payload.allow_blocked_exception and ("approvals:manage" not in current_user.permissions or not payload.exception_reason or len(payload.exception_reason.strip()) < 3):
        raise HTTPException(403, "La excepción de bloqueo requiere un responsable de aprobaciones y un motivo documentado.")

    sale.is_credit = payload.is_credit_sale if payload else sale.is_credit
    from salesia.modules.organizacion.application.perfil_operativo import require_sale_areas
    require_sale_areas(db, sale)

    validate_sale_source(db, sale)

    validation = sale_validation(db, sale, current_user, bool(payload and payload.allow_blocked_exception))

    if not validation["valid"]:
        raise HTTPException(409, "La venta no supera la validación comercial: " + "; ".join(validation["errors"]))

    cust_profile = db.scalar(
        select(CustomerProfileModel).where(
            CustomerProfileModel.company_id == sale.company_id, CustomerProfileModel.customer_id == sale.customer_id
        )
    )

    if cust_profile and cust_profile.status == "blocked" and not (payload and payload.allow_blocked_exception):
        raise HTTPException(
            409, "El cliente se encuentra bloqueado para operaciones comerciales sin excepción registrada."
        )

    changed = db.execute(
        update(SaleModel)
        .where(SaleModel.id == sale.id, SaleModel.status == "draft", SaleModel.version == sale.version)
        .values(status="confirmed", version=SaleModel.version + 1)
    )

    if changed.rowcount != 1:
        raise HTTPException(409, "Confirmación concurrente; reintente la misma solicitud.")

    sale.is_credit = payload.is_credit_sale if payload else sale.is_credit

    if sale.is_credit:
        granted = db.execute(
            update(CustomerModel)
            .where(
                CustomerModel.id == sale.customer_id,
                CustomerModel.company_id == sale.company_id,
                CustomerModel.is_active.is_(True),
                CustomerModel.current_balance + sale.total_amount <= CustomerModel.credit_limit,
            )
            .values(current_balance=CustomerModel.current_balance + sale.total_amount)
        )

        if granted.rowcount != 1:
            raise HTTPException(409, "Límite de crédito insuficiente.")

    for line in sorted(sale.lines, key=lambda row: str(row.product_id)):
        if sale.order_id:
            continue
        prof = db.scalar(
            select(ProductProfileModel).where(
                ProductProfileModel.company_id == sale.company_id, ProductProfileModel.product_id == line.product_id
            )
        )

        if prof and (prof.product_type == "service" or not prof.track_inventory):
            continue

        serials = db.scalars(
            select(InventorySerial)
            .where(
                InventorySerial.company_id == sale.company_id,
                InventorySerial.product_id == line.product_id,
                InventorySerial.warehouse_id == sale.warehouse_id,
                InventorySerial.status == "IN_STOCK",
            )
            .with_for_update()
        ).all()

        selected_serials = json.loads(line.serial_numbers_json or "[]")

        if selected_serials or serials:
            available_by_number = {serial.serial_number: serial for serial in serials}

            if len(selected_serials) != int(line.quantity):
                raise HTTPException(
                    409, f"El producto {line.sku_snapshot} requiere una serie disponible por cada unidad."
                )

            missing = [number for number in selected_serials if number not in available_by_number]

            if missing:
                raise HTTPException(
                    409,
                    f"Las series seleccionadas para {line.sku_snapshot} ya no están disponibles: {', '.join(missing)}.",
                )

            for number in selected_serials:
                serial = available_by_number[number]

                serial.status = "SOLD"

                serial.current_doc_type = "SALE"

                serial.current_doc_id = sale.id

        if prof and prof.is_kit:
            kit_items = db.scalars(
                select(ProductKitItemModel).where(
                    ProductKitItemModel.company_id == sale.company_id,
                    ProductKitItemModel.kit_product_id == line.product_id,
                )
            ).all()

            for kitem in kit_items:
                req_qty = kitem.quantity * line.quantity

                k_stock = db.scalar(
                    select(InventoryStockModel)
                    .where(
                        InventoryStockModel.company_id == sale.company_id,
                        InventoryStockModel.warehouse_id == sale.warehouse_id,
                        InventoryStockModel.product_id == kitem.component_product_id,
                    )
                    .with_for_update()
                )

                if not k_stock or (k_stock.physical_quantity - k_stock.reserved_quantity < req_qty):
                    raise HTTPException(409, "Stock disponible insuficiente para componente del kit.")

                db.execute(
                    update(InventoryStockModel)
                    .where(InventoryStockModel.id == k_stock.id)
                    .values(physical_quantity=InventoryStockModel.physical_quantity - req_qty)
                )

                db.refresh(k_stock)

                db.add(
                    KardexMovementModel(
                        id=uuid4(),
                        company_id=sale.company_id,
                        warehouse_id=sale.warehouse_id,
                        product_id=kitem.component_product_id,
                        movement_type="VENTA",
                        reference_doc_type="SALE",
                        reference_doc_id=sale.id,
                        quantity_delta=-req_qty,
                        resulting_physical_qty=k_stock.physical_quantity,
                        unit_cost=k_stock.average_cost,
                        moving_average_cost=k_stock.average_cost,
                        occurred_at=datetime.now(timezone.utc),
                    )
                )

            continue

        stock_query = (
            select(InventoryStockModel)
            .where(
                InventoryStockModel.company_id == sale.company_id,
                InventoryStockModel.warehouse_id == sale.warehouse_id,
                InventoryStockModel.product_id == line.product_id,
            )
            .with_for_update()
        )

        stock = db.scalar(stock_query)

        if not stock:
            raise HTTPException(409, f"No hay existencias registradas para {line.sku_snapshot}.")

        changed = db.execute(
            update(InventoryStockModel)
            .where(
                InventoryStockModel.id == stock.id,
                InventoryStockModel.physical_quantity - InventoryStockModel.reserved_quantity >= line.quantity,
            )
            .values(physical_quantity=InventoryStockModel.physical_quantity - line.quantity)
        )

        if changed.rowcount != 1:
            raise HTTPException(409, f"Stock disponible insuficiente para {line.sku_snapshot}.")

        db.refresh(stock)

        db.add(
            KardexMovementModel(
                id=uuid4(),
                company_id=sale.company_id,
                warehouse_id=sale.warehouse_id,
                product_id=line.product_id,
                movement_type="VENTA",
                reference_doc_type="SALE",
                reference_doc_id=sale.id,
                quantity_delta=-line.quantity,
                resulting_physical_qty=stock.physical_quantity,
                unit_cost=line.unit_cost_snapshot,
                moving_average_cost=line.unit_cost_snapshot,
                occurred_at=datetime.now(timezone.utc),
            )
        )

    sale.confirmed_at = datetime.now(timezone.utc)
    from salesia.modules.finanzas.application.politicas_devolucion import freeze_sale_policies
    freeze_sale_policies(db, sale)
    from salesia.modules.ventas.application.participacion_comercial import freeze_commission
    freeze_commission(db, sale)

    set_sale_due_date(sale, sale.confirmed_at, db)
    if sale.order_id:
        synchronize_order_fulfillment(db, sale.company_id, sale.order_id)
    else:
        sale.fulfillment_status = "delivered"
        for line in sale.lines:
            line.fulfilled_quantity, line.delivered_at = line.quantity, sale.confirmed_at

    applied_rules = json.loads(sale.pricing_explanation_json or "[]")

    promotion_codes = {
        rule.get("code")
        for line in applied_rules
        for rule in line.get("rules_applied", [])
        if rule.get("rule_type") == "PROMOTION" and rule.get("code")
    }

    for code in promotion_codes:
        db.execute(
            update(PromotionModel)
            .where(
                PromotionModel.company_id == sale.company_id,
                PromotionModel.code == code,
                PromotionModel.current_uses < PromotionModel.max_quota,
            )
            .values(current_uses=PromotionModel.current_uses + 1)
        )

    if sale.coupon_code:
        changed_coupon = db.execute(
            update(CouponModel)
            .where(
                CouponModel.company_id == sale.company_id,
                CouponModel.code == sale.coupon_code,
                CouponModel.is_active.is_(True),
                CouponModel.current_uses < CouponModel.max_uses,
            )
            .values(current_uses=CouponModel.current_uses + 1)
        )

        if changed_coupon.rowcount != 1:
            raise HTTPException(409, "El cupón dejó de estar disponible antes de confirmar la venta.")

    db.add(
        OutboxEventModel(
            id=uuid4(),
            company_id=sale.company_id,
            event_type="SALE_CONFIRMED",
            aggregate_type="Sale",
            aggregate_id=sale.id,
            payload_json=json.dumps({"sale_id": str(sale.id), "total_amount": str(sale.total_amount)}),
            status="PENDING",
        )
    )

    record_audit_event(
        db,
        company_id=sale.company_id,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        action="CONFIRM_SALE",
        entity_type="Sale",
        entity_id=sale.id,
        diff={"status": "confirmed", "total_amount": str(sale.total_amount)},
        reason="Confirmacion de venta comercial",
        category="COMMERCIAL",
        fail_critical=True,
    )

    db.flush()

    response = response_for(sale)

    complete_request(record, response)

    db.commit()

    return response


def annul_sale(
    sale_id: UUID, payload: AnnulSaleRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: str
):
    record, cached = claim_request(
        db,
        current_user.company_id,
        "sales.annul",
        idempotency_key,
        {"sale_id": str(sale_id), "reason": payload.reason, "version": payload.version},
    )

    if cached is not None:
        return cached

    sale = scoped_sale(db, sale_id, current_user, lock=True)

    if payload.version and sale.version != payload.version:
        raise HTTPException(409, "La versión de la venta no coincide.")

    if sale.status == "cancelled":
        response = response_for(sale)

        complete_request(record, response)

        db.commit()

        return response

    if sale.paid_amount > 0 or sale.status not in ("draft", "confirmed"):
        raise HTTPException(409, "Reembolse los cobros y resuelva el estado antes de anular.")

    old_status = sale.status

    changed = db.execute(
        update(SaleModel)
        .where(SaleModel.id == sale.id, SaleModel.version == sale.version, SaleModel.status == old_status)
        .values(status="cancelled", version=SaleModel.version + 1)
    )

    if changed.rowcount != 1:
        raise HTTPException(409, "La venta cambió; recargue.")

    if old_status == "confirmed":
        from salesia.modules.organizacion.application.periodos import business_date, require_open_period
        require_open_period(db, current_user.company_id, business_date(db, current_user.company_id, sale.confirmed_at or sale.created_at))
        require_open_period(db, current_user.company_id, business_date(db, current_user.company_id), ["inventory"])
        if sale.is_credit:
            require_open_period(db, current_user.company_id, business_date(db, current_user.company_id), ["receivables"])

        movements = db.scalars(
            select(KardexMovementModel)
            .where(
                KardexMovementModel.company_id == sale.company_id,
                KardexMovementModel.reference_doc_id == sale.id,
                KardexMovementModel.reference_doc_type == "SALE",
            )
            .order_by(KardexMovementModel.product_id)
        ).all()

        if not movements:
            raise HTTPException(409, "No existe trazabilidad de stock para revertir esta venta.")

        for movement in movements:
            stock = db.scalar(
                select(InventoryStockModel)
                .where(
                    InventoryStockModel.company_id == sale.company_id,
                    InventoryStockModel.warehouse_id == movement.warehouse_id,
                    InventoryStockModel.product_id == movement.product_id,
                )
                .with_for_update()
            )

            if not stock:
                raise HTTPException(409, "Falta el registro de inventario original.")

            db.execute(
                update(InventoryStockModel)
                .where(InventoryStockModel.id == stock.id)
                .values(physical_quantity=InventoryStockModel.physical_quantity - movement.quantity_delta)
            )

            db.refresh(stock)

            db.add(
                KardexMovementModel(
                    company_id=sale.company_id,
                    warehouse_id=movement.warehouse_id,
                    product_id=movement.product_id,
                    movement_type="ANULACION_VENTA",
                    reference_doc_type="SALE_ANNUL",
                    reference_doc_id=sale.id,
                    quantity_delta=-movement.quantity_delta,
                    resulting_physical_qty=stock.physical_quantity,
                    unit_cost=movement.unit_cost,
                    moving_average_cost=movement.moving_average_cost,
                    occurred_at=datetime.now(timezone.utc),
                )
            )

        db.execute(
            update(InventorySerial)
            .where(
                InventorySerial.company_id == sale.company_id,
                InventorySerial.current_doc_type == "SALE",
                InventorySerial.current_doc_id == sale.id,
                InventorySerial.status == "SOLD",
            )
            .values(status="IN_STOCK", current_doc_type=None, current_doc_id=None)
        )

        if sale.is_credit:
            changed = db.execute(
                update(CustomerModel)
                .where(CustomerModel.id == sale.customer_id, CustomerModel.current_balance >= sale.total_amount)
                .values(current_balance=CustomerModel.current_balance - sale.total_amount)
            )

            if changed.rowcount != 1:
                raise HTTPException(409, "Saldo de crédito inconsistente; concilie antes de anular.")

    if sale.order_id:
        synchronize_order_fulfillment(db, sale.company_id, sale.order_id)

    from salesia.modules.finanzas.application.reservas_credito_cliente import reconcile_sale_reservations
    reconcile_sale_reservations(db, current_user, sale, cancelled=True)

    record_audit_event(
        db,
        company_id=sale.company_id,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        action="ANNUL_SALE",
        entity_type="Sale",
        entity_id=sale.id,
        diff={"reason": payload.reason, "approved_by": payload.approved_by},
        reason=payload.reason,
        category="COMMERCIAL",
        fail_critical=True,
    )

    db.flush()

    db.refresh(sale)

    response = response_for(sale)

    complete_request(record, response)

    db.commit()

    return response


def clone_sale_as_draft(sale_id: UUID, current_user: AuthenticatedUser, db: Session, idempotency_key: str):
    record, cached = claim_request(
        db, current_user.company_id, "sales.clone", idempotency_key, {"sale_id": str(sale_id)}
    )

    if cached is not None:
        return cached

    sale = scoped_sale(db, sale_id, current_user)

    payload = CreateSaleDraftRequest(
        branch_id=sale.branch_id,
        customer_id=sale.customer_id,
        warehouse_id=sale.warehouse_id,
        currency=sale.currency,
        is_credit=sale.is_credit,
        document_type="RECEIPT" if sale.series.startswith("B") else "INVOICE",
        lines=[
            LineItemRequest(
                product_id=line.product_id,
                sku=line.sku_snapshot,
                product_name=line.name_snapshot,
                quantity=line.quantity,
                unit_price=line.unit_price_snapshot,
            )
            for line in sale.lines
        ],
    )

    warehouse = validate_context(db, payload, current_user.company_id)

    representative = db.scalar(
        select(SalesRepresentative).where(
            SalesRepresentative.company_id == current_user.company_id,
            SalesRepresentative.user_id == current_user.user_id,
            SalesRepresentative.is_active.is_(True),
        )
    )

    cloned_id = uuid4()

    lines, explanations = prepare_lines(db, payload, current_user.company_id, cloned_id)

    series = "F001" if payload.document_type == "INVOICE" else "B001"

    cloned = SaleModel(
        id=cloned_id,
        company_id=current_user.company_id,
        branch_id=payload.branch_id,
        customer_id=payload.customer_id,
        warehouse_id=warehouse.id,
        sales_rep_id=representative.id if representative else None,
        version=1,
        is_credit=payload.is_credit,
        series=series,
        number=next_number(db, current_user.company_id, series),
        status="draft",
        currency=payload.currency.upper(),
        payment_terms_days=sale.payment_terms_days,
        exchange_rate=sale.exchange_rate,
        notes=sale.notes,
        delivery_address=sale.delivery_address,
        internal_observations=sale.internal_observations,
        pricing_explanation_json=json.dumps(explanations),
        subtotal_amount=sum(line.subtotal_amount for line in lines),
        tax_amount=sum(line.tax_amount for line in lines),
        total_amount=sum(line.total_amount for line in lines),
        paid_amount=Decimal("0"),
        lines=lines,
    )

    db.add(cloned)

    db.flush()

    response = {**response_for(cloned), "cloned_sale_id": str(cloned.id), "source_sale_id": str(sale.id)}

    complete_request(record, response)

    db.commit()

    return response


def prevalidate_sale(sale_id: UUID, current_user: AuthenticatedUser, db: Session):
    sale = scoped_sale(db, sale_id, current_user)
    return sale_validation(db, sale, current_user)


def get_sale_document(sale_id: UUID, current_user: AuthenticatedUser, db: Session):
    sale = scoped_sale(db, sale_id, current_user)

    company = db.get(CompanyModel, sale.company_id)

    customer = db.get(CustomerModel, sale.customer_id)

    branch = db.get(BranchModel, sale.branch_id)

    return {
        "document_type": "FACTURA_COMERCIAL" if sale.series.startswith("F") else "BOLETA_COMERCIAL",
        "document_number": f"{sale.series}-{sale.number:08d}",
        "issue_date": (sale.confirmed_at or sale.created_at).isoformat(),
        "company": {"tax_id": company.tax_id, "legal_name": company.legal_name},
        "customer": {"code": customer.code, "legal_name": customer.legal_name, "doc_number": customer.doc_number},
        "branch": {"code": branch.code, "name": branch.name},
        "status": sale.status,
        "is_annulled": sale.status == "cancelled",
        "due_at": sale.due_at.isoformat() if sale.due_at else None,
        "due_calendar": json.loads(sale.due_calendar_snapshot_json) if sale.due_calendar_snapshot_json else None,
        "currency": sale.currency,
        "subtotal_amount": str(sale.subtotal_amount),
        "tax_amount": str(sale.tax_amount),
        "total_amount": str(sale.total_amount),
        "lines": [
            {
                "sku": line.sku_snapshot,
                "name": line.name_snapshot,
                "quantity": str(line.quantity),
                "unit_price": str(line.unit_price_snapshot),
                "total_amount": str(line.total_amount),
                "return_policy": json.loads(line.return_policy_snapshot) if line.return_policy_snapshot else None,
            }
            for line in sale.lines
        ],
    }


def correct_sale(
    sale_id: UUID, payload: CorrectSaleRequest, current_user: AuthenticatedUser, db: Session, idempotency_key: str
):
    record, cached = claim_request(
        db,
        current_user.company_id,
        "sales.correct",
        idempotency_key,
        {"sale_id": str(sale_id), "reason": payload.reason},
    )

    if cached is not None:
        return cached

    sale = scoped_sale(db, sale_id, current_user, lock=True)

    if sale.status not in ("draft", "confirmed"):
        raise HTTPException(409, "Solo se pueden corregir ventas en borrador o confirmadas.")

    old_version = sale.version

    sale.version = old_version + 1

    db.add(
        AuditLogModel(
            company_id=sale.company_id,
            actor_id=current_user.user_id,
            actor_email=current_user.email,
            action="CORRECT_SALE",
            entity_type="Sale",
            entity_id=sale.id,
            trace_id=uuid4().hex,
            payload_diff=json.dumps({"reason": payload.reason, "notes": payload.notes, "prior_version": old_version}),
            created_at=datetime.now(timezone.utc),
        )
    )

    db.flush()

    response = response_for(sale)

    complete_request(record, response)

    db.commit()

    return response
