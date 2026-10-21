from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.clientes.application.contracts.crm import CustomerActivityCreateModel, CustomerActivityUpdateModel
from salesia.modules.clientes.domain.texto import sanitize_text
from salesia.modules.clientes.infrastructure.models import CustomerActivityModel, CustomerModel
from salesia.modules.clientes.infrastructure.perfiles import ensure_customer_profile
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainNotFoundException


def list_customer_activities(customer_id: UUID, current_user: AuthenticatedUser, db: Session):
    acts = db.scalars(
        select(CustomerActivityModel)
        .where(
            CustomerActivityModel.company_id == current_user.company_id,
            CustomerActivityModel.customer_id == customer_id,
        )
        .order_by(CustomerActivityModel.due_date.asc())
    ).all()
    return [
        {
            "id": str(a.id),
            "activity_type": a.activity_type,
            "subject": a.subject,
            "due_date": a.due_date.isoformat(),
            "status": a.status,
            "outcome": a.outcome,
        }
        for a in acts
    ]


def create_customer_activity(
    customer_id: UUID, req: CustomerActivityCreateModel, current_user: AuthenticatedUser, db: Session
):
    cust = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        )
    )
    if not cust:
        raise DomainNotFoundException("Cliente no encontrado.")

    act = CustomerActivityModel(
        id=uuid4(),
        company_id=current_user.company_id,
        customer_id=customer_id,
        activity_type=req.activity_type,
        subject=sanitize_text(req.subject) or "Actividad",
        due_date=req.due_date,
        reminder_minutes=req.reminder_minutes,
        status="pending",
        assigned_to_id=req.assigned_to_id or current_user.user_id,
    )
    db.add(act)
    db.commit()
    db.refresh(act)

    return {
        "id": str(act.id),
        "customer_id": str(customer_id),
        "activity_type": act.activity_type,
        "subject": act.subject,
        "status": act.status,
        "due_date": act.due_date.isoformat(),
    }


def list_crm_activities(view_mode: str, status: Optional[str], current_user: AuthenticatedUser, db: Session):
    query = select(CustomerActivityModel).where(CustomerActivityModel.company_id == current_user.company_id)
    if status:
        query = query.where(CustomerActivityModel.status == status)
    acts = db.scalars(query.order_by(CustomerActivityModel.due_date.asc())).all()

    items = [
        {
            "id": str(a.id),
            "customer_id": str(a.customer_id),
            "activity_type": a.activity_type,
            "subject": a.subject,
            "due_date": a.due_date.isoformat(),
            "status": a.status,
            "outcome": a.outcome,
        }
        for a in acts
    ]

    if view_mode == "calendar":
        calendar_events = {}
        for item in items:
            date_key = item["due_date"][:10]
            calendar_events.setdefault(date_key, []).append(item)
        return {"view_mode": "calendar", "events_by_date": calendar_events}

    return {"view_mode": "list", "items": items}


def update_crm_activity(
    activity_id: UUID, req: CustomerActivityUpdateModel, current_user: AuthenticatedUser, db: Session
):
    act = db.scalar(
        select(CustomerActivityModel).where(
            CustomerActivityModel.company_id == current_user.company_id, CustomerActivityModel.id == activity_id
        )
    )
    if not act:
        raise DomainNotFoundException("Actividad no encontrada.")

    if req.status:
        act.status = req.status
        if req.status == "completed":
            act.completed_at = datetime.now(timezone.utc)
    if req.outcome is not None:
        act.outcome = sanitize_text(req.outcome)

    if req.update_customer_status:
        cust = db.scalar(select(CustomerModel).where(CustomerModel.id == act.customer_id))
        if cust:
            profile = ensure_customer_profile(db, cust)
            profile.status = req.update_customer_status

    db.commit()
    db.refresh(act)
    return {
        "id": str(act.id),
        "status": act.status,
        "outcome": act.outcome,
        "completed_at": act.completed_at.isoformat() if act.completed_at else None,
    }
