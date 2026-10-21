from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from salesia.modules.clientes.application import oportunidades as service
from salesia.modules.clientes.application.contracts.crm import (
    CustomerOpportunityCreateModel,
    CustomerOpportunityUpdateModel,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

crm_router = APIRouter(prefix="/crm")

router = APIRouter(prefix="/customers")


@router.get("/{customer_id}/opportunities")
def list_customer_opportunities(
    customer_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service.list_customer_opportunities(customer_id=customer_id, current_user=current_user, db=db)


@router.post("/{customer_id}/opportunities", status_code=status.HTTP_201_CREATED)
def create_customer_opportunity(
    customer_id: UUID,
    req: CustomerOpportunityCreateModel,
    current_user: AuthenticatedUser = Depends(require_permission("customers:write")),
    db: Session = Depends(get_db),
):
    return service.create_customer_opportunity(customer_id=customer_id, req=req, current_user=current_user, db=db)


@crm_router.get("/opportunities")
def list_all_crm_opportunities(
    stage: Optional[str] = Query(None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.list_all_crm_opportunities(stage=stage, current_user=current_user, db=db)


@crm_router.patch("/opportunities/{opportunity_id}")
def update_crm_opportunity(
    opportunity_id: UUID,
    req: CustomerOpportunityUpdateModel,
    current_user: AuthenticatedUser = Depends(require_permission("customers:write")),
    db: Session = Depends(get_db),
):
    return service.update_crm_opportunity(opportunity_id=opportunity_id, req=req, current_user=current_user, db=db)


@crm_router.post("/opportunities/{opportunity_id}/convert-to-quote")
def convert_opportunity_to_quote(
    opportunity_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("quotations:write")),
    db: Session = Depends(get_db),
):
    return service.convert_opportunity_to_quote(opportunity_id=opportunity_id, current_user=current_user, db=db)
