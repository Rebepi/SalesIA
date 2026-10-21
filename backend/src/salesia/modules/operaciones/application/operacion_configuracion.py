import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application.auxiliares.now import now
from salesia.modules.operaciones.application.contracts.operacion_configuracion import SettingRequest
from salesia.modules.operaciones.infrastructure_models import OperationSetting
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def get_operation_settings(current_user: AuthenticatedUser, db: Session):
    rows = db.scalars(
        select(OperationSetting)
        .where(OperationSetting.company_id == current_user.company_id)
        .order_by(OperationSetting.key)
    ).all()

    return {
        "items": [
            {
                "key": row.key,
                "value": json.loads(row.value_json),
                "version": row.version,
                "updated_at": row.updated_at.isoformat(),
            }
            for row in rows
        ]
    }


def set_operation_setting(payload: SettingRequest, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(OperationSetting)
        .where(OperationSetting.company_id == current_user.company_id, OperationSetting.key == payload.key)
        .with_for_update()
    )

    current_version = row.version if row else 0

    if payload.version != current_version:
        raise HTTPException(409, "La configuración cambió; recargue.")

    if row:
        row.value_json = json.dumps(payload.value)

        row.version += 1

        row.updated_at = now()

    else:
        row = OperationSetting(
            company_id=current_user.company_id,
            key=payload.key,
            value_json=json.dumps(payload.value),
            version=1,
            updated_at=now(),
        )

        db.add(row)

    db.commit()

    return {"key": row.key, "value": payload.value, "version": row.version, "updated_at": row.updated_at.isoformat()}
