from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.operacion_integridad as service_operacion_integridad
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/operations/business-invariants")
def check_business_invariants(
    current_user: AuthenticatedUser = Depends(require_permission("audit:logs:read")), db: Session = Depends(get_db)
):

    return service_operacion_integridad.check_business_invariants(current_user=current_user, db=db)
