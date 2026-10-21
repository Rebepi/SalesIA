from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.seguridad.application.perfil as service_perfil
from salesia.modules.seguridad.application.contracts.perfil import ProfileUpdateRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/auth/me")
def get_me(current_user: AuthenticatedUser = Depends(get_current_user)):
    return service_perfil.get_me(current_user=current_user)


@router.get("/auth/profile")
def get_profile(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return service_perfil.get_profile(current_user=current_user, db=db)


@router.patch("/auth/profile")
def update_profile(
    payload: ProfileUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service_perfil.update_profile(payload=payload, current_user=current_user, db=db)