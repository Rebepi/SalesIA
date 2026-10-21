from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from salesia.modules.clientes.application import actividades as service
from salesia.modules.clientes.application.contracts.crm import CustomerActivityCreateModel, CustomerActivityUpdateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

crm_router = APIRouter(prefix="/crm")

router = APIRouter(prefix="/customers")


@router.get("/{customer_id}/activities")
def list_customer_activities(
    customer_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service.list_customer_activities(customer_id=customer_id, current_user=current_user, db=db)


@router.post("/{customer_id}/activities", status_code=status.HTTP_201_CREATED)
def create_customer_activity(
    customer_id: UUID,
    req: CustomerActivityCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("customers:write")),
    db: Session = Depends(get_db),
):
    return service.create_customer_activity(customer_id=customer_id, req=req, current_user=current_user, db=db)


@crm_router.get("/activities")
def list_crm_activities(
    view_mode: str = Query("list", pattern="^(list|calendar)$"),
    status: Optional[str] = Query(None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.list_crm_activities(view_mode=view_mode, status=status, current_user=current_user, db=db)


@crm_router.patch("/activities/{activity_id}")
def update_crm_activity(
    activity_id: UUID,
    req: CustomerActivityUpdateModel,
    current_user: AuthenticatedUser = Depends(require_permission("customers:write")),
    db: Session = Depends(get_db),
):
    return service.update_crm_activity(activity_id=activity_id, req=req, current_user=current_user, db=db)
