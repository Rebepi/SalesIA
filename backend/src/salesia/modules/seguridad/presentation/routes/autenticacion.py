from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

import salesia.modules.seguridad.application.autenticacion as service_autenticacion
from salesia.modules.seguridad.application.contracts.autenticacion import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/auth/login", response_model=LoginResponse)
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    return service_autenticacion.login(req=req, request=request, db=db)


@router.post("/auth/refresh", response_model=LoginResponse)
def refresh_tokens(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    return service_autenticacion.refresh_tokens(req=req, db=db)


@router.post("/auth/logout")
def logout(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return service_autenticacion.logout(current_user=current_user, db=db)