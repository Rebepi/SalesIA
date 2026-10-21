from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.operaciones.infrastructure_models import SalesRepresentative
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import (
    CompanyModel,
    PaymentModel,
    ProductModel,
    SaleLineModel,
    SaleModel,
    UserModel,
)
from salesia.shared.infrastructure.transactions import RefundModel


def get_seller_analytics(
    period: str,
    branch_id: Optional[UUID],
    currency: Optional[str],
    category: Optional[str],
    current_user: AuthenticatedUser,
    db: Session,
    as_of: Optional[datetime] = None,
):
    if period not in ("7d", "30d", "90d", "12m", "all"):
        raise HTTPException(422, "Periodo inválido.")

    company = db.get(CompanyModel, current_user.company_id)
    currency = (currency or (company.base_currency if company else "USD")).strip().upper()
    if len(currency) != 3 or not currency.isalpha():
        raise HTTPException(422, "Seleccione una moneda válida de tres letras.")
    now = as_of or datetime.now(timezone.utc)
    from salesia.modules.analitica.application.definiciones_indicadores import measurement_context
    measurement = measurement_context(db, current_user, currency, branch_id, period, now, category)

    filters = [SaleModel.company_id == current_user.company_id, SaleModel.status.in_(("confirmed", "paid"))]
    filters.append((SaleModel.confirmed_at <= now) | SaleModel.confirmed_at.is_(None))

    if period != "all":
        days = 365 if period == "12m" else int(period[:-1])

        filters.append(SaleModel.confirmed_at >= now - timedelta(days=days))

    if branch_id:
        filters.append(SaleModel.branch_id == branch_id)

    if currency:
        filters.append(SaleModel.currency == currency)

    if category:
        filters.append(
            SaleModel.id.in_(
                select(SaleLineModel.sale_id)
                .join(ProductModel, ProductModel.id == SaleLineModel.product_id)
                .where(SaleLineModel.company_id == current_user.company_id, ProductModel.category == category)
            )
        )

    total_period_rev = db.scalar(select(func.coalesce(func.sum(SaleModel.total_amount), 0)).where(*filters)) or Decimal(
        "0"
    )

    users = db.scalars(
        select(UserModel)
        .where(
            UserModel.company_id == current_user.company_id,
            (UserModel.role.in_(("salesperson", "manager"))) | UserModel.id.in_(select(SaleModel.sales_rep_id).where(*filters)),
        )
        .order_by(UserModel.email)
    ).all()

    reps = db.scalars(
        select(SalesRepresentative)
        .where(SalesRepresentative.company_id == current_user.company_id)
        .order_by(SalesRepresentative.full_name)
    ).all()

    reps_by_id = {r.id: r for r in reps}

    reps_by_user = {r.user_id: r for r in reps if r.user_id}

    items = []

    seen_rep_ids = set()

    for rep in reps:
        seen_rep_ids.add(rep.id)

        sales_cnt, seller_rev = db.execute(
            select(func.count(SaleModel.id), func.coalesce(func.sum(SaleModel.total_amount), 0)).where(
                *filters, SaleModel.sales_rep_id == rep.id
            )
        ).one()

        cust_served = (
            db.scalar(
                select(func.count(func.distinct(SaleModel.customer_id))).where(
                    *filters, SaleModel.sales_rep_id == rep.id
                )
            )
            or 0
        )

        refunds_amt = db.scalar(
            select(func.coalesce(func.sum(RefundModel.amount), 0))
            .join(PaymentModel, PaymentModel.id == RefundModel.payment_id)
            .join(SaleModel, SaleModel.id == PaymentModel.sale_id)
            .where(*filters, SaleModel.sales_rep_id == rep.id, RefundModel.company_id == current_user.company_id)
        ) or Decimal("0")

        if period == "7d":
            quota = (
                (rep.monthly_quota * Decimal("7") / Decimal("30")).quantize(Decimal("0.01"))
                if rep.monthly_quota
                else Decimal("0")
            )

        elif period == "30d":
            quota = rep.monthly_quota or Decimal("0")

        elif period == "90d":
            quota = (rep.monthly_quota * Decimal("3")).quantize(Decimal("0.01")) if rep.monthly_quota else Decimal("0")

        elif period == "12m":
            quota = (rep.monthly_quota * Decimal("12")).quantize(Decimal("0.01")) if rep.monthly_quota else Decimal("0")

        else:
            quota = None

        quota_pct = (seller_rev / quota * Decimal("100")).quantize(Decimal("0.01")) if (quota and quota > 0) else None

        avg_tkt = (seller_rev / sales_cnt).quantize(Decimal("0.01")) if sales_cnt > 0 else None

        user_email = ""

        user_role = "salesperson"

        if rep.user_id:
            u = db.get(UserModel, rep.user_id)

            if u:
                user_email = u.email

                user_role = u.role

        items.append(
            {
                "seller_id": str(rep.id),
                "seller_email": user_email or rep.full_name,
                "seller_name": rep.full_name,
                "is_active": rep.is_active,
                "identifier": str(rep.id),
                "role": user_role,
                "sales_count": int(sales_cnt),
                "deals_closed": int(sales_cnt),
                "total_revenue": str(seller_rev),
                "average_ticket": str(avg_tkt) if avg_tkt else None,
                "customers_served": int(cust_served),
                "returns_amount": str(refunds_amt),
                "quota_target": str(quota) if quota is not None else None,
                "quota_completion_pct": str(quota_pct) if quota_pct is not None else None,
            }
        )

    for u in users:
        if u.id in reps_by_user and not db.scalar(select(SaleModel.id).where(*filters, SaleModel.sales_rep_id == u.id).limit(1)):
            continue

        sales_cnt, seller_rev = db.execute(
            select(func.count(SaleModel.id), func.coalesce(func.sum(SaleModel.total_amount), 0)).where(
                *filters, SaleModel.sales_rep_id == u.id
            )
        ).one()

        cust_served = (
            db.scalar(
                select(func.count(func.distinct(SaleModel.customer_id))).where(*filters, SaleModel.sales_rep_id == u.id)
            )
            or 0
        )

        refunds_amt = db.scalar(
            select(func.coalesce(func.sum(RefundModel.amount), 0))
            .join(PaymentModel, PaymentModel.id == RefundModel.payment_id)
            .join(SaleModel, SaleModel.id == PaymentModel.sale_id)
            .where(*filters, SaleModel.sales_rep_id == u.id, RefundModel.company_id == current_user.company_id)
        ) or Decimal("0")

        avg_tkt = (seller_rev / sales_cnt).quantize(Decimal("0.01")) if sales_cnt > 0 else None

        items.append(
            {
                "seller_id": str(u.id),
                "seller_email": u.email,
                "seller_name": u.email.split("@")[0],
                "is_active": u.is_active,
                "identifier": str(u.id),
                "role": u.role,
                "sales_count": int(sales_cnt),
                "deals_closed": int(sales_cnt),
                "total_revenue": str(seller_rev),
                "average_ticket": str(avg_tkt) if avg_tkt else None,
                "customers_served": int(cust_served),
                "returns_amount": str(refunds_amt),
                "quota_target": None,
                "quota_completion_pct": None,
            }
        )

    items.sort(key=lambda x: Decimal(x["total_revenue"]), reverse=True)

    assigned_sales_ids = [UUID(it["seller_id"]) for it in items]

    unassigned_cnt, unassigned_rev = db.execute(
        select(func.count(SaleModel.id), func.coalesce(func.sum(SaleModel.total_amount), 0)).where(
            *filters,
            SaleModel.sales_rep_id.is_(None),
        )
    ).one()

    unassigned_tkt = (unassigned_rev / unassigned_cnt).quantize(Decimal("0.01")) if unassigned_cnt > 0 else None

    sum_sellers_rev = sum(Decimal(it["total_revenue"]) for it in items)

    unknown_query = select(func.count(SaleModel.id), func.coalesce(func.sum(SaleModel.total_amount), 0)).where(*filters, SaleModel.sales_rep_id.is_not(None))
    if assigned_sales_ids:
        unknown_query = unknown_query.where(SaleModel.sales_rep_id.not_in(assigned_sales_ids))
    unknown_count, unknown_revenue = db.execute(unknown_query).one()
    reconciliation_checked = sum_sellers_rev + unassigned_rev + unknown_revenue == total_period_rev
    categories = {name: {"sales_count": sum(item["sales_count"] for item in items if bool(item["is_active"]) == active), "total_revenue": str(sum((Decimal(item["total_revenue"]) for item in items if bool(item["is_active"]) == active), Decimal("0")))} for name, active in (("active", True), ("inactive", False))}
    categories["unassigned"] = {"sales_count": int(unassigned_cnt), "total_revenue": str(unassigned_rev)}
    categories["unidentifiable"] = {"sales_count": int(unknown_count), "total_revenue": str(unknown_revenue)}

    company = db.get(CompanyModel, current_user.company_id)

    resolved_currency = currency or (company.base_currency if company else "USD")

    return {
        "items": items,
        "count": len(items),
        "total_revenue": str(total_period_rev),
        "currency": resolved_currency,
        "measurement_context": measurement,
        "unassigned": {
            "seller_name": "Ventas sin asignar",
            "sales_count": int(unassigned_cnt),
            "total_revenue": str(unassigned_rev),
            "average_ticket": str(unassigned_tkt) if unassigned_tkt else None,
        },
        "reconciliation_checked": reconciliation_checked,
        "categories": categories,
        "unidentifiable": categories["unidentifiable"],
    }
