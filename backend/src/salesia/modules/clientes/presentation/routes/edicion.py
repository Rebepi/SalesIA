from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from salesia.modules.clientes.application import edicion as service
from salesia.modules.clientes.application.contracts.clientes import CustomerUpdateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/customers")


@router.patch("/{customer_id}")
def update_customer(
    customer_id: UUID,
    req: CustomerUpdateModel,
    current_user: AuthenticatedUser = Depends(require_permission("customers:write")),
    db: Session = Depends(get_db),
):
    return service.update_customer(customer_id=customer_id, req=req, current_user=current_user, db=db)
