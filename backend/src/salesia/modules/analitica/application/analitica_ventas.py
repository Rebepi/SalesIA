from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.analitica.domain.statistics import compute_statistical_summary
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import CompanyModel, ProductModel, SaleLineModel, SaleModel


def get_sales_analytics(
    period: str,
    granularity: str,
    branch_id: Optional[UUID],
    currency: Optional[str],
    category: Optional[str],
    current_user: AuthenticatedUser,
    db: Session,
    as_of: Optional[datetime] = None,
):
    if period not in ("7d", "30d", "90d", "12m", "all"):
        raise HTTPException(422, "Periodo inválido.")

    if granularity not in ("day", "week", "month"):
        raise HTTPException(422, "Granularidad inválida.")

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
        days = 0

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

    company = db.get(CompanyModel, current_user.company_id)

    resolved_currency = currency or (company.base_currency if company else "USD")

    sales = db.execute(select(SaleModel).where(*filters).order_by(SaleModel.confirmed_at.desc())).scalars().all()

    def bucket_key(value: datetime) -> str:
        value = (value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value).astimezone(ZoneInfo(measurement["timezone"]))

        if granularity == "month":
            return value.strftime("%Y-%m")

        if granularity == "week":
            return (value.date() - timedelta(days=value.weekday())).isoformat()

        return value.date().isoformat()

    if not sales:
        empty_series = []

        if period != "all":
            empty_keys: list[str] = []

            for i in range(days):
                d = bucket_key(now - timedelta(days=days - 1 - i))

                if d in empty_keys:
                    continue

                empty_keys.append(d)

                empty_series.append(
                    {"date": d, "revenue": "0.000000", "orders_count": 0, "status": "zero_sales", "has_data": True}
                )

        return {
            "count": 0,
            "mean_sale": None,
            "median_sale": None,
            "min_sale": None,
            "max_sale": None,
            "total_volume": "0.000000",
            "skewness": None,
            "granularity": granularity,
            "period": period,
            "currency": resolved_currency,
            "measurement_context": measurement,
            "series": empty_series,
            "breakdown": {"recorded_days": 0, "zero_sales_days": len(empty_series), "no_data_days": 0},
        }

    measurement["undated_records"] = sum(1 for sale in sales if sale.confirmed_at is None)
    measurement["date_quality"] = "Los registros sin fecha permanecen en el total histórico, pero no en la serie temporal." if measurement["undated_records"] else "Todas las ventas seleccionadas tienen fecha de confirmación."
    amounts = [s.total_amount for s in sales]

    summary = compute_statistical_summary(amounts)

    buckets_map: dict[str, dict[str, Any]] = {}

    if period != "all":
        for i in range(days):
            d = bucket_key(now - timedelta(days=days - 1 - i))

            if d in buckets_map:
                continue

            buckets_map[d] = {
                "date": d,
                "revenue": Decimal("0"),
                "orders_count": 0,
                "status": "zero_sales",
                "has_data": True,
            }

    for s in sales:
        if s.confirmed_at:
            d_str = bucket_key(s.confirmed_at)

            if d_str not in buckets_map:
                buckets_map[d_str] = {
                    "date": d_str,
                    "revenue": Decimal("0"),
                    "orders_count": 0,
                    "status": "recorded",
                    "has_data": True,
                }

            buckets_map[d_str]["revenue"] += s.total_amount

            buckets_map[d_str]["orders_count"] += 1

            buckets_map[d_str]["status"] = "recorded"

    sorted_series = []

    for d_key in sorted(buckets_map.keys()):
        item = buckets_map[d_key]

        sorted_series.append(
            {
                "date": item["date"],
                "revenue": str(item["revenue"]),
                "orders_count": item["orders_count"],
                "status": item["status"],
                "has_data": item["has_data"],
            }
        )

    rec_days = len([b for b in sorted_series if b["status"] == "recorded"])

    zero_days = len([b for b in sorted_series if b["status"] == "zero_sales"])

    return {
        "count": summary.count,
        "mean_sale": str(summary.mean),
        "median_sale": str(summary.median),
        "min_sale": str(summary.minimum),
        "max_sale": str(summary.maximum),
        "total_volume": str(summary.sum_total),
        "skewness": summary.skewness_direction,
        "granularity": granularity,
        "period": period,
        "currency": resolved_currency,
        "measurement_context": measurement,
        "series": sorted_series,
        "breakdown": {"recorded_days": rec_days, "zero_sales_days": zero_days, "no_data_days": 0},
    }
