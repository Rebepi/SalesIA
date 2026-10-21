from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from salesia.modules.clientes.application import asignaciones as service
from salesia.modules.clientes.application.contracts.comercial import CustomerAssignmentModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/customers")


@router.get("/{customer_id}/assignment")
def get_customer_assignment(
    customer_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service.get_customer_assignment(customer_id=customer_id, current_user=current_user, db=db)


@router.post("/{customer_id}/assignment")
def update_customer_assignment(
    customer_id: UUID,
    req: CustomerAssignmentModel,
    current_user: AuthenticatedUser = Depends(require_permission("customers:write")),
    db: Session = Depends(get_db),
):
    return service.update_customer_assignment(customer_id=customer_id, req=req, current_user=current_user, db=db)
