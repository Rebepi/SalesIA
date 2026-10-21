from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import cast, func, select, String
from sqlalchemy.orm import Session

from salesia.modules.operaciones.infrastructure_models import SalesRepresentative
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.ventas.application.auxiliares.response_for import response_for
from salesia.modules.ventas.application.auxiliares.return_summary import returned_quantity_expression, sold_quantity_expression, sale_return_quantities, sale_return_status
from salesia.modules.ventas.application.auxiliares.scoped_sale import scoped_sale
from salesia.shared.infrastructure.models import AuditLogModel, CustomerModel, PaymentModel, ProductModel, SaleLineModel, SaleModel
from salesia.shared.infrastructure.transactions import IdempotencyRecord


def list_sales(
    page: int,
    page_size: int,
    sale_status: Optional[str],
    customer_id: Optional[UUID],
    branch_id: Optional[UUID],
    sales_rep_id: Optional[UUID],
    currency: Optional[str],
    current_user: AuthenticatedUser,
    db: Session,
    warehouse_id: Optional[str] = None,
    search: Optional[str] = None,
    date_shortcut: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    document_type: Optional[str] = None,
    payment_status: Optional[str] = None,
    delivery_status: Optional[str] = None,
    sunat_status: Optional[str] = None,
    return_status: Optional[str] = None,
    min_amount: Optional[str] = None,
    max_amount: Optional[str] = None,
    only_with_balance: Optional[str] = None,
    only_overdue: Optional[str] = None,
    only_with_returns: Optional[str] = None,
    origin: Optional[str] = None,
    only_zero_cost: bool = False,
    only_unassigned: bool = False,
    only_with_lines: bool = False,
    category: Optional[str] = None,
    date_basis: str = "created",
    dashboard_period: Optional[str] = None,
    dashboard_as_of: Optional[str] = None,
):
    filters = [SaleModel.company_id == current_user.company_id]
    if only_zero_cost and "products:cost:read" not in current_user.permissions:
        raise HTTPException(403, "La consulta de líneas con costo cero requiere permiso de lectura de costos.")
    if date_basis not in ("created", "confirmed"):
        raise HTTPException(422, "Seleccione una base de fecha válida.")
    if only_unassigned:
        filters.append(SaleModel.sales_rep_id.is_(None))
    if only_zero_cost or only_with_lines:
        line_filters = [SaleLineModel.company_id == current_user.company_id]
        if only_zero_cost:
            line_filters.append(SaleLineModel.unit_cost_snapshot <= 0)
        filters.append(SaleModel.id.in_(select(SaleLineModel.sale_id).where(*line_filters)))
    if category:
        filters.append(SaleModel.id.in_(select(SaleLineModel.sale_id).join(ProductModel, ProductModel.id == SaleLineModel.product_id).where(SaleLineModel.company_id == current_user.company_id, ProductModel.company_id == current_user.company_id, ProductModel.category == category)))
    if dashboard_period:
        if dashboard_period not in ("7d", "30d", "90d", "12m", "all") or not dashboard_as_of:
            raise HTTPException(422, "El filtro ejecutivo requiere período y corte válidos.")
        try:
            cutoff = datetime.fromisoformat(dashboard_as_of)
            if cutoff.tzinfo is None or cutoff > datetime.now(timezone.utc) + timedelta(seconds=5):
                raise ValueError()
        except ValueError:
            raise HTTPException(422, "El corte ejecutivo debe incluir zona horaria y no estar en el futuro.")
        filters.extend([SaleModel.status.in_(["confirmed", "paid"]), (SaleModel.confirmed_at <= cutoff) | SaleModel.confirmed_at.is_(None)])
        if dashboard_period != "all":
            days = 365 if dashboard_period == "12m" else int(dashboard_period[:-1])
            filters.append(SaleModel.confirmed_at >= cutoff - timedelta(days=days))
    date_column = SaleModel.confirmed_at if date_basis == "confirmed" else SaleModel.created_at

    if current_user.role == "salesperson":
        rep = db.scalar(
            select(SalesRepresentative).where(
                SalesRepresentative.company_id == current_user.company_id,
                SalesRepresentative.user_id == current_user.user_id,
                SalesRepresentative.is_active.is_(True),
            )
        )

        if rep:
            filters.append(SaleModel.sales_rep_id == rep.id)

    elif sales_rep_id:
        filters.append(SaleModel.sales_rep_id == sales_rep_id)

    if sale_status:
        st = sale_status.strip().lower()
        if st in ("draft", "borrador"):
            filters.append(SaleModel.status == "draft")
        elif st in ("confirmed", "confirmada"):
            filters.append(SaleModel.status.in_(["confirmed", "paid"]))
        elif st in ("cancelled", "anulada", "anulado"):
            filters.append(SaleModel.status == "cancelled")
        elif st in ("paid", "pagada", "pagado"):
            filters.append(SaleModel.status == "paid")
        elif st in ("refunded", "reembolsada", "reembolsado"):
            filters.append(SaleModel.status == "refunded")
        else:
            filters.append(SaleModel.status == sale_status)

    if customer_id:
        filters.append(SaleModel.customer_id == customer_id)

    if branch_id:
        filters.append(SaleModel.branch_id == branch_id)

    if warehouse_id and str(warehouse_id).strip():
        try:
            filters.append(SaleModel.warehouse_id == UUID(str(warehouse_id).strip()))
        except Exception:
            pass

    if currency:
        filters.append(SaleModel.currency == currency.upper())

    if search and str(search).strip():
        term = f"%{str(search).strip()}%"
        filters.append(
            SaleModel.series.ilike(term)
            | cast(SaleModel.number, String).ilike(term)
            | SaleModel.customer.has(CustomerModel.legal_name.ilike(term))
            | SaleModel.customer.has(CustomerModel.doc_number.ilike(term))
            | cast(SaleModel.total_amount, String).ilike(term)
        )

    now = datetime.now(timezone.utc)
    if date_shortcut == "today":
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        filters.append(date_column >= today_start)
    elif date_shortcut == "yesterday":
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        yesterday_start = today_start - timedelta(days=1)
        filters.append(date_column >= yesterday_start)
        filters.append(date_column < today_start)
    elif date_shortcut == "this_week":
        week_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc) - timedelta(days=now.weekday())
        filters.append(date_column >= week_start)
    elif date_shortcut == "this_month":
        month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        filters.append(date_column >= month_start)
    elif date_shortcut == "last_30_days":
        past_30 = now - timedelta(days=30)
        filters.append(date_column >= past_30)

    if date_from and str(date_from).strip():
        try:
            df = datetime.fromisoformat(str(date_from).strip())
            if df.tzinfo is None:
                df = df.replace(tzinfo=timezone.utc)
            filters.append(date_column >= df)
        except Exception:
            pass

    if date_to and str(date_to).strip():
        try:
            dt = datetime.fromisoformat(str(date_to).strip())
            if dt.tzinfo is None:
                dt = datetime(dt.year, dt.month, dt.day, 23, 59, 59, 999999, tzinfo=timezone.utc)
            filters.append(date_column <= dt)
        except Exception:
            pass

    if document_type and str(document_type).strip():
        dt_val = str(document_type).strip().upper()
        if dt_val in ("INVOICE", "FACTURA"):
            filters.append(SaleModel.series.ilike("F%"))
        elif dt_val in ("RECEIPT", "BOLETA"):
            filters.append(SaleModel.series.ilike("B%"))
        elif dt_val in ("SALE_NOTE", "NOTA_VENTA"):
            filters.append(SaleModel.series.ilike("NV%") | SaleModel.series.ilike("N%"))

    if payment_status and str(payment_status).strip():
        ps = str(payment_status).strip().lower()
        if ps in ("sin cobrar", "unpaid"):
            filters.append(SaleModel.paid_amount <= 0)
        elif ps in ("pagada", "paid"):
            filters.append(SaleModel.paid_amount >= SaleModel.total_amount)
            filters.append(SaleModel.total_amount > 0)
        elif ps in ("parcial", "partial"):
            filters.append(SaleModel.paid_amount > 0)
            filters.append(SaleModel.paid_amount < SaleModel.total_amount)
        elif ps in ("vencida", "overdue"):
            filters.append(SaleModel.paid_amount < SaleModel.total_amount)
            filters.append(SaleModel.status == "confirmed")

    if delivery_status and str(delivery_status).strip():
        ds = str(delivery_status).strip().lower()
        if ds in ("pendiente", "pending"):
            filters.append(SaleModel.status == "draft")
        elif ds in ("entregada", "delivered"):
            filters.append(SaleModel.status.in_(["confirmed", "paid"]))
        elif ds in ("no aplica", "n/a"):
            filters.append(SaleModel.status == "cancelled")

    if sunat_status and str(sunat_status).strip():
        ss = str(sunat_status).strip().lower()
        if ss in ("aceptado", "accepted"):
            filters.append(SaleModel.status.in_(["confirmed", "paid"]))
        elif ss in ("no aplica", "n/a"):
            filters.append(SaleModel.status == "draft")
        elif ss in ("baja", "annulled"):
            filters.append(SaleModel.status == "cancelled")
        elif ss in ("rechazado", "rejected"):
            filters.append(SaleModel.status == "rejected")

    if return_status and str(return_status).strip():
        rs = str(return_status).strip().lower()
        returned = returned_quantity_expression(current_user.company_id)
        sold = sold_quantity_expression(current_user.company_id)
        if rs == "total":
            filters.append((SaleModel.status == "refunded") | ((returned > 0) & (returned >= sold)))
        elif rs == "parcial":
            filters.extend([SaleModel.status != "refunded", returned > 0, returned < sold])
        elif rs in ("sin devolución", "none"):
            filters.extend([SaleModel.status != "refunded", returned == 0])

    if only_with_balance in (True, "true", "True", "1", 1):
        filters.append(SaleModel.paid_amount < SaleModel.total_amount)

    if only_overdue in (True, "true", "True", "1", 1):
        filters.append(SaleModel.paid_amount < SaleModel.total_amount)
        filters.append(SaleModel.status.in_(["confirmed"]))

    if only_with_returns in (True, "true", "True", "1", 1):
        filters.append((SaleModel.status == "refunded") | (returned_quantity_expression(current_user.company_id) > 0))

    if min_amount is not None and str(min_amount).strip():
        try:
            filters.append(SaleModel.total_amount >= Decimal(str(min_amount).strip()))
        except Exception:
            pass

    if max_amount is not None and str(max_amount).strip():
        try:
            filters.append(SaleModel.total_amount <= Decimal(str(max_amount).strip()))
        except Exception:
            pass

    total = db.scalar(select(func.count()).select_from(SaleModel).where(*filters))

    rows = db.scalars(
        select(SaleModel)
        .where(*filters)
        .order_by(SaleModel.created_at.desc(), SaleModel.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return_quantities = sale_return_quantities(db, current_user.company_id, rows)
    matching_lines = None
    line_counts = {}
    if only_zero_cost:
        line_counts = dict(db.execute(select(SaleLineModel.sale_id, func.count()).where(SaleLineModel.company_id == current_user.company_id, SaleLineModel.sale_id.in_([sale.id for sale in rows]), SaleLineModel.unit_cost_snapshot <= 0).group_by(SaleLineModel.sale_id)).all()) if rows else {}
        matching_lines = db.scalar(select(func.count(SaleLineModel.id)).where(SaleLineModel.company_id == current_user.company_id, SaleLineModel.sale_id.in_(select(SaleModel.id).where(*filters)), SaleLineModel.unit_cost_snapshot <= 0)) or 0
    return {"items": [{**response_for(s), "return_status": sale_return_status(s, return_quantities.get(s.id, {})), **({"zero_cost_lines_count": line_counts.get(s.id, 0)} if only_zero_cost else {})} for s in rows], "total": int(total or 0), "total_count": int(total or 0), "page": page, "page_size": page_size, "matching_lines_count": matching_lines}


def export_sales(current_user: AuthenticatedUser, db: Session):
    rows = db.scalars(
        select(SaleModel).where(SaleModel.company_id == current_user.company_id).order_by(SaleModel.created_at.desc())
    ).all()

    return {"exported_records": len(rows), "sales": [response_for(s) for s in rows]}


def lookup_sales(search: Optional[str], limit: int, offset: int, current_user: AuthenticatedUser, db: Session):
    filters = [SaleModel.company_id == current_user.company_id]

    if search:
        term = f"%{search.strip()}%"

        filters.append(
            SaleModel.series.ilike(term) | CustomerModel.legal_name.ilike(term) | CustomerModel.doc_number.ilike(term)
        )

    query = (
        select(SaleModel, CustomerModel)
        .join(
            CustomerModel,
            (CustomerModel.id == SaleModel.customer_id) & (CustomerModel.company_id == SaleModel.company_id),
        )
        .where(*filters)
    )

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0

    rows = db.execute(query.order_by(SaleModel.created_at.desc()).offset(offset).limit(limit)).all()

    return {
        "items": [
            {**response_for(sale), "customer_name": customer.legal_name, "customer_document": customer.doc_number}
            for sale, customer in rows
        ],
        "total_count": total,
        "limit": limit,
        "offset": offset,
    }


def get_sale_by_idempotency_key(key: str, operation: str, current_user: AuthenticatedUser, db: Session):
    rec = db.get(IdempotencyRecord, {"company_id": current_user.company_id, "operation": operation, "key": key})

    if not rec or not rec.response_json:
        raise HTTPException(404, "Operación no encontrada.")

    return json.loads(rec.response_json)


def get_sale(sale_id: UUID, current_user: AuthenticatedUser, db: Session):
    sale = scoped_sale(db, sale_id, current_user)
    returned = sale_return_quantities(db, current_user.company_id, [sale]).get(sale.id, {})

    payments = db.scalars(
        select(PaymentModel).where(PaymentModel.company_id == current_user.company_id, PaymentModel.sale_id == sale.id)
    ).all()

    audit_logs = db.scalars(
        select(AuditLogModel)
        .where(
            AuditLogModel.company_id == current_user.company_id,
            AuditLogModel.entity_type == "Sale",
            AuditLogModel.entity_id == sale.id,
        )
        .order_by(AuditLogModel.created_at)
    ).all()

    cust_name = ""
    cust_doc = ""
    if hasattr(sale, "customer") and sale.customer:
        cust_name = getattr(sale.customer, "legal_name", "") or getattr(sale.customer, "name", "")
        cust_doc = f"{getattr(sale.customer, 'doc_type', '')} {getattr(sale.customer, 'doc_number', '')}".strip()

    return {
        **response_for(sale),
        "return_status": sale_return_status(sale, returned),
        "customer_name": cust_name,
        "customer_document": cust_doc,
        "lines": [
            {
                "product_id": str(line.product_id),
                "sale_line_id": str(line.id),
                "order_line_number": line.order_line_number,
                "sku": line.sku_snapshot,
                "name": line.name_snapshot,
                "product_name": line.name_snapshot,
                "quantity": str(line.quantity),
                "unit_price": str(line.unit_price_snapshot),
                **({"unit_cost": str(line.unit_cost_snapshot)} if "products:cost:read" in current_user.permissions else {}),
                "discount": str(line.discount_amount),
                "tax_amount": str(line.tax_amount),
                "total_amount": str(line.total_amount),
                "unit_of_measure": line.unit_of_measure_snapshot,
                "delivered_quantity": str(line.fulfilled_quantity if line.fulfilled_quantity is not None else line.quantity) if sale.status in ("confirmed", "paid") else "0",
                "returned_quantity": str(returned.get(line.id, Decimal("0"))),
                "serial_numbers": json.loads(line.serial_numbers_json or "[]"),
            }
            for line in sale.lines
        ],
        "payments": [
            {
                "payment_id": str(p.id),
                "id": str(p.id),
                "amount": str(p.amount),
                "currency": p.currency,
                "payment_method": p.payment_method,
                "status": p.status,
                "reference_code": p.reference_code,
                "created_at": p.created_at.isoformat() if hasattr(p, "created_at") and p.created_at else None,
            }
            for p in payments
        ],
        "timeline": [
            {"action": a.action, "actor_email": a.actor_email, "created_at": a.created_at.isoformat()}
            for a in audit_logs
        ],
    }
