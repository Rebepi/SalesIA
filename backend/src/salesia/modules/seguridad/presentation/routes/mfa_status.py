from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import salesia.modules.seguridad.application.mfa_status as service_mfa_status
from salesia.modules.seguridad.application.contracts.mfa_status import PasswordResetRequestModel
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/auth/mfa-status")
def get_mfa_status(email: str = Query(default=""), db: Session = Depends(get_db)):
    return service_mfa_status.get_mfa_status(email=email, db=db)


@router.post("/auth/mfa-status")
def check_mfa_status(req: PasswordResetRequestModel, db: Session = Depends(get_db)):
    return service_mfa_status.check_mfa_status(req=req, db=db)