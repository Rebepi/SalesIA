from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.finanzas.application.disputas as service_disputas
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/finance/disputes")
def list_payment_disputes(
    current_user: AuthenticatedUser = Depends(require_permission("payments:read")), db: Session = Depends(get_db)
):

    return service_disputas.list_payment_disputes(current_user=current_user, db=db)
