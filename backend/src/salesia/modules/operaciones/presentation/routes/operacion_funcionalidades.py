from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.operacion_funcionalidades as service_operacion_funcionalidades
from salesia.modules.operaciones.application.contracts.operacion_funcionalidades import FeatureToggleRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/operations/feature-flags")
def get_feature_flags(
    current_user: AuthenticatedUser = Depends(require_permission("operations:manage")), db: Session = Depends(get_db)
):

    return service_operacion_funcionalidades.get_feature_flags(current_user=current_user, db=db)


@router.post("/operations/feature-flags/toggle")
def toggle_feature_flag(
    payload: FeatureToggleRequest,
    current_user: AuthenticatedUser = Depends(require_permission("operations:manage")),
    db: Session = Depends(get_db),
):

    return service_operacion_funcionalidades.toggle_feature_flag(payload=payload, current_user=current_user, db=db)
