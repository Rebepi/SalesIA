import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, Response
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from salesia.modules.catalogo.infrastructure_models import ProductBarcodeModel, ProductProfileModel
from salesia.modules.inventario.infrastructure_models import InventorySerial
from salesia.modules.pedidos.application.despacho_stock import dispatch_order_line
from salesia.modules.ventas.application.pedidos_facturacion import synchronize_order_fulfillment
from salesia.modules.clientes.infrastructure.models import CustomerProfileModel
from salesia.modules.operaciones.infrastructure_models import SalesRepresentative
from salesia.modules.pedidos.application.auxiliares.add_history import add_history
from salesia.modules.pedidos.application.auxiliares.audit import audit
from salesia.modules.pedidos.application.auxiliares.build_order import build_order
from salesia.modules.pedidos.application.auxiliares.emit import emit
from salesia.modules.pedidos.application.auxiliares.locked_order import locked_order
from salesia.modules.pedidos.application.auxiliares.money import money
from salesia.modules.pedidos.application.auxiliares.now import now
from salesia.modules.pedidos.application.auxiliares.order_response import order_response
from salesia.modules.pedidos.application.auxiliares.price_lines import price_lines
from salesia.modules.pedidos.application.auxiliares.validate_references import validate_references
from salesia.modules.pedidos.application.contracts.pedidos_registro import (
    ConfirmOrderRequest,
    DocumentLine,
    OrderCancelRequest,
    OrderCreateModel,
    PickingScanRequest,
    UpdateOrderLinesRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainForbiddenException
from salesia.shared.infrastructure.models import (
    CustomerModel,
    InventoryStockModel,
    OrderModel,
    ProductModel,
    QuotationModel,
    SaleModel,
)
from salesia.shared.infrastructure.transactions import claim_request, complete_request, next_number


def list_orders(
    response: Response,
    status_filter: Optional[str],
    customer_id: Optional[UUID],
    branch_id: Optional[UUID],
    sales_rep_id: Optional[UUID],
    active_only: bool,
    limit: int,
    offset: int,
    current_user: AuthenticatedUser,
    db: Session,
):
    query = select(OrderModel).where(OrderModel.company_id == current_user.company_id)

    if active_only:
        query = query.where(
            OrderModel.status.in_(("draft", "pending_approval", "confirmed", "backorder", "partially_fulfilled"))
        )

    elif status_filter:
        query = query.where(OrderModel.status == status_filter)

    if customer_id:
        query = query.where(OrderModel.customer_id == customer_id)

    if branch_id:
        query = query.where(OrderModel.branch_id == branch_id)

    if sales_rep_id:
        rep = db.get(SalesRepresentative, sales_rep_id)

        rep_user_id_str = str(rep.user_id) if (rep and rep.user_id) else None

        cust_sub = select(CustomerProfileModel.customer_id).where(
            CustomerProfileModel.company_id == current_user.company_id,
            CustomerProfileModel.assigned_sales_rep_id == sales_rep_id,
        )

        conds = [OrderModel.customer_id.in_(cust_sub)]

        if rep_user_id_str:
            conds.append(OrderModel.history_json.contains(rep_user_id_str))

        query = query.where(or_(*conds))

    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery()))

    response.headers["X-Total-Count"] = str(total or 0)

    joined_query = (
        query.add_columns(CustomerModel.legal_name)
        .outerjoin(CustomerModel, CustomerModel.id == OrderModel.customer_id)
        .order_by(OrderModel.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    rows = db.execute(joined_query).all()

    return [order_response(order_row, customer_name=cust_name) for order_row, cust_name in rows]


def get_order(order_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(OrderModel).where(OrderModel.id == order_id, OrderModel.company_id == current_user.company_id)
    )

    if not row:
        other = db.scalar(select(OrderModel.id).where(OrderModel.id == order_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Pedido no encontrado.")

    cust_name = db.scalar(select(CustomerModel.legal_name).where(CustomerModel.id == row.customer_id))

    return order_response(row, customer_name=cust_name)


def create_order(req: OrderCreateModel, current_user: AuthenticatedUser, db: Session, idempotency_key: str):
    record, cached = claim_request(
        db, current_user.company_id, "orders.create", idempotency_key, req.model_dump(mode="json")
    )

    if cached is not None:
        return cached

    validate_references(db, current_user.company_id, req.customer_id, req.branch_id, req.warehouse_id)

    lines, subtotal, tax, total = price_lines(db, current_user.company_id, req.lines)

    row = build_order(
        db,
        current_user,
        req.customer_id,
        req.branch_id,
        req.warehouse_id,
        req.currency,
        req.payment_terms_days,
        lines,
        subtotal,
        tax,
        total,
        delivery_terms=req.delivery_terms,
        customer_po_number=req.customer_po_number,
        attachments=req.attachments,
    )

    response = order_response(row)

    complete_request(record, response)

    db.commit()

    return response


def approve_order(order_id: UUID, current_user: AuthenticatedUser, db: Session, idempotency_key: str):
    record, cached = claim_request(db, current_user.company_id, f"orders.approve:{order_id}", idempotency_key, {})

    if cached is not None:
        return cached

    row = locked_order(db, current_user, order_id)

    history = json.loads(row.history_json) if row.history_json else []

    if history and (
        history[0].get("actor") == current_user.email or history[0].get("actor_id") == str(current_user.user_id)
    ):
        raise DomainForbiddenException("Separación de funciones: el solicitante no puede aprobar su propia excepción.")

    if row.status != "pending_approval":
        raise HTTPException(409, "El pedido no está pendiente de aprobación.")

    row.status, row.requires_approval = "draft", False

    add_history(row, "approved", current_user, "Descuento especial aprobado")

    audit(db, current_user, "APPROVE", "Order", row.id, {})

    response = order_response(row)

    complete_request(record, response)

    db.commit()

    return response


def confirm_order(
    order_id: UUID,
    req: Optional[ConfirmOrderRequest],
    current_user: AuthenticatedUser,
    db: Session,
    idempotency_key: str,
):
    body = req.model_dump(mode="json") if req else {}

    record, cached = claim_request(db, current_user.company_id, f"orders.confirm:{order_id}", idempotency_key, body)

    if cached is not None:
        return cached

    row = locked_order(db, current_user, order_id)

    if row.status not in ("draft", "pending") or row.requires_approval:
        raise HTTPException(409, "El pedido no puede confirmarse.")

    allow_bo = req.allow_backorder if req else False

    res_days = req.reservation_days if req else 7

    lines = json.loads(row.lines_json)

    has_backorder = False

    for line in lines:
        quantity = Decimal(line["quantity"])

        profile = db.scalar(select(ProductProfileModel).where(ProductProfileModel.company_id == row.company_id, ProductProfileModel.product_id == UUID(line["product_id"])))
        if profile and (profile.product_type == "service" or not profile.track_inventory):
            line["reserved_quantity"], line["backorder_quantity"], line["is_backorder"] = "0.000000", "0.000000", False
            continue

        stock = db.scalar(
            select(InventoryStockModel)
            .where(
                InventoryStockModel.company_id == row.company_id,
                InventoryStockModel.warehouse_id == row.warehouse_id,
                InventoryStockModel.product_id == UUID(line["product_id"]),
            )
            .with_for_update()
        )

        if not stock:
            raise HTTPException(409, f"Stock inexistente para {line['sku']}.")

        available = stock.physical_quantity - stock.reserved_quantity

        if available >= quantity:
            stock.reserved_quantity += quantity

            line["reserved_quantity"] = str(quantity)

            line["backorder_quantity"] = "0.000000"

            line["is_backorder"] = False

        elif allow_bo:
            reserved_portion = max(Decimal("0"), available)

            stock.reserved_quantity += reserved_portion

            line["reserved_quantity"] = str(reserved_portion)

            line["backorder_quantity"] = str(quantity - reserved_portion)

            line["is_backorder"] = True

            line["estimated_delivery_date"] = (now() + timedelta(days=14)).strftime("%Y-%m-%d")

            has_backorder = True

        else:
            raise HTTPException(409, f"Stock insuficiente para reservar {line['sku']}.")

    row.status = "backorder" if has_backorder else "confirmed"

    row.stock_reserved = not has_backorder or any(Decimal(l.get("reserved_quantity", "0")) > 0 for l in lines)

    res_expiry = (now() + timedelta(days=res_days)).isoformat()

    row.reservation_expires_at = res_expiry

    row.lines_json = json.dumps(lines)

    snapshot = {
        "customer_po_number": row.customer_po_number,
        "delivery_terms": row.delivery_terms,
        "attachments": json.loads(row.attachments_json) if row.attachments_json else [],
        "reservation_expires_at": res_expiry,
    }

    add_history(
        row,
        row.status,
        current_user,
        f"Confirmado con snapshot: terms={row.delivery_terms}, po={row.customer_po_number}",
    )

    audit(db, current_user, "CONFIRM", "Order", row.id, snapshot)

    emit(db, row.company_id, "ORDER_CONFIRMED", "Order", row.id, {"order_id": str(row.id), "status": row.status})

    response = order_response(row)

    complete_request(record, response)

    db.commit()

    return response


def update_order_lines(order_id: UUID, req: UpdateOrderLinesRequest, current_user: AuthenticatedUser, db: Session):
    row = locked_order(db, current_user, order_id)

    if row.status not in ("draft", "pending_approval"):
        raise HTTPException(409, "Solo pedidos en borrador o pendientes de aprobación pueden editarse.")

    lines, subtotal, tax, total = price_lines(db, current_user.company_id, req.lines)

    row.lines_json = json.dumps(lines)

    row.subtotal_amount = subtotal

    row.tax_amount = tax

    row.total_amount = total

    high_discount = max((Decimal(line["discount_pct"]) for line in lines), default=Decimal("0")) > Decimal("15")

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    customer_daily_total = db.scalar(
        select(func.coalesce(func.sum(OrderModel.total_amount), 0)).where(
            OrderModel.company_id == current_user.company_id,
            OrderModel.customer_id == row.customer_id,
            OrderModel.id != row.id,
            OrderModel.created_at >= today_start,
        )
    ) or Decimal("0")

    exceeds_aggregate = (customer_daily_total + total) > Decimal("20000.00")

    needs_approval = high_discount or exceeds_aggregate

    if needs_approval:
        row.requires_approval = True

        row.status = "pending_approval"

        add_history(
            row,
            "pending_approval",
            current_user,
            "Líneas editadas: aprobación previa invalidada por nuevos importes/descuentos",
        )

    else:
        row.requires_approval = False

        row.status = "draft"

        add_history(row, "draft", current_user, "Líneas editadas")

    db.commit()

    return order_response(row)


def cancel_order(
    order_id: UUID,
    req: Optional[OrderCancelRequest],
    current_user: AuthenticatedUser,
    db: Session,
    idempotency_key: str,
):
    body = req.model_dump(mode="json") if req else {}

    record, cached = claim_request(db, current_user.company_id, f"orders.cancel:{order_id}", idempotency_key, body)

    if cached is not None:
        return cached

    row = locked_order(db, current_user, order_id)

    if row.status in ("fulfilled", "cancelled"):
        raise HTTPException(409, "El pedido ya no puede cancelarse.")

    lines = json.loads(row.lines_json)

    reason = req.reason if req and req.reason else "Cancelación solicitada"

    from collections import defaultdict
    from salesia.modules.ventas.infrastructure.models import SaleModel
    invoiced = defaultdict(lambda: Decimal("0"))
    linked_sales = db.scalars(select(SaleModel).where(SaleModel.company_id == current_user.company_id, SaleModel.order_id == row.id, SaleModel.status.in_(("draft", "confirmed", "paid", "refunded")))).all()
    for sale in linked_sales:
        for sale_line in sale.lines:
            invoiced[sale_line.order_line_number] += sale_line.quantity
    requested_cancellations = {item.product_id: item.quantity for item in req.cancelled_items} if req and req.cancelled_items else None
    if requested_cancellations is not None:
        if len(requested_cancellations) != len(req.cancelled_items):
            raise HTTPException(422, "No repitas productos al cancelar cantidades.")
        known = {UUID(line["product_id"]) for line in lines}
        if not set(requested_cancellations).issubset(known):
            raise HTTPException(422, "La cancelación contiene productos ajenos al pedido.")
    for number, line in enumerate(lines, 1):
        product_id = UUID(line["product_id"])
        if requested_cancellations is not None and product_id not in requested_cancellations:
            continue
        ordered = Decimal(line["quantity"])
        fulfilled = Decimal(line.get("fulfilled_quantity", "0"))
        already_cancelled = Decimal(line.get("cancelled_quantity", "0"))
        cancelling = requested_cancellations[product_id] if requested_cancellations is not None else ordered - fulfilled - already_cancelled
        if requested_cancellations is not None and sum(1 for item in lines if item["product_id"] == str(product_id)) > 1:
            raise HTTPException(409, "La cancelación por producto es ambigua para líneas repetidas; revisa el pedido completo.")
        if cancelling > ordered - already_cancelled - max(fulfilled, invoiced[number]):
            raise HTTPException(409, f"La línea {number} contiene cantidades facturadas pendientes de entrega. Anula primero la venta correspondiente.")


    if req and req.cancelled_items:
        cancel_map = {item.product_id: item.quantity for item in req.cancelled_items}

        for line in lines:
            pid = UUID(line["product_id"])

            if pid in cancel_map:
                c_qty = cancel_map[pid]

                ordered = Decimal(line["quantity"])

                fulfilled = Decimal(line.get("fulfilled_quantity", "0"))

                prev_cancelled = Decimal(line.get("cancelled_quantity", "0"))

                remaining = ordered - fulfilled - prev_cancelled

                if c_qty > remaining:
                    raise HTTPException(409, f"La cantidad a cancelar supera el saldo pendiente de {line['sku']}.")

                reserved = Decimal(line.get("reserved_quantity", "0"))

                to_release = min(reserved, c_qty)

                if to_release > 0:
                    changed = db.execute(
                        update(InventoryStockModel)
                        .where(
                            InventoryStockModel.company_id == row.company_id,
                            InventoryStockModel.warehouse_id == row.warehouse_id,
                            InventoryStockModel.product_id == pid,
                            InventoryStockModel.reserved_quantity >= to_release,
                        )
                        .values(reserved_quantity=InventoryStockModel.reserved_quantity - to_release)
                    )

                    if changed.rowcount != 1:
                        raise HTTPException(409, f"No se pudo conciliar reserva de {line['sku']}.")

                    line["reserved_quantity"] = str(money(reserved - to_release))

                line["cancelled_quantity"] = str(money(prev_cancelled + c_qty))

        all_unserved_cancelled = all(
            Decimal(l.get("fulfilled_quantity", "0")) + Decimal(l.get("cancelled_quantity", "0"))
            >= Decimal(l["quantity"])
            for l in lines
        )

        if all_unserved_cancelled:
            row.status = (
                "fulfilled" if any(Decimal(l.get("fulfilled_quantity", "0")) > 0 for l in lines) else "cancelled"
            )

            row.stock_reserved = False

        else:
            row.status = "partially_cancelled"

            row.stock_reserved = any(Decimal(l.get("reserved_quantity", "0")) > 0 for l in lines)

        add_history(row, row.status, current_user, f"Cancelación parcial: {reason}")

    else:
        for line in lines:
            reserved = Decimal(line.get("reserved_quantity", "0"))

            if reserved > 0:
                changed = db.execute(
                    update(InventoryStockModel)
                    .where(
                        InventoryStockModel.company_id == row.company_id,
                        InventoryStockModel.warehouse_id == row.warehouse_id,
                        InventoryStockModel.product_id == UUID(line["product_id"]),
                        InventoryStockModel.reserved_quantity >= reserved,
                    )
                    .values(reserved_quantity=InventoryStockModel.reserved_quantity - reserved)
                )

                if changed.rowcount != 1:
                    raise HTTPException(409, "No se pudo reconciliar la reserva.")

                line["reserved_quantity"] = "0.000000"

            ordered = Decimal(line["quantity"])

            fulfilled = Decimal(line.get("fulfilled_quantity", "0"))

            line["cancelled_quantity"] = str(money(ordered - fulfilled))

        row.status = "fulfilled" if any(Decimal(line.get("fulfilled_quantity", "0")) > 0 for line in lines) else "cancelled"

        row.stock_reserved = False

        add_history(row, row.status, current_user, f"Saldo pendiente cancelado y reservas liberadas: {reason}")

    row.lines_json = json.dumps(lines)

    audit(db, current_user, "CANCEL", "Order", row.id, {"reason": reason, "items": body.get("cancelled_items")})

    emit(db, row.company_id, "ORDER_CANCELLED", "Order", row.id, {"order_id": str(row.id), "status": row.status})

    response = order_response(row)

    complete_request(record, response)

    db.commit()

    return response


def get_order_tracking(order_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(OrderModel).where(OrderModel.id == order_id, OrderModel.company_id == current_user.company_id)
    )

    if not row:
        raise HTTPException(404, "Pedido no encontrado.")

    linked_quotation = None

    if row.quotation_id:
        q = db.scalar(
            select(QuotationModel).where(
                QuotationModel.id == row.quotation_id, QuotationModel.company_id == current_user.company_id
            )
        )

        if q:
            linked_quotation = {"id": str(q.id), "quotation_number": q.quotation_number, "status": q.status}

    sales = db.scalars(
        select(SaleModel)
        .where(SaleModel.company_id == current_user.company_id, SaleModel.customer_id == row.customer_id)
        .order_by(SaleModel.created_at.desc())
    ).all()

    history = json.loads(row.history_json) if row.history_json else []

    timeline = []

    for h in history:
        timeline.append(
            {"event": h.get("status"), "timestamp": h.get("timestamp"), "actor": h.get("actor"), "note": h.get("note")}
        )

    next_step = (
        "Confirmar pedido"
        if row.status == "draft"
        else "Aprobar pedido"
        if row.status == "pending_approval"
        else "Despachar pedido"
        if row.status in ("confirmed", "partially_fulfilled")
        else "Completado"
        if row.status == "fulfilled"
        else "Cerrado"
    )

    return {
        "order_id": str(row.id),
        "order_number": row.order_number,
        "current_status": row.status,
        "linked_quotation": linked_quotation,
        "linked_sales": [
            {"id": str(s.id), "series_number": f"{s.series}-{s.number:08d}", "status": s.status} for s in sales[:5]
        ],
        "timeline": timeline,
        "history": history,
        "next_step": next_step,
    }


def clone_order(order_id: UUID, current_user: AuthenticatedUser, db: Session, idempotency_key: str):
    record, cached = claim_request(db, current_user.company_id, f"orders.clone:{order_id}", idempotency_key, {})

    if cached is not None:
        return cached

    source = locked_order(db, current_user, order_id)

    requested = [
        DocumentLine(
            product_id=UUID(line["product_id"]),
            quantity=Decimal(line["quantity"]),
            discount_pct=Decimal(line.get("discount_pct", "0")),
        )
        for line in json.loads(source.lines_json)
    ]

    lines, subtotal, tax, total = price_lines(db, current_user.company_id, requested)

    row = build_order(
        db,
        current_user,
        source.customer_id,
        source.branch_id,
        source.warehouse_id,
        source.currency,
        source.payment_terms_days,
        lines,
        subtotal,
        tax,
        total,
        delivery_terms=source.delivery_terms,
        customer_po_number=source.customer_po_number,
        attachments=json.loads(source.attachments_json or "[]"),
    )

    add_history(row, "draft", current_user, f"Duplicado desde {source.order_number}")

    response = order_response(row)

    complete_request(record, response)

    db.commit()

    return response


def scan_order_picking(order_id: UUID, req: PickingScanRequest, current_user: AuthenticatedUser, db: Session):
    row = locked_order(db, current_user, order_id)

    picking = json.loads(row.picking_json or "{}")

    if picking.get("status") != "PENDING":
        raise HTTPException(409, "No existe una preparación pendiente.")

    scanned_serial = db.scalar(select(InventorySerial).where(InventorySerial.company_id == row.company_id, InventorySerial.warehouse_id == row.warehouse_id, InventorySerial.serial_number == req.scanned_code, InventorySerial.status == "IN_STOCK"))
    scanned_product = db.scalar(select(ProductModel).where(ProductModel.company_id == row.company_id, ProductModel.sku == req.scanned_code))
    scanned_barcode = db.scalar(select(ProductBarcodeModel).where(ProductBarcodeModel.company_id == row.company_id, ProductBarcodeModel.barcode == req.scanned_code, ProductBarcodeModel.is_active.is_(True)))
    product_id = scanned_serial.product_id if scanned_serial else scanned_product.id if scanned_product else scanned_barcode.product_id if scanned_barcode else req.product_id
    candidates = [item for item in picking["lines"] if UUID(item["product_id"]) == product_id and not item.get("verified") and (req.order_line_number is None or item.get("order_line_number") == req.order_line_number)]
    line = candidates[0] if candidates else None

    if not line:
        raise HTTPException(422, "El artículo escaneado no pertenece a esta preparación.")

    product = db.scalar(
        select(ProductModel).where(ProductModel.id == product_id, ProductModel.company_id == row.company_id)
    )

    barcode = db.scalar(
        select(ProductBarcodeModel.id).where(
            ProductBarcodeModel.company_id == row.company_id,
            ProductBarcodeModel.product_id == product_id,
            ProductBarcodeModel.barcode == req.scanned_code,
            ProductBarcodeModel.is_active.is_(True),
        )
    )

    profile = db.scalar(select(ProductProfileModel).where(ProductProfileModel.company_id == row.company_id, ProductProfileModel.product_id == product_id))
    serial = db.scalar(select(InventorySerial).where(InventorySerial.company_id == row.company_id, InventorySerial.product_id == product_id, InventorySerial.warehouse_id == row.warehouse_id, InventorySerial.serial_number == req.scanned_code, InventorySerial.status == "IN_STOCK"))
    if profile and profile.tracking_mode == "SERIAL":
        if not serial or req.quantity != 1:
            raise HTTPException(422, "Escanea la serie de una unidad disponible para preparar este producto.")
        scanned = line.get("serial_numbers", [])
        if any(serial.serial_number in item.get("serial_numbers", []) for item in picking["lines"]):
            raise HTTPException(409, "Esa serie ya fue escaneada.")
        line["serial_numbers"] = scanned + [serial.serial_number]
    elif not product or (req.scanned_code != product.sku and not barcode):
        raise HTTPException(422, "El código escaneado no corresponde al artículo esperado.")

    picked = Decimal(line["picked_quantity"]) + req.quantity

    expected = Decimal(line["expected_quantity"])

    if picked > expected:
        raise HTTPException(409, "La cantidad escaneada supera la cantidad reservada.")

    line["picked_quantity"] = str(money(picked))

    line["verified"] = picked == expected

    row.picking_json = json.dumps(picking)

    db.commit()

    return picking


def complete_order_picking(order_id: UUID, current_user: AuthenticatedUser, db: Session, idempotency_key: str):
    record, cached = claim_request(
        db, current_user.company_id, f"orders.picking.complete:{order_id}", idempotency_key, {}
    )

    if cached is not None:
        return cached

    row = locked_order(db, current_user, order_id)

    picking = json.loads(row.picking_json or "{}")

    if (
        picking.get("status") != "PENDING"
        or not picking.get("lines")
        or not all(line.get("verified") for line in picking["lines"])
    ):
        raise HTTPException(409, "Escanee y valide todos los artículos antes de completar la preparación.")

    order_lines = json.loads(row.lines_json)

    picked_by_number = {}
    for item in picking["lines"]:
        number = item.get("order_line_number")
        if number is None:
            matches = [index for index, original in enumerate(order_lines, 1) if original["product_id"] == item["product_id"]]
            if len(matches) != 1:
                raise HTTPException(409, "Recrea la preparación para identificar las líneas repetidas del pedido.")
            number = matches[0]
        if number in picked_by_number or number > len(order_lines) or order_lines[number - 1]["product_id"] != item["product_id"]:
            raise HTTPException(409, "La preparación ya no coincide con las líneas del pedido.")
        picked_by_number[number] = item
    for number, scanned_line in picked_by_number.items():
        line = order_lines[number - 1]
        quantity = Decimal(scanned_line["picked_quantity"])
        if quantity <= 0:
            continue
        dispatch_order_line(db, row, line, quantity, scanned_line.get("serial_numbers", []))

        line["fulfilled_quantity"] = str(money(Decimal(line.get("fulfilled_quantity", "0")) + quantity))

        line["reserved_quantity"] = str(money(max(Decimal("0"), Decimal(line.get("reserved_quantity", "0")) - quantity)))

    complete = all(
        Decimal(item.get("fulfilled_quantity", "0")) + Decimal(item.get("cancelled_quantity", "0"))
        >= Decimal(item["quantity"])
        for item in order_lines
    )

    picking.update(
        {
            "status": "COMPLETED",
            "completed_at": now().isoformat(),
            "delivery_reference": f"ENT-{next_number(db, row.company_id, 'ENT'):08d}",
        }
    )

    row.lines_json = json.dumps(order_lines)

    row.picking_json = json.dumps(picking)

    row.status = "fulfilled" if complete else "partially_fulfilled"

    row.stock_reserved = any(Decimal(item.get("reserved_quantity", "0")) > 0 for item in order_lines)

    add_history(
        row, row.status, current_user, f"Preparación validada y entrega {picking['delivery_reference']} generada"
    )

    audit(db, current_user, "PICK_AND_DISPATCH", "Order", row.id, picking)

    synchronize_order_fulfillment(db, row.company_id, row.id)

    response = order_response(row)

    complete_request(record, response)

    db.commit()

    return response
