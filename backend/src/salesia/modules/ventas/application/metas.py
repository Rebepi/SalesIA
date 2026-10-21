from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.operaciones.infrastructure_models import SalesRepresentative, SalesTarget
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.ventas.application.auxiliares.period_bounds import period_bounds
from salesia.modules.ventas.application.contracts.metas import SalesTargetCreateRequest
from salesia.shared.infrastructure.models import SaleModel


def create_sales_target(req: SalesTargetCreateRequest, current_user: AuthenticatedUser, db: Session):
    rep = db.scalar(
        select(SalesRepresentative).where(
            SalesRepresentative.id == req.representative_id, SalesRepresentative.company_id == current_user.company_id
        )
    )

    if not rep:
        raise HTTPException(404, "Vendedor no encontrado.")

    existing = db.scalar(
        select(SalesTarget).where(
            SalesTarget.company_id == current_user.company_id,
            SalesTarget.representative_id == rep.id,
            SalesTarget.period == req.period,
            SalesTarget.target_type == req.target_type,
            SalesTarget.currency == req.currency,
            SalesTarget.scope == req.scope,
        )
    )

    if existing:
        existing.target_value = req.target_value

        existing.currency = req.currency

        existing.scope = req.scope

        db.commit()

        target_row = existing

    else:
        target_row = SalesTarget(
            company_id=current_user.company_id,
            representative_id=rep.id,
            period=req.period,
            target_type=req.target_type,
            target_value=req.target_value,
            currency=req.currency,
            scope=req.scope,
        )

        db.add(target_row)

        db.commit()

    return {
        "id": str(target_row.id),
        "representative_id": str(target_row.representative_id),
        "period": target_row.period,
        "target_type": target_row.target_type,
        "target_value": str(target_row.target_value),
        "currency": target_row.currency,
        "scope": target_row.scope,
        "created_at": target_row.created_at.isoformat(),
    }


def list_sales_targets(
    period: Optional[str], representative_id: Optional[UUID], current_user: AuthenticatedUser, db: Session
):
    query = select(SalesTarget).where(SalesTarget.company_id == current_user.company_id)

    if period:
        query = query.where(SalesTarget.period == period)

    if representative_id:
        query = query.where(SalesTarget.representative_id == representative_id)

    targets = db.scalars(query.order_by(SalesTarget.period.desc())).all()

    results = []

    for t in targets:
        start, end = period_bounds(t.period)

        sales_q = select(SaleModel).where(
            SaleModel.company_id == current_user.company_id,
            SaleModel.sales_rep_id == t.representative_id,
            SaleModel.status.in_(("confirmed", "paid")),
            SaleModel.confirmed_at >= start,
            SaleModel.confirmed_at < end,
        )

        sales = db.scalars(sales_q).all()

        if t.target_type == "amount":
            advance = sum((s.total_amount for s in sales if s.currency == t.currency), Decimal("0"))

        elif t.target_type == "margin":
            advance = sum((line.subtotal_amount - line.unit_cost_snapshot * line.quantity for s in sales if s.currency == t.currency for line in s.lines), Decimal("0"))

        elif t.target_type == "units":
            advance = sum((Decimal(line.quantity) for s in sales for line in s.lines), Decimal("0"))

        elif t.target_type == "clients":
            advance = Decimal(len({s.customer_id for s in sales if s.customer_id}))

        else:
            advance = Decimal("0")

        attainment = (
            (advance / t.target_value * Decimal("100")).quantize(Decimal("0.01"))
            if t.target_value > 0
            else Decimal("0")
        )

        results.append(
            {
                "id": str(t.id),
                "representative_id": str(t.representative_id),
                "period": t.period,
                "target_type": t.target_type,
                "target_value": str(t.target_value),
                "advance_value": str(advance),
                "attainment_percentage": str(attainment),
                "currency": t.currency,
                "scope": t.scope,
            }
        )

    return {"items": results, "count": len(results)}
