import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.clientes.infrastructure.models import CustomerActivityModel, CustomerOpportunityModel
from salesia.modules.operaciones.infrastructure_models import Notification, SalesRepresentative, SalesTarget
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.ventas.application.auxiliares.period_bounds import period_bounds
from salesia.modules.ventas.application.auxiliares.rep_detail_response import rep_detail_response
from salesia.modules.ventas.application.contracts.vendedores import (
    ReassignPortfolioRequest,
    SalesRepCreateRequest,
    SalesRepUpdateRequest,
)
from salesia.shared.infrastructure.models import (
    AuditLogModel,
    BranchModel,
    CustomerProfileModel,
    PaymentModel,
    SaleModel,
    UserModel,
)
from salesia.shared.infrastructure.transactions import RefundModel, next_number


def list_sales_reps(
    period: Optional[str], team: Optional[str], branch_id: Optional[UUID], current_user: AuthenticatedUser, db: Session, limit: Optional[int] = None, offset: int = 0, search: str = ""
):
    query = select(SalesRepresentative).where(SalesRepresentative.company_id == current_user.company_id)

    if team:
        query = query.where(SalesRepresentative.team == team)

    if branch_id:
        query = query.where(SalesRepresentative.branch_id == branch_id)

    if "organization:manage" not in current_user.permissions:
        user_rep = db.scalar(
            select(SalesRepresentative).where(
                SalesRepresentative.company_id == current_user.company_id,
                SalesRepresentative.user_id == current_user.user_id,
            )
        )

        if user_rep:
            if user_rep.team:
                query = query.where(
                    (SalesRepresentative.team == user_rep.team)
                    | (SalesRepresentative.supervisor_id == current_user.user_id)
                    | (SalesRepresentative.id == user_rep.id)
                )

            else:
                query = query.where(SalesRepresentative.id == user_rep.id)

        else:
            supervised = db.scalars(
                select(SalesRepresentative.id).where(
                    SalesRepresentative.company_id == current_user.company_id,
                    SalesRepresentative.supervisor_id == current_user.user_id,
                )
            ).all()

            if supervised:
                query = query.where(SalesRepresentative.supervisor_id == current_user.user_id)

            else:
                return {"items": [], "count": 0}

    if search.strip():
        term = search.strip()
        query = query.where(SalesRepresentative.full_name.icontains(term, autoescape=True) | SalesRepresentative.code.icontains(term, autoescape=True))
    total_count = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.order_by(SalesRepresentative.full_name, SalesRepresentative.id).offset(offset).limit(limit)).all()

    items = []

    start, end = None, None

    if period:
        start, end = period_bounds(period)

    for row in rows:
        sales_q = select(SaleModel).where(
            SaleModel.company_id == current_user.company_id,
            SaleModel.sales_rep_id == row.id,
            SaleModel.status.in_(("confirmed", "paid")),
        )

        if start and end:
            sales_q = sales_q.where(SaleModel.confirmed_at >= start, SaleModel.confirmed_at < end)

        if branch_id:
            sales_q = sales_q.where(SaleModel.branch_id == branch_id)

        sales = db.scalars(sales_q).all()

        current_sales = sum((s.total_amount for s in sales), Decimal("0"))

        sales_count = len(sales)

        ticket_avg = (current_sales / sales_count).quantize(Decimal("0.01")) if sales_count > 0 else Decimal("0.00")

        refund_q = (
            select(func.coalesce(func.sum(RefundModel.amount), 0))
            .join(PaymentModel, PaymentModel.id == RefundModel.payment_id)
            .join(SaleModel, SaleModel.id == PaymentModel.sale_id)
            .where(RefundModel.company_id == current_user.company_id, SaleModel.sales_rep_id == row.id)
        )

        if start and end:
            refund_q = refund_q.where(RefundModel.created_at >= start, RefundModel.created_at < end)

        if branch_id:
            refund_q = refund_q.where(SaleModel.branch_id == branch_id)

        returns = db.scalar(refund_q) or Decimal("0")

        active_days_set = set()

        for s in sales:
            if s.confirmed_at:
                active_days_set.add(s.confirmed_at.date())

        active_days = len(active_days_set)

        target_val = None

        if period:
            st = db.scalar(
                select(SalesTarget).where(
                    SalesTarget.company_id == current_user.company_id,
                    SalesTarget.representative_id == row.id,
                    SalesTarget.period == period,
                    SalesTarget.target_type == "amount",
                )
            )

            if st:
                target_val = st.target_value

            elif row.monthly_quota and row.monthly_quota > 0:
                target_val = row.monthly_quota

        else:
            if row.monthly_quota and row.monthly_quota > 0:
                target_val = row.monthly_quota

        if target_val is not None and target_val > Decimal("0"):
            attainment = ((current_sales - returns) / target_val * Decimal("100")).quantize(Decimal("0.01"))

            attainment_str = str(attainment)

            target_str = str(target_val)

            target_configured = True

        else:
            attainment_str = None

            target_str = None

            target_configured = False

        items.append(
            {
                "rep_id": str(row.id),
                "code": row.code,
                "user_id": str(row.user_id) if row.user_id else None,
                "full_name": row.full_name,
                "branch_id": str(row.branch_id) if row.branch_id else None,
                "team": row.team,
                "supervisor_id": str(row.supervisor_id) if row.supervisor_id else None,
                "territory": row.territory,
                "monthly_quota": str(row.monthly_quota) if row.monthly_quota is not None else None,
                "current_sales": str(current_sales),
                "gross_sales": str(current_sales),
                "returns_amount": str(returns),
                "net_sales": str(current_sales - returns),
                "total_sales": str(current_sales),
                "sales_count": sales_count,
                "ticket_average": str(ticket_avg),
                "average_ticket": str(ticket_avg),
                "active_days": active_days,
                "target_quota": target_str,
                "quota_attainment_pct": attainment_str,
                "target_configured": target_configured,
                "is_active": row.is_active,
            }
        )

    return {"items": items, "count": total_count, "total_count": total_count}


