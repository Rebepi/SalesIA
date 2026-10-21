from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.seguridad.application.sesiones as service_sesiones
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/auth/sessions")
def list_sessions(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return service_sesiones.list_sessions(current_user=current_user, db=db)


@router.delete("/auth/sessions/{session_id}")
def revoke_session(
    session_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service_sesiones.revoke_session(session_id=session_id, current_user=current_user, db=db)