import json
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select

from salesia.modules.pedidos.application.auxiliares.audit import audit
from salesia.modules.pedidos.application.auxiliares.emit import emit
from salesia.modules.pedidos.application.auxiliares.now import now
from salesia.shared.infrastructure.models import OrderModel
from salesia.shared.infrastructure.transactions import next_number


def build_order(
    db,
    user,
    customer_id,
    branch_id,
    warehouse_id,
    currency,
    terms,
    lines,
    subtotal,
    tax,
    total,
    quotation_id=None,
    delivery_terms=None,
    customer_po_number=None,
    attachments=None,
    reservation_expires_at=None,
):

    high_discount = max((Decimal(line["discount_pct"]) for line in lines), default=Decimal("0")) > Decimal("15")

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    customer_daily_total = db.scalar(
        select(func.coalesce(func.sum(OrderModel.total_amount), 0)).where(
            OrderModel.company_id == user.company_id,
            OrderModel.customer_id == customer_id,
            OrderModel.created_at >= today_start,
        )
    ) or Decimal("0")

    exceeds_aggregate = (customer_daily_total + total) > Decimal("20000.00")

    needs_approval = high_discount or exceeds_aggregate

    initial = "pending_approval" if needs_approval else "draft"

    history = [
        {
            "status": initial,
            "timestamp": now().isoformat(),
            "actor": user.email,
            "actor_id": str(user.user_id),
            "note": "Pedido registrado",
        }
    ]

    row = OrderModel(
        company_id=user.company_id,
        branch_id=branch_id,
        customer_id=customer_id,
        warehouse_id=warehouse_id,
        quotation_id=quotation_id,
        order_number=f"PED-{next_number(db, user.company_id, 'PED'):08d}",
        status=initial,
        currency=currency,
        subtotal_amount=subtotal,
        tax_amount=tax,
        total_amount=total,
        stock_reserved=False,
        requires_approval=needs_approval,
        payment_terms_days=terms,
        delivery_terms=delivery_terms,
        customer_po_number=customer_po_number,
        attachments_json=json.dumps(attachments or []),
        reservation_expires_at=reservation_expires_at,
        lines_json=json.dumps(lines),
        history_json=json.dumps(history),
    )

    db.add(row)

    db.flush()

    audit(db, user, "CREATE", "Order", row.id, {"number": row.order_number, "total": str(total)})

    emit(db, user.company_id, "ORDER_CREATED", "Order", row.id, {"order_id": str(row.id)})

    return row