def create_sales_rep(req: SalesRepCreateRequest, current_user: AuthenticatedUser, db: Session):
    if req.user_id:
        user = db.scalar(
            select(UserModel).where(
                UserModel.id == req.user_id,
                UserModel.company_id == current_user.company_id,
                UserModel.is_active.is_(True),
            )
        )

        if not user:
            raise HTTPException(422, "El usuario no existe o está inactivo.")

        if db.scalar(
            select(SalesRepresentative.id).where(
                SalesRepresentative.company_id == current_user.company_id, SalesRepresentative.user_id == req.user_id
            )
        ):
            raise HTTPException(409, "El usuario ya está asignado como vendedor.")

    if req.branch_id:
        if not db.scalar(
            select(BranchModel.id).where(
                BranchModel.id == req.branch_id, BranchModel.company_id == current_user.company_id
            )
        ):
            raise HTTPException(422, "La sucursal indicada no existe en esta empresa.")

    if req.supervisor_id:
        if not db.scalar(
            select(UserModel.id).where(
                UserModel.id == req.supervisor_id, UserModel.company_id == current_user.company_id
            )
        ):
            raise HTTPException(422, "El supervisor indicado no existe en esta empresa.")

    code = req.code

    if code:
        if db.scalar(
            select(SalesRepresentative.id).where(
                SalesRepresentative.company_id == current_user.company_id, SalesRepresentative.code == code
            )
        ):
            raise HTTPException(409, "El código de vendedor ya existe.")

    else:
        code = f"REP-{next_number(db, current_user.company_id, 'REP'):04d}"

    quota = req.monthly_quota if req.monthly_quota is not None else Decimal("0")

    row = SalesRepresentative(
        company_id=current_user.company_id,
        user_id=req.user_id,
        code=code,
        full_name=req.full_name,
        branch_id=req.branch_id,
        team=req.team,
        supervisor_id=req.supervisor_id,
        territory=req.territory or "Principal",
        monthly_quota=quota,
        is_active=True,
    )

    db.add(row)

    db.commit()

    return rep_detail_response(row)


