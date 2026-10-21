import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from salesia.modules.clientes.application.contracts.comercial import CustomerAssignmentModel
from salesia.modules.clientes.infrastructure.models import (
    CustomerActivityModel,
    CustomerModel,
    CustomerOpportunityModel,
)
from salesia.modules.clientes.infrastructure.perfiles import ensure_customer_profile
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainNotFoundException


def get_customer_assignment(customer_id: UUID, current_user: AuthenticatedUser, db: Session):
    cust = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        )
    )
    if not cust:
        raise DomainNotFoundException("Cliente no encontrado.")

    profile = ensure_customer_profile(db, cust)
    return {
        "customer_id": str(customer_id),
        "assigned_sales_rep_id": str(profile.assigned_sales_rep_id) if profile.assigned_sales_rep_id else None,
        "sales_team": profile.sales_team,
        "backup_sales_rep_id": str(profile.backup_sales_rep_id) if profile.backup_sales_rep_id else None,
        "history": json.loads(profile.assignment_history_json),
    }


def update_customer_assignment(
    customer_id: UUID, req: CustomerAssignmentModel, current_user: AuthenticatedUser, db: Session
):
    cust = db.scalar(
        select(CustomerModel).where(
            CustomerModel.company_id == current_user.company_id, CustomerModel.id == customer_id
        )
    )
    if not cust:
        raise DomainNotFoundException("Cliente no encontrado.")

    profile = ensure_customer_profile(db, cust)
    history = json.loads(profile.assignment_history_json)
    history.append(
        {
            "previous_rep": str(profile.assigned_sales_rep_id) if profile.assigned_sales_rep_id else None,
            "new_rep": str(req.assigned_sales_rep_id) if req.assigned_sales_rep_id else None,
            "team": req.sales_team,
            "backup_rep": str(req.backup_sales_rep_id) if req.backup_sales_rep_id else None,
            "actor": current_user.email,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": req.reason,
        }
    )

    profile.assigned_sales_rep_id = req.assigned_sales_rep_id
    profile.sales_team = req.sales_team
    profile.backup_sales_rep_id = req.backup_sales_rep_id
    profile.assignment_history_json = json.dumps(history)
    profile.version += 1

    if req.assigned_sales_rep_id:
        db.execute(
            update(CustomerActivityModel)
            .where(
                CustomerActivityModel.company_id == current_user.company_id,
                CustomerActivityModel.customer_id == customer_id,
                CustomerActivityModel.status == "pending",
            )
            .values(assigned_to_id=req.assigned_sales_rep_id)
        )
        db.execute(
            update(CustomerOpportunityModel)
            .where(
                CustomerOpportunityModel.company_id == current_user.company_id,
                CustomerOpportunityModel.customer_id == customer_id,
                CustomerOpportunityModel.stage.notin_(("won", "lost")),
            )
            .values(assigned_to_id=req.assigned_sales_rep_id)
        )

    db.commit()
    return {
        "status": "updated",
        "assigned_sales_rep_id": str(profile.assigned_sales_rep_id) if profile.assigned_sales_rep_id else None,
        "sales_team": profile.sales_team,
    }
