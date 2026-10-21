from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.auditoria.application.auditoria_integridad as service_auditoria_integridad
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/audit/logs/verify", operation_id="verify_audit_logs_integrity")
@router.get("/audit-logs/verify", operation_id="verify_audit_logs_integrity_alias", deprecated=True)
def verify_logs_integrity(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return service_auditoria_integridad.verify_logs_integrity(current_user=current_user, db=db)
