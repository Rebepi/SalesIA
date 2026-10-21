from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from salesia.modules.finanzas.infrastructure_models import ReturnLineModel, ReturnModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import CompanyModel, ProductModel, SaleLineModel, SaleModel


def get_product_analytics(
    period: str,
    category: Optional[str],
    branch_id: Optional[UUID],
    currency: Optional[str],
    limit: Optional[int],
    metric: str,
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

    if metric not in ("revenue", "units", "margin"):
        raise HTTPException(422, "Ordene los productos por facturación, unidades o margen de venta.")
    cost_visible = "products:cost:read" in current_user.permissions
    if metric == "margin" and not cost_visible:
        raise HTTPException(403, "Ordenar o consultar por margen requiere permiso de lectura de costos.")

    prod_q = (
        select(
            ProductModel.id,
            ProductModel.sku,
            ProductModel.name,
            ProductModel.category,
            ProductModel.unit_price,
            ProductModel.unit_cost,
            func.sum(SaleLineModel.quantity).label("units"),
            func.sum(SaleLineModel.subtotal_amount).label("subtotal"),
            func.sum(SaleLineModel.total_amount).label("revenue"),
            func.sum(SaleLineModel.quantity * SaleLineModel.unit_cost_snapshot).label("historical_cost"),
            func.sum(case((SaleLineModel.unit_cost_snapshot <= 0, 1), else_=0)).label("zero_cost_lines"),
        )
        .join(SaleLineModel, SaleLineModel.product_id == ProductModel.id)
        .join(SaleModel, SaleModel.id == SaleLineModel.sale_id)
        .where(*filters, SaleLineModel.company_id == current_user.company_id)
        .group_by(
            ProductModel.id,
            ProductModel.sku,
            ProductModel.name,
            ProductModel.category,
            ProductModel.unit_price,
            ProductModel.unit_cost,
        )
    )

    if category:
        prod_q = prod_q.where(ProductModel.category == category)

    ordering = func.sum(SaleLineModel.quantity) if metric == "units" else func.sum(SaleLineModel.subtotal_amount - SaleLineModel.quantity * SaleLineModel.unit_cost_snapshot) if metric == "margin" else func.sum(SaleLineModel.total_amount)
    prod_q = prod_q.order_by(ordering.desc(), ProductModel.id)

    sales_results = db.execute(prod_q).all()
    total_period_rev = sum((row.revenue for row in sales_results), Decimal("0"))
    document_filters = list(filters)
    if category:
        document_filters.append(SaleModel.id.in_(select(SaleLineModel.sale_id).join(ProductModel, ProductModel.id == SaleLineModel.product_id).where(SaleLineModel.company_id == current_user.company_id, ProductModel.company_id == current_user.company_id, ProductModel.category == category)))
    document_revenue = db.scalar(select(func.coalesce(func.sum(SaleModel.total_amount), 0)).where(*document_filters)) or Decimal("0")
    detailed_ids = select(SaleLineModel.sale_id).where(SaleLineModel.company_id == current_user.company_id)
    missing_count, missing_revenue = db.execute(select(func.count(SaleModel.id), func.coalesce(func.sum(SaleModel.total_amount), 0)).where(*document_filters, SaleModel.id.not_in(detailed_ids))).one()
    coverage = {"detail_revenue": str(total_period_rev), "document_revenue": str(document_revenue), "percent": str((total_period_rev / document_revenue * 100).quantize(Decimal("0.01"))) if document_revenue > 0 else None, "documents_without_detail": missing_count, "amount_without_detail": str(missing_revenue), "definition": "Participación: importe del producto dividido entre el importe de todas las líneas de productos seleccionadas, antes de limitar el ranking. Cobertura: importe de esas líneas dividido entre el total de documentos con los mismos filtros. Con categoría, los documentos se seleccionan por contener esa categoría y el detalle solo incluye sus líneas."}

    items = []

    for row in sales_results:
        p_id, sku, name, cat, price, cost, units, subtotal, rev, historical_cost, zero_cost_lines = row

        margin = subtotal - historical_cost

        margin_pct = (margin / subtotal * Decimal("100")).quantize(Decimal("0.01")) if subtotal > 0 else Decimal("0.00")

        share_pct = (
            (rev / total_period_rev * Decimal("100")).quantize(Decimal("0.01"))
            if total_period_rev > 0
            else Decimal("0.00")
        )

        ret_units, ret_amt = db.execute(
            select(
                func.coalesce(func.sum(ReturnLineModel.quantity), 0),
                func.coalesce(func.sum(ReturnLineModel.quantity * (ReturnLineModel.unit_price_snapshot - ReturnLineModel.discount_per_unit) * (1 + ReturnLineModel.tax_rate_snapshot)), 0),
            )
            .join(ReturnModel, ReturnModel.id == ReturnLineModel.return_id)
            .where(
                ReturnModel.company_id == current_user.company_id,
                ReturnLineModel.product_id == p_id,
                ReturnModel.status == "accepted",
                ReturnModel.created_at <= now,
                ReturnModel.sale_id.in_(select(SaleModel.id).where(*filters).correlate(None)),
            )
        ).one()

        items.append(
            {
                "product_id": str(p_id),
                "has_zero_cost": bool(zero_cost_lines),
                "sku": sku,
                "name": name,
                "category": cat,
                "unit_price": str(price),
                "unit_cost": str(cost),
                "historical_cost": str(historical_cost),
                "units": str(units),
                "base_commercial": str(subtotal),
                "revenue": str(rev),
                "share_pct": str(share_pct),
                "margin_amount": str(margin),
                "margin_pct": str(margin_pct),
                "returns_units": str(ret_units),
                "returns_amount": str(ret_amt),
            }
        )

    other_categories = None

    if limit is not None and len(items) > limit:
        primary_items = items[:limit]

        tail_items = items[limit:]

        other_rev = sum(Decimal(it["revenue"]) for it in tail_items)

        other_units = sum(Decimal(it["units"]) for it in tail_items)

        other_base = sum(Decimal(it["base_commercial"]) for it in tail_items)

        other_margin = sum(Decimal(it["margin_amount"]) for it in tail_items)

        other_margin_pct = (
            (other_margin / other_base * Decimal("100")).quantize(Decimal("0.01"))
            if other_base > 0
            else Decimal("0.00")
        )

        other_share = (
            (other_rev / total_period_rev * Decimal("100")).quantize(Decimal("0.01"))
            if total_period_rev > 0
            else Decimal("0.00")
        )

        other_categories = {
            "name": "Otros",
            "products_count": len(tail_items),
            "units": str(other_units),
            "revenue": str(other_rev),
            "share_pct": str(other_share),
            "margin_amount": str(other_margin),
            "margin_pct": str(other_margin_pct),
        }

        items = primary_items

    company = db.get(CompanyModel, current_user.company_id)

    resolved_currency = currency or (company.base_currency if company else "USD")

    if not cost_visible:
        for item in items:
            item["has_zero_cost"] = None
            for key in ("unit_cost", "historical_cost", "margin_amount", "margin_pct"):
                item[key] = None
        if other_categories:
            other_categories["margin_amount"] = None
            other_categories["margin_pct"] = None
    return {
        "items": items,
        "count": len(items),
        "total_revenue": str(total_period_rev),
        "currency": resolved_currency,
        "measurement_context": measurement,
        "other_categories": other_categories,
        "cost_visible": cost_visible,
        "coverage": coverage,
        "definitions": {"revenue": "Suma del total de líneas de ventas confirmadas o pagadas, en la moneda seleccionada y con los filtros de venta y categoría aplicados.", "margin": "Base comercial sin impuestos menos el costo histórico de cada línea multiplicado por su cantidad. No usa el costo actual del catálogo ni descuenta logística, gastos o comisiones.", "catalog_cost": "unit_cost es el costo vigente del catálogo; historical_cost es el costo conservado en las ventas seleccionadas. No representan la misma fecha.", "returns": "Unidades e importe conservado en las líneas de devoluciones aceptadas de las ventas seleccionadas, conocidas al consultar. Se muestran aparte y no se descuentan otra vez de la facturación o margen de esta tabla.", "currency": currency, "date_reference": "confirmed_at", "cutoff": now.isoformat(), "ordering": metric},
    }
