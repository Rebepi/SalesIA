from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.analitica.domain.statistics import calculate_distribution
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import (
    BranchModel,
    CompanyModel,
    CustomerModel,
    InventoryStockModel,
    PaymentModel,
    ProductModel,
    SaleLineModel,
    SaleModel,
    WarehouseModel,
)
from salesia.shared.infrastructure.transactions import RefundModel


def get_dashboard_summary(
    period: str,
    branch_id: Optional[UUID],
    currency: Optional[str],
    seller_id: Optional[UUID],
    category: Optional[str],
    zone: Optional[str],
    current_user: AuthenticatedUser,
    db: Session,
    evidence_key: Optional[str] = None,
    as_of: Optional[datetime] = None,
):
    from statistics import median, quantiles

    if period not in ("7d", "30d", "90d", "12m", "all"):
        raise HTTPException(422, "Periodo inválido.")

    company = db.get(CompanyModel, current_user.company_id)
    currency = (currency or (company.base_currency if company else "USD")).strip().upper()
    if len(currency) != 3 or not currency.isalpha():
        raise HTTPException(422, "Seleccione una moneda válida de tres letras.")
    now = as_of or datetime.now(timezone.utc)
    if now.tzinfo is None or now > datetime.now(timezone.utc) + timedelta(seconds=5):
        raise HTTPException(422, "El corte debe incluir zona horaria y no puede estar en el futuro.")
    zone_filter = zone
    from salesia.modules.analitica.application.definiciones_indicadores import measurement_context
    measurement = measurement_context(db, current_user, currency, branch_id, period, now, category)

    filters = [SaleModel.company_id == current_user.company_id, SaleModel.status.in_(["confirmed", "paid"])]
    filters.append((SaleModel.confirmed_at <= now) | SaleModel.confirmed_at.is_(None))

    if period != "all":
        days = 365 if period == "12m" else int(period[:-1])

        period_start = now - timedelta(days=days)

        filters.append(SaleModel.confirmed_at >= period_start)

        filters.append(SaleModel.confirmed_at <= now)

        prev_start = period_start - timedelta(days=days)

        prev_end = period_start

        is_partial = True

        business_days = days

    else:
        days = 0

        period_start = None

        prev_start = None

        prev_end = None

        is_partial = False

        business_days = 0

    if branch_id:
        filters.append(SaleModel.branch_id == branch_id)

    if currency:
        filters.append(SaleModel.currency == currency)

    if seller_id:
        filters.append(SaleModel.sales_rep_id == seller_id)

    if zone:
        filters.append(
            SaleModel.branch_id.in_(
                select(BranchModel.id).where(
                    BranchModel.company_id == current_user.company_id,
                    (BranchModel.code.ilike(f"%{zone}%") | BranchModel.name.ilike(f"%{zone}%")),
                )
            )
        )

    if category:
        filters.append(
            SaleModel.id.in_(
                select(SaleLineModel.sale_id)
                .join(ProductModel, ProductModel.id == SaleLineModel.product_id)
                .where(SaleLineModel.company_id == current_user.company_id, ProductModel.category == category)
            )
        )

    revenue, count = db.execute(
        select(func.coalesce(func.sum(SaleModel.total_amount), 0), func.count(SaleModel.id)).where(*filters)
    ).one()

    if count > 10000:
        raise HTTPException(413, "Seleccione un periodo menor para calcular la distribución interactiva.")

    tax_amount = db.scalar(select(func.coalesce(func.sum(SaleModel.tax_amount), 0)).where(*filters)) or Decimal("0")

    valid_refund_statuses = ["confirmed", "approved", "processed", "completed"]

    refunds_q = (
        select(func.coalesce(func.sum(RefundModel.amount), 0))
        .join(PaymentModel, PaymentModel.id == RefundModel.payment_id)
        .join(SaleModel, SaleModel.id == PaymentModel.sale_id)
        .where(RefundModel.company_id == current_user.company_id, RefundModel.status.in_(valid_refund_statuses), RefundModel.currency == currency, RefundModel.unapplied_only.is_(False))
    )

    if period != "all":
        refunds_q = refunds_q.where(RefundModel.created_at >= period_start, RefundModel.created_at <= now)

    if branch_id:
        refunds_q = refunds_q.where(SaleModel.branch_id == branch_id)

    if currency:
        refunds_q = refunds_q.where(SaleModel.currency == currency)

    if seller_id:
        refunds_q = refunds_q.where(SaleModel.sales_rep_id == seller_id)

    if category:
        refunds_q = refunds_q.where(
            SaleModel.id.in_(
                select(SaleLineModel.sale_id)
                .join(ProductModel, ProductModel.id == SaleLineModel.product_id)
                .where(SaleLineModel.company_id == current_user.company_id, ProductModel.category == category)
            )
        )

    refunds_sum = db.scalar(refunds_q) or Decimal("0")

    gross_revenue = revenue

    net_revenue = revenue - refunds_sum

    unassigned_count, unassigned_rev = db.execute(
        select(func.count(SaleModel.id), func.coalesce(func.sum(SaleModel.total_amount), 0)).where(
            *filters, SaleModel.sales_rep_id.is_(None)
        )
    ).one()

    values = list(db.scalars(select(SaleModel.total_amount).where(*filters).order_by(SaleModel.total_amount)))

    average = (revenue / count).quantize(Decimal("0.01")) if count else None

    if len(values) > 1:
        quartiles = [q.quantize(Decimal("0.01")) for q in quantiles(values, n=4, method="inclusive")]

    elif values:
        quartiles = [values[0].quantize(Decimal("0.01"))] * 3

    else:
        quartiles = [None, None, None]

    median_val = str(median(values).quantize(Decimal("0.01"))) if values else None

    if period != "all":
        prev_filters = [
            SaleModel.company_id == current_user.company_id,
            SaleModel.status.in_(["confirmed", "paid"]),
            SaleModel.confirmed_at >= prev_start,
            SaleModel.confirmed_at < prev_end,
        ]

        if branch_id:
            prev_filters.append(SaleModel.branch_id == branch_id)

        if currency:
            prev_filters.append(SaleModel.currency == currency)

        if seller_id:
            prev_filters.append(SaleModel.sales_rep_id == seller_id)

        if category:
            prev_filters.append(
                SaleModel.id.in_(
                    select(SaleLineModel.sale_id)
                    .join(ProductModel, ProductModel.id == SaleLineModel.product_id)
                    .where(SaleLineModel.company_id == current_user.company_id, ProductModel.category == category)
                )
            )

        prev_rev, prev_cnt = db.execute(
            select(func.coalesce(func.sum(SaleModel.total_amount), 0), func.count(SaleModel.id)).where(*prev_filters)
        ).one()

        prev_refunds_q = (
            select(func.coalesce(func.sum(RefundModel.amount), 0))
            .join(PaymentModel, PaymentModel.id == RefundModel.payment_id)
            .join(SaleModel, SaleModel.id == PaymentModel.sale_id)
            .where(
                RefundModel.company_id == current_user.company_id,
                RefundModel.status.in_(valid_refund_statuses), RefundModel.currency == currency, RefundModel.unapplied_only.is_(False),
                RefundModel.created_at >= prev_start,
                RefundModel.created_at < prev_end,
            )
        )

        if branch_id:
            prev_refunds_q = prev_refunds_q.where(SaleModel.branch_id == branch_id)

        if currency:
            prev_refunds_q = prev_refunds_q.where(SaleModel.currency == currency)

        if seller_id:
            prev_refunds_q = prev_refunds_q.where(SaleModel.sales_rep_id == seller_id)

        if category:
            prev_refunds_q = prev_refunds_q.where(
                SaleModel.id.in_(
                    select(SaleLineModel.sale_id)
                    .join(ProductModel, ProductModel.id == SaleLineModel.product_id)
                    .where(SaleLineModel.company_id == current_user.company_id, ProductModel.category == category)
                )
            )

        prev_refunds = db.scalar(prev_refunds_q) or Decimal("0")

        prev_net_rev = prev_rev - prev_refunds

        if prev_net_rev > 0:
            delta_rev = ((net_revenue - prev_net_rev) / prev_net_rev * Decimal("100")).quantize(Decimal("0.01"))

            delta_rev_str = f"+{delta_rev}" if delta_rev > 0 else str(delta_rev)

            has_prior_data = True

        else:
            delta_rev_str = None

            has_prior_data = False

        delta_ord = (
            (Decimal(count - prev_cnt) / Decimal(prev_cnt) * Decimal("100")).quantize(Decimal("0.01"))
            if prev_cnt > 0
            else None
        )

        delta_ord_str = (
            f"+{delta_ord}"
            if (delta_ord is not None and delta_ord > 0)
            else (str(delta_ord) if delta_ord is not None else None)
        )

        comparative = {
            "previous_period_label": f"Periodo previo ({days} días)",
            "previous_revenue": str(prev_net_rev),
            "previous_gross_revenue": str(prev_rev),
            "previous_refunds": str(prev_refunds),
            "previous_orders_count": prev_cnt,
            "delta_revenue_pct": delta_rev_str,
            "delta_orders_pct": delta_ord_str,
            "has_prior_data": has_prior_data,
            "is_partial_day": is_partial,
            "cutoff_time": now.isoformat(),
            "business_days": business_days,
        }

    else:
        comparative = {
            "previous_period_label": "Todo el historial",
            "previous_revenue": "0.000000",
            "previous_gross_revenue": "0.000000",
            "previous_refunds": "0.000000",
            "previous_orders_count": 0,
            "delta_revenue_pct": None,
            "delta_orders_pct": None,
            "has_prior_data": False,
            "is_partial_day": False,
            "cutoff_time": now.isoformat(),
            "business_days": 0,
        }

    zone = ZoneInfo(measurement["timezone"])
    trend_values = db.execute(select(SaleModel.confirmed_at, SaleModel.total_amount).where(*filters).order_by(SaleModel.confirmed_at)).all()
    by_day = {}
    undated = 0
    for confirmed_at, amount in trend_values:
        if confirmed_at is None:
            undated += 1
            continue
        moment = confirmed_at.replace(tzinfo=timezone.utc) if confirmed_at.tzinfo is None else confirmed_at
        day = moment.astimezone(zone).date().isoformat()
        row = by_day.setdefault(day, {"revenue": Decimal("0"), "orders_count": 0})
        row["revenue"] += amount
        row["orders_count"] += 1
    measurement["undated_records"] = undated
    measurement["date_quality"] = "El total incluye registros sin fecha que no pueden representarse en la serie temporal." if undated else "Todas las ventas de esta selección tienen fecha de confirmación."
    trend = [{"date": day, "revenue": str(value["revenue"]), "orders_count": value["orders_count"], "is_partial": day == now.astimezone(zone).date().isoformat()} for day, value in sorted(by_day.items())]

    top_raw = db.execute(
        select(
            SaleLineModel.sku_snapshot,
            SaleLineModel.name_snapshot,
            func.sum(SaleLineModel.quantity),
            func.sum(SaleLineModel.total_amount),
        )
        .join(SaleModel, SaleModel.id == SaleLineModel.sale_id)
        .where(*filters, SaleLineModel.company_id == current_user.company_id)
        .group_by(SaleLineModel.sku_snapshot, SaleLineModel.name_snapshot)
        .order_by(func.sum(SaleLineModel.total_amount).desc())
        .limit(10)
    ).all()

    top_products = [
        {
            "sku": sku,
            "name": name,
            "units": str(units),
            "revenue": str(amt),
            "share_pct": str((amt / revenue * Decimal("100")).quantize(Decimal("0.01"))) if revenue > 0 else "0.00",
        }
        for sku, name, units, amt in top_raw
    ]

    company = db.get(CompanyModel, current_user.company_id)

    customers = (
        db.scalar(
            select(func.count(CustomerModel.id)).where(
                CustomerModel.company_id == current_user.company_id, CustomerModel.is_active.is_(True)
            )
        )
        or 0
    )

    active_purchasing_customers = (
        db.scalar(select(func.count(func.distinct(SaleModel.customer_id))).where(*filters)) or 0
    )

    products = (
        db.scalar(
            select(func.count(ProductModel.id)).where(
                ProductModel.company_id == current_user.company_id, ProductModel.is_active.is_(True)
            )
        )
        or 0
    )

    stock_filters = [InventoryStockModel.company_id == current_user.company_id]

    if branch_id:
        stock_filters.append(
            InventoryStockModel.warehouse_id.in_(
                select(WarehouseModel.id).where(
                    WarehouseModel.company_id == current_user.company_id, WarehouseModel.branch_id == branch_id
                )
            )
        )

    if category:
        stock_filters.append(
            InventoryStockModel.product_id.in_(
                select(ProductModel.id).where(
                    ProductModel.company_id == current_user.company_id, ProductModel.category == category
                )
            )
        )

    stock_row = db.execute(
        select(
            func.coalesce(func.sum(InventoryStockModel.physical_quantity), 0),
            func.coalesce(func.sum(InventoryStockModel.physical_quantity - InventoryStockModel.reserved_quantity), 0),
            func.coalesce(func.sum(InventoryStockModel.physical_quantity * InventoryStockModel.average_cost), 0),
        ).where(*stock_filters)
    ).one()

    units_breakdown_raw = db.execute(
        select(
            ProductModel.unit_of_measure,
            func.coalesce(func.sum(InventoryStockModel.physical_quantity), 0),
            func.coalesce(func.sum(InventoryStockModel.physical_quantity - InventoryStockModel.reserved_quantity), 0),
        )
        .join(ProductModel, ProductModel.id == InventoryStockModel.product_id)
        .where(*stock_filters)
        .group_by(ProductModel.unit_of_measure)
    ).all()

    units_breakdown = [
        {"unit": u or "unid.", "physical": str(p), "available": str(a)} for u, p, a in units_breakdown_raw
    ]

    inventory_summary = {
        "total_physical": str(stock_row[0]),
        "total_available": str(stock_row[1]),
        "valuation_total": str(stock_row[2]) if "products:cost:read" in current_user.permissions else None,
        "cost_visible": "products:cost:read" in current_user.permissions,
        "valuation_method": "Costo Promedio Ponderado",
        "cutoff_date": now.isoformat(),
        "has_mixed_units": len(units_breakdown) > 1,
        "units_breakdown": units_breakdown,
        "filters_applied": {"branch_id": str(branch_id) if branch_id else None, "category": category},
    }

    if values:
        histogram = calculate_distribution(values, num_bins=5)

        iqr = quartiles[2] - quartiles[0] if quartiles[2] and quartiles[0] else Decimal("0")

        lf = quartiles[0] - Decimal("1.5") * iqr if quartiles[0] else Decimal("0")

        uf = quartiles[2] + Decimal("1.5") * iqr if quartiles[2] else Decimal("0")

        outliers = [str(x) for x in values if x < lf or x > uf]

        boxplot = {
            "min": str(values[0]),
            "q1": str(quartiles[0]),
            "median": str(quartiles[1]),
            "q3": str(quartiles[2]),
            "max": str(values[-1]),
            "lower_fence": str(lf),
            "upper_fence": str(uf),
            "outliers": outliers,
            "outliers_count": len(outliers),
        }

    else:
        histogram = {"num_bins": 0, "bins": [], "count": 0}

        boxplot = {
            "min": None,
            "q1": None,
            "median": None,
            "q3": None,
            "max": None,
            "lower_fence": None,
            "upper_fence": None,
            "outliers": [],
            "outliers_count": 0,
        }

    resolved_currency = currency or (company.base_currency if company else "USD")

    from salesia.modules.analitica.application.definiciones_indicadores import dashboard_definitions
    kpi_definitions = dashboard_definitions(resolved_currency)
    from salesia.modules.analitica.application.resumen_ejecutivo import build as executive_summary
    executive = executive_summary(db, current_user, filters, resolved_currency, branch_id, category, seller_id, zone_filter, period_start, now, evidence_key)
    peak_day = max(trend, key=lambda row: (Decimal(row["revenue"]), row["date"])) if trend else None
    largest_amount = sum(values[-3:], Decimal("0"))
    if evidence_key:
        return {**executive["evidence"], "period": period, "branch_id": str(branch_id) if branch_id else None, "currency": resolved_currency, "category": category, "measurement_context": measurement}
    executive["concentration"] = {"peak_day": {**peak_day, "percent": str((Decimal(peak_day["revenue"]) / revenue * 100).quantize(Decimal("0.01"))) if revenue > 0 else None} if peak_day else None, "largest": {"count": min(3, len(values)), "amount": str(largest_amount), "percent": str((largest_amount / revenue * 100).quantize(Decimal("0.01"))) if revenue > 0 else None}, "definition": "Día principal según la zona horaria de la sede o empresa; mayores operaciones por total de documento, con los mismos filtros. Son dos concentraciones distintas. Los documentos sin fecha no se atribuyen a un día."}
    kpi_definitions["executive_scope"] = {"name": "Alcance del resumen ejecutivo", "formula": executive["scope_note"]}
    for key, name in (("margin", "Margen comercial y cobertura parcial"), ("collections", "Cobros recibidos"), ("receivables", "Cartera actual"), ("payables", "Obligaciones actuales"), ("funds", "Fondos registrados")):
        kpi_definitions[f"executive_{key}"] = {"name": name, "formula": executive[key]["note"]}
    kpi_definitions["ticket_notice"] = {"name": "Aviso del ticket promedio", "formula": "Se muestra si hay al menos diez documentos, mediana mayor que cero y promedio de al menos tres veces la mediana. Describe una diferencia, sin atribuirle una causa."}

    return {
        "total_revenue": str(revenue),
        "gross_revenue": str(gross_revenue),
        "net_revenue": str(net_revenue),
        "orders_count": count,
        "active_customers": customers,
        "active_purchasing_customers": active_purchasing_customers,
        "active_products": products,
        "average_ticket": str(average) if average is not None else None,
        "median_ticket": median_val,
        "currency": resolved_currency,
        "period": period,
        "sample_count": count,
        "distribution": {
            "min": str(values[0]) if values else None,
            "q1": str(quartiles[0]) if values else None,
            "median": str(quartiles[1]) if values else None,
            "q3": str(quartiles[2]) if values else None,
            "max": str(values[-1]) if values else None,
        },
        "comparative_period": comparative,
        "refunds_amount": str(refunds_sum),
        "tax_amount": str(tax_amount),
        "unassigned_sales": {"orders_count": unassigned_count, "revenue": str(unassigned_rev)},
        "trend": trend,
        "top_products": top_products,
        "histogram": histogram,
        "boxplot": boxplot,
        "inventory_summary": inventory_summary if "inventory:read" in current_user.permissions else None,
        "restrictions": {"inventory": "inventory:read" not in current_user.permissions, "costs": "products:cost:read" not in current_user.permissions},
        "kpi_definitions": kpi_definitions,
        "measurement_context": measurement,
        "generated_at": now.isoformat(),
        "executive": executive,
    }
