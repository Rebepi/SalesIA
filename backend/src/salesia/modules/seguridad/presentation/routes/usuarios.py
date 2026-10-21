from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import salesia.modules.seguridad.application.usuarios as service_usuarios
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
):
    return service_usuarios.list_users(page=page, page_size=page_size, current_user=current_user, db=db)


@router.get("/users/{user_id}/security")
def member_security(
    user_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
):
    return service_usuarios.member_security(user_id=user_id, current_user=current_user, db=db)
