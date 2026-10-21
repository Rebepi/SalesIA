from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.ayuda as service_ayuda
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/help/contextual")
def get_contextual_help(
    screen: Optional[str] = None,
    error_code: Optional[str] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_ayuda.get_contextual_help(screen=screen, error_code=error_code, current_user=current_user, db=db)
