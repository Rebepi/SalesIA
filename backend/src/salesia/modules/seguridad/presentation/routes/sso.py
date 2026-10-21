from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

import salesia.modules.seguridad.application.sso as service_sso
from salesia.modules.seguridad.application.contracts.autenticacion import LoginResponse
from salesia.modules.seguridad.application.contracts.sso import SsoLoginRequest
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/auth/sso/callback", response_model=LoginResponse)
def sso_callback(req: SsoLoginRequest, request: Request, db: Session = Depends(get_db)):
    return service_sso.sso_callback(req=req, request=request, db=db)
