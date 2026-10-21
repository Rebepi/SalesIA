from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.seguridad.application.sudo as service_sudo
from salesia.modules.seguridad.application.contracts.mfa import SudoVerifyRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/auth/sudo/verify")
def verify_sudo_mode(
    req: SudoVerifyRequest, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service_sudo.verify_sudo_mode(req=req, current_user=current_user, db=db)
