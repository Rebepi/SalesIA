from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import CompanyModel, CustomerModel, ProductModel, SaleLineModel, SaleModel


def get_customer_analytics(
    period: str,
    branch_id: Optional[UUID],
    category: Optional[str],
    segment: Optional[str],
    currency: Optional[str],
    limit: Optional[int],
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

        period_start = now - timedelta(days=days)

        filters.append(SaleModel.confirmed_at >= period_start)

    else:
        period_start = None

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

    cust_sales = db.execute(
        select(
            CustomerModel.id,
            CustomerModel.code,
            CustomerModel.legal_name,
            CustomerModel.credit_limit,
            CustomerModel.current_balance,
            func.count(SaleModel.id).label("freq"),
            func.coalesce(func.sum(SaleModel.total_amount), 0).label("tot_rev"),
            func.max(SaleModel.confirmed_at).label("last_date"),
        )
        .join(SaleModel, SaleModel.customer_id == CustomerModel.id)
        .where(*filters)
        .group_by(
            CustomerModel.id,
            CustomerModel.code,
            CustomerModel.legal_name,
            CustomerModel.credit_limit,
            CustomerModel.current_balance,
        )
        .order_by(func.sum(SaleModel.total_amount).desc())
        .limit(limit)
    ).all()

    items = []


    for row in cust_sales:
        c_id, code, legal_name, cred_lim, balance, freq, tot_rev, last_date = row


        has_prior = False

        if period_start:
            has_prior = (
                db.scalar(
                    select(func.count(SaleModel.id)).where(
                        SaleModel.company_id == current_user.company_id,
                        SaleModel.customer_id == c_id,
                        SaleModel.status.in_(["confirmed", "paid"]),
                        SaleModel.confirmed_at < period_start,
                    )
                )
                or 0
            ) > 0

        else:
            has_prior = freq > 1

        cust_type = "final_consumer" if code.upper() == "CONSUMIDOR_FINAL" or legal_name.strip().upper() == "CONSUMIDOR FINAL" else "recurring" if has_prior else "new"

        if last_date:
            last = last_date.replace(tzinfo=timezone.utc) if last_date.tzinfo is None else last_date
            zone = ZoneInfo(measurement["timezone"])
            recency = (now.astimezone(zone).date() - last.astimezone(zone).date()).days
        else:
            recency = 0

        share_pct = (
            (tot_rev / total_period_rev * Decimal("100")).quantize(Decimal("0.01"))
            if total_period_rev > 0
            else Decimal("0.00")
        )

        avg_tkt = (tot_rev / freq).quantize(Decimal("0.01")) if freq > 0 else None

        items.append(
            {
                "customer_id": str(c_id),
                "code": code,
                "legal_name": legal_name,
                "credit_limit": str(cred_lim),
                "current_balance": str(balance),
                "orders_count": int(freq),
                "total_revenue": str(tot_rev),
                "average_ticket": str(avg_tkt) if avg_tkt else None,
                "revenue_share_pct": str(share_pct),
                "last_order_date": last_date.isoformat() if last_date else None,
                "recency_days": recency,
                "customer_type": cust_type,
            }
        )

    all_cust_revs = (
        db.execute(
            select(func.coalesce(func.sum(SaleModel.total_amount), 0))
            .where(*filters)
            .group_by(SaleModel.customer_id)
            .order_by(func.sum(SaleModel.total_amount).desc())
        )
        .scalars()
        .all()
    )

    all_cust_count = len(all_cust_revs)

    top_20_count = max(1, round(all_cust_count * 0.2)) if all_cust_count > 0 else 0

    top_20_rev = sum(all_cust_revs[:top_20_count]) if top_20_count > 0 else Decimal("0")

    top_20_share = (
        (top_20_rev / total_period_rev * Decimal("100")).quantize(Decimal("0.01"))
        if total_period_rev > 0
        else Decimal("0.00")
    )

    total_customers = (
        db.scalar(
            select(func.count()).select_from(CustomerModel).where(CustomerModel.company_id == current_user.company_id)
        )
        or 0
    )

    all_sales_query = select(SaleModel.customer_id, SaleModel.confirmed_at).where(
        SaleModel.company_id == current_user.company_id,
        SaleModel.status.in_(("confirmed", "paid")),
        SaleModel.customer_id.is_not(None),
        SaleModel.confirmed_at.is_not(None),
        SaleModel.confirmed_at <= now,
        SaleModel.currency == currency,
    )

    if branch_id:
        all_sales_query = all_sales_query.where(SaleModel.branch_id == branch_id)

    all_sales = db.execute(all_sales_query.order_by(SaleModel.confirmed_at)).all()

    customer_months: dict[UUID, set[str]] = {}

    for customer_id, confirmed_at in all_sales:
        moment = confirmed_at.replace(tzinfo=timezone.utc) if confirmed_at.tzinfo is None else confirmed_at
        month_key = moment.astimezone(ZoneInfo(measurement["timezone"])).strftime("%Y-%m")

        customer_months.setdefault(customer_id, set()).add(month_key)

    cohort_members: dict[str, list[UUID]] = {}

    for customer_id, months in customer_months.items():
        first_month = min(months)

        cohort_members.setdefault(first_month, []).append(customer_id)

    cohorts = []

    for cohort_month in sorted(cohort_members.keys(), reverse=True)[:12]:
        year, month = (int(part) for part in cohort_month.split("-"))

        members = cohort_members[cohort_month]

        retention = []

        for offset in range(4):
            absolute_month = month - 1 + offset

            target_year = year + int(absolute_month / 12)

            target_month = absolute_month % 12 + 1

            target_key = f"{target_year:04d}-{target_month:02d}"

            if target_key > now.astimezone(ZoneInfo(measurement["timezone"])).strftime("%Y-%m"):
                retention.append(None)
                continue
            retained = sum(1 for customer_id in members if target_key in customer_months[customer_id])

            retention.append(
                str((Decimal(retained) / Decimal(len(members)) * Decimal("100")).quantize(Decimal("0.1")))
                if members
                else "0.0"
            )

        cohorts.append({"cohort": cohort_month, "size": len(members), "retention_pct": retention})

    company = db.get(CompanyModel, current_user.company_id)

    resolved_currency = currency or (company.base_currency if company else "USD")

    final_ids = select(CustomerModel.id).where(CustomerModel.company_id == current_user.company_id, (func.upper(CustomerModel.code) == "CONSUMIDOR_FINAL") | (func.upper(func.trim(CustomerModel.legal_name)) == "CONSUMIDOR FINAL"))
    final_consumers_count = db.scalar(select(func.count(func.distinct(SaleModel.customer_id))).where(*filters, SaleModel.customer_id.in_(final_ids))) or 0
    buyer_ids = select(SaleModel.customer_id).where(*filters, SaleModel.customer_id.not_in(final_ids)).distinct().subquery()
    if period_start:
        previous_buyers = select(SaleModel.customer_id).where(SaleModel.company_id == current_user.company_id, SaleModel.status.in_(["confirmed", "paid"]), SaleModel.confirmed_at < period_start)
        new_customers_count = db.scalar(select(func.count()).select_from(buyer_ids).where(buyer_ids.c.customer_id.notin_(previous_buyers))) or 0
    else:
        frequencies = db.scalars(select(func.count(SaleModel.id)).where(*filters, SaleModel.customer_id.not_in(final_ids)).group_by(SaleModel.customer_id)).all()
        new_customers_count = sum(1 for count in frequencies if count == 1)
    measurement["customer_classification"] = "En períodos delimitados, nuevo significa sin compras confirmadas o pagadas antes del inicio del período en la empresa, y recurrente significa con compras anteriores. Un cliente puede comprar varias veces dentro del período y seguir siendo nuevo. En todo el historial, se distingue una sola compra de varias compras dentro de la selección; es una clasificación distinta. Consumidor final se muestra aparte y no cuenta como nuevo ni recurrente."
    measurement["cohort_definition"] = "Cohortes de primera compra en la moneda y sede elegidas, usando su zona horaria. Incluyen el historial completo y no solo la ventana comercial; el mes actual está incompleto y los meses futuros no tienen porcentaje observado."
    measurement["ranking_limit"] = limit
    summary = {
        "total_customers": total_customers,
        "active_in_period": all_cust_count,
        "total_revenue": str(total_period_rev),
        "new_customers_count": new_customers_count,
        "recurring_customers_count": all_cust_count - final_consumers_count - new_customers_count,
        "final_consumers_count": final_consumers_count,
        "inactive_customers_count": max(0, total_customers - all_cust_count),
        "top_20_concentration_pct": str(top_20_share),
    }

    return {"items": items, "count": len(items), "currency": resolved_currency, "measurement_context": measurement, "summary": summary, "cohorts": cohorts}
