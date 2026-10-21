from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.seguridad.application.mfa as service_mfa
from salesia.modules.seguridad.application.contracts.mfa import MfaVerifyRequest, SudoVerifyRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/auth/mfa/setup")
def setup_mfa(
    req: SudoVerifyRequest, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service_mfa.setup_mfa(req=req, current_user=current_user, db=db)


@router.post("/auth/mfa/verify")
def verify_mfa(
    req: MfaVerifyRequest, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service_mfa.verify_mfa(req=req, current_user=current_user, db=db)


@router.post("/auth/mfa/recovery-codes/regenerate")
def regenerate_mfa_recovery_codes(
    current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service_mfa.regenerate_mfa_recovery_codes(current_user=current_user, db=db)
