from fastapi import HTTPException
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application.auxiliares.now import now
from salesia.modules.operaciones.application.auxiliares.replace_setting import replace_setting
from salesia.modules.operaciones.application.contracts.operacion_mantenimiento import OperationalModeRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def set_degraded_mode(payload: OperationalModeRequest, current_user: AuthenticatedUser, db: Session):
    if payload.active and not payload.reason:
        raise HTTPException(422, "Debe indicar el motivo de la degradación.")

    value = {
        "active": payload.active,
        "reason": payload.reason,
        "updated_by": str(current_user.user_id),
        "updated_at": now().isoformat(),
    }

    row = replace_setting(db, current_user.company_id, "degraded_mode", value)

    db.commit()

    return {**value, "version": row.version}