def get_sales_rep(rep_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(SalesRepresentative).where(
            SalesRepresentative.id == rep_id, SalesRepresentative.company_id == current_user.company_id
        )
    )

    if not row:
        raise HTTPException(404, "Vendedor no encontrado.")

    return rep_detail_response(row)


def update_sales_rep(rep_id: UUID, req: SalesRepUpdateRequest, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(SalesRepresentative)
        .where(SalesRepresentative.id == rep_id, SalesRepresentative.company_id == current_user.company_id)
        .with_for_update()
    )

    if not row:
        raise HTTPException(404, "Vendedor no encontrado.")

    if req.code is not None:
        if req.code != row.code and db.scalar(
            select(SalesRepresentative.id).where(
                SalesRepresentative.company_id == current_user.company_id,
                SalesRepresentative.code == req.code,
                SalesRepresentative.id != row.id,
            )
        ):
            raise HTTPException(409, "El código de vendedor ya existe.")

        row.code = req.code

    if req.full_name is not None:
        row.full_name = req.full_name

    if req.branch_id is not None:
        if not db.scalar(
            select(BranchModel.id).where(
                BranchModel.id == req.branch_id, BranchModel.company_id == current_user.company_id
            )
        ):
            raise HTTPException(422, "Sucursal no válida.")

        row.branch_id = req.branch_id

    if req.team is not None:
        row.team = req.team

    if req.supervisor_id is not None:
        if not db.scalar(
            select(UserModel.id).where(
                UserModel.id == req.supervisor_id, UserModel.company_id == current_user.company_id
            )
        ):
            raise HTTPException(422, "Supervisor no válido.")

        row.supervisor_id = req.supervisor_id

    if req.territory is not None:
        row.territory = req.territory

    if req.monthly_quota is not None:
        row.monthly_quota = req.monthly_quota

    if req.is_active is not None:
        row.is_active = req.is_active

    db.commit()

    return rep_detail_response(row)


def preview_sales_rep_portfolio(rep_id: UUID, current_user: AuthenticatedUser, db: Session):
    rep = db.scalar(
        select(SalesRepresentative).where(
            SalesRepresentative.id == rep_id, SalesRepresentative.company_id == current_user.company_id
        )
    )

    if not rep:
        raise HTTPException(404, "Vendedor no encontrado.")

    customers = db.scalars(
        select(CustomerProfileModel).where(
            CustomerProfileModel.company_id == current_user.company_id,
            CustomerProfileModel.assigned_sales_rep_id == rep.id,
        )
    ).all()

    opps = []

    activities = []

    if rep.user_id:
        opps = db.scalars(
            select(CustomerOpportunityModel).where(
                CustomerOpportunityModel.company_id == current_user.company_id,
                CustomerOpportunityModel.assigned_to_id == rep.user_id,
                CustomerOpportunityModel.stage.notin_(("won", "lost")),
            )
        ).all()

        activities = db.scalars(
            select(CustomerActivityModel).where(
                CustomerActivityModel.company_id == current_user.company_id,
                CustomerActivityModel.assigned_to_id == rep.user_id,
                CustomerActivityModel.status != "completed",
            )
        ).all()

    return {
        "rep_id": str(rep.id),
        "full_name": rep.full_name,
        "customers_count": len(customers),
        "opportunities_count": len(opps),
        "activities_count": len(activities),
        "customers": [{"customer_id": str(c.customer_id), "status": c.status} for c in customers],
        "opportunities": [
            {"id": str(o.id), "title": o.title, "stage": o.stage, "amount": str(o.estimated_amount)} for o in opps
        ],
        "activities": [{"id": str(a.id), "subject": a.subject, "status": a.status} for a in activities],
    }


