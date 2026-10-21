from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from salesia.modules.clientes.application import condiciones as service
from salesia.modules.clientes.application.contracts.comercial import CreditCheckRequest, CustomerCommercialTermsModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/customers")


@router.get("/{customer_id}/commercial-terms")
def get_customer_commercial_terms(
    customer_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service.get_customer_commercial_terms(customer_id=customer_id, current_user=current_user, db=db)


@router.patch("/{customer_id}/commercial-terms")
def update_customer_commercial_terms(
    customer_id: UUID,
    req: CustomerCommercialTermsModel,
    current_user: AuthenticatedUser = Depends(require_permission("customers:write")),
    db: Session = Depends(get_db),
):
    return service.update_customer_commercial_terms(customer_id=customer_id, req=req, current_user=current_user, db=db)


@router.post("/{customer_id}/credit-check")
def check_customer_credit(
    customer_id: UUID,
    req: CreditCheckRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service.check_customer_credit(customer_id=customer_id, req=req, current_user=current_user, db=db)
