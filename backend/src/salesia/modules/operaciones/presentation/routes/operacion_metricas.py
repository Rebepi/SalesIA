from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.operacion_metricas as service_operacion_metricas
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/operations/metrics")
def get_operational_metrics(
    current_user: AuthenticatedUser = Depends(require_permission("operations:manage")), db: Session = Depends(get_db)
):

    return service_operacion_metricas.get_operational_metrics(current_user=current_user, db=db)
