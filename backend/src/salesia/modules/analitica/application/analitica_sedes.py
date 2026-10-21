from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import BranchModel, CompanyModel, SaleModel


def get_branch_analytics(period: str, currency: Optional[str], current_user: AuthenticatedUser, db: Session):
    if period not in ("7d", "30d", "90d", "12m", "all"):
        raise HTTPException(422, "Periodo inválido.")

    company = db.get(CompanyModel, current_user.company_id)
    currency = (currency or (company.base_currency if company else "USD")).strip().upper()
    if len(currency) != 3 or not currency.isalpha():
        raise HTTPException(422, "Seleccione una moneda válida de tres letras.")
    now = datetime.now(timezone.utc)
    from salesia.modules.analitica.application.definiciones_indicadores import measurement_context
    measurement = measurement_context(db, current_user, currency, None, period, now)
    filters = [SaleModel.company_id == current_user.company_id, SaleModel.status.in_(("confirmed", "paid"))]

    if period != "all":
        days = 365 if period == "12m" else int(period[:-1])

        filters.append(SaleModel.confirmed_at >= now - timedelta(days=days))

    filters.append((SaleModel.confirmed_at <= now) | SaleModel.confirmed_at.is_(None))

    if currency:
        filters.append(SaleModel.currency == currency)

    total_revenue = db.scalar(select(func.coalesce(func.sum(SaleModel.total_amount), 0)).where(*filters)) or Decimal(
        "0"
    )

    branches = db.scalars(
        select(BranchModel)
        .where(BranchModel.company_id == current_user.company_id)
        .order_by(BranchModel.name)
    ).all()

    items = []

    for branch in branches:
        sales_count, revenue = db.execute(
            select(func.count(SaleModel.id), func.coalesce(func.sum(SaleModel.total_amount), 0)).where(
                *filters, SaleModel.branch_id == branch.id
            )
        ).one()

        average_ticket = (revenue / sales_count).quantize(Decimal("0.01")) if sales_count else None

        share = (
            (revenue / total_revenue * Decimal("100")).quantize(Decimal("0.01"))
            if total_revenue > 0
            else Decimal("0.00")
        )

        items.append(
            {
                "branch_id": str(branch.id),
                "code": branch.code,
                "name": branch.name,
                "is_active": branch.is_active,
                "sales_count": int(sales_count),
                "total_revenue": str(revenue),
                "average_ticket": str(average_ticket) if average_ticket is not None else None,
                "share_pct": str(share),
            }
        )

    return {"items": items, "count": len(items), "total_revenue": str(total_revenue), "period": period, "currency": currency, "measurement_context": measurement}
