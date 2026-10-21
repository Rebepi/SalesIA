from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from salesia.modules.clientes.application import fidelizacion as service
from salesia.modules.clientes.application.contracts.fidelizacion import LoyaltyAccrualModel, LoyaltyReversalModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/customers")


@router.get("/{customer_id}/loyalty")
def get_customer_loyalty(
    customer_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service.get_customer_loyalty(customer_id=customer_id, current_user=current_user, db=db)


@router.post("/{customer_id}/loyalty/accrue", status_code=status.HTTP_201_CREATED)
def accrue_loyalty_points(
    customer_id: UUID,
    req: LoyaltyAccrualModel,
    current_user: AuthenticatedUser = Depends(require_permission("customers:write")),
    db: Session = Depends(get_db),
):
    return service.accrue_loyalty_points(customer_id=customer_id, req=req, current_user=current_user, db=db)


@router.post("/{customer_id}/loyalty/reverse")
def reverse_loyalty_points(
    customer_id: UUID,
    req: LoyaltyReversalModel,
    current_user: AuthenticatedUser = Depends(require_permission("customers:write")),
    db: Session = Depends(get_db),
):
    return service.reverse_loyalty_points(customer_id=customer_id, req=req, current_user=current_user, db=db)
