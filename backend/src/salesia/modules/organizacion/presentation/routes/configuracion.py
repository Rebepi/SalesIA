from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.organizacion.application.configuracion as service_configuracion
from salesia.modules.organizacion.application.contracts.configuracion import SettingsUpdateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/settings")
@router.get("/companies/current/settings")
def get_settings(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return service_configuracion.get_settings(current_user=current_user, db=db)


@router.patch("/settings")
@router.patch("/companies/current/settings")
def update_settings(
    req: SettingsUpdateModel,
    current_user: AuthenticatedUser = Depends(require_permission("organization:manage")),
    db: Session = Depends(get_db),
):
    return service_configuracion.update_settings(req=req, current_user=current_user, db=db)
