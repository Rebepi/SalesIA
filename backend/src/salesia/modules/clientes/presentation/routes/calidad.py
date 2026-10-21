from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from salesia.modules.clientes.application import calidad as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/customers")


@router.get("/{customer_id}/quality")
def get_customer_quality(
    customer_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service.get_customer_quality(customer_id=customer_id, current_user=current_user, db=db)
