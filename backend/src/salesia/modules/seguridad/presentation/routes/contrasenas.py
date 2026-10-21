from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.seguridad.application.contrasenas as service_contrasenas
from salesia.modules.seguridad.application.contracts.contrasenas import PasswordResetConfirmModel
from salesia.modules.seguridad.application.contracts.mfa_status import PasswordResetRequestModel
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/auth/password/reset-request", status_code=202)
def request_password_reset(req: PasswordResetRequestModel, db: Session = Depends(get_db)):
    return service_contrasenas.request_password_reset(req=req, db=db)


@router.post("/auth/password/reset")
def confirm_password_reset(req: PasswordResetConfirmModel, db: Session = Depends(get_db)):
    return service_contrasenas.confirm_password_reset(req=req, db=db)