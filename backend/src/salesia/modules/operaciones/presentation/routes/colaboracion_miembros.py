from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.colaboracion_miembros as service_colaboracion_miembros
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/collaboration/members")
def collaboration_members(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):

    return service_colaboracion_miembros.collaboration_members(current_user=current_user, db=db)