def reassign_sales_rep_portfolio(
    rep_id: UUID, req: ReassignPortfolioRequest, current_user: AuthenticatedUser, db: Session
):
    source_rep = db.scalar(
        select(SalesRepresentative).where(
            SalesRepresentative.id == rep_id, SalesRepresentative.company_id == current_user.company_id
        )
    )

    if not source_rep:
        raise HTTPException(404, "Vendedor de origen no encontrado.")

    target_rep = db.scalar(
        select(SalesRepresentative).where(
            SalesRepresentative.id == req.target_rep_id,
            SalesRepresentative.company_id == current_user.company_id,
            SalesRepresentative.is_active.is_(True),
        )
    )

    if not target_rep:
        raise HTTPException(422, "Vendedor de destino no válido o inactivo.")

    profiles = db.scalars(
        select(CustomerProfileModel).where(
            CustomerProfileModel.company_id == current_user.company_id,
            CustomerProfileModel.assigned_sales_rep_id == source_rep.id,
        )
    ).all()

    timestamp_str = datetime.now(timezone.utc).isoformat()

    for profile in profiles:
        history = json.loads(profile.assignment_history_json) if profile.assignment_history_json else []

        history.append(
            {
                "from_rep_id": str(source_rep.id),
                "to_rep_id": str(target_rep.id),
                "reassigned_by": current_user.email,
                "reason": req.reason,
                "timestamp": timestamp_str,
            }
        )

        profile.assigned_sales_rep_id = target_rep.id

        profile.assignment_history_json = json.dumps(history)

    reassigned_opps = 0

    reassigned_acts = 0

    if source_rep.user_id and target_rep.user_id:
        opps = db.scalars(
            select(CustomerOpportunityModel).where(
                CustomerOpportunityModel.company_id == current_user.company_id,
                CustomerOpportunityModel.assigned_to_id == source_rep.user_id,
                CustomerOpportunityModel.stage.notin_(("won", "lost")),
            )
        ).all()

        for o in opps:
            o.assigned_to_id = target_rep.user_id

        reassigned_opps = len(opps)

        acts = db.scalars(
            select(CustomerActivityModel).where(
                CustomerActivityModel.company_id == current_user.company_id,
                CustomerActivityModel.assigned_to_id == source_rep.user_id,
                CustomerActivityModel.status != "completed",
            )
        ).all()

        for a in acts:
            a.assigned_to_id = target_rep.user_id

        reassigned_acts = len(acts)

    if target_rep.user_id:
        db.add(
            Notification(
                company_id=current_user.company_id,
                user_id=target_rep.user_id,
                title="Cartera reasignada",
                message=f"Se le ha reasignado la cartera de {source_rep.full_name}: {len(profiles)} clientes, {reassigned_opps} oportunidades. Motivo: {req.reason}",
                event_type="PORTFOLIO_REASSIGNED",
            )
        )

    db.add(
        AuditLogModel(
            company_id=current_user.company_id,
            actor_id=current_user.user_id,
            actor_email=current_user.email,
            action="REASSIGN_PORTFOLIO",
            entity_type="SalesRepresentative",
            entity_id=source_rep.id,
            trace_id=uuid4().hex,
            payload_diff=json.dumps(
                {
                    "source_rep_id": str(source_rep.id),
                    "target_rep_id": str(target_rep.id),
                    "customers": len(profiles),
                    "reason": req.reason,
                }
            ),
        )
    )

    db.commit()

    return {
        "status": "reassigned",
        "source_rep_id": str(source_rep.id),
        "target_rep_id": str(target_rep.id),
        "reassigned_customers": len(profiles),
        "reassigned_opportunities": reassigned_opps,
        "reassigned_activities": reassigned_acts,
        "reason": req.reason,
    }
