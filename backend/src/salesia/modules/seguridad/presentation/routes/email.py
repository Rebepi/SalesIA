from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.seguridad.application.email as service_email
from salesia.modules.seguridad.application.contracts.email import EmailChangeRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/auth/email/change-request")
def request_email_change(
    req: EmailChangeRequest, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service_email.request_email_change(req=req, current_user=current_user, db=db)
