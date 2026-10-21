from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.operacion_respaldos as service_operacion_respaldos
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/operations/backup/trigger", status_code=202)
def trigger_backup(
    current_user: AuthenticatedUser = Depends(require_permission("platform:manage")),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128),
):

    return service_operacion_respaldos.trigger_backup(current_user=current_user, db=db, idempotency_key=idempotency_key)


@router.get("/operations/backup/status")
def get_backup_status(
    current_user: AuthenticatedUser = Depends(require_permission("platform:manage")), db: Session = Depends(get_db)
):

    return service_operacion_respaldos.get_backup_status(current_user=current_user, db=db)
