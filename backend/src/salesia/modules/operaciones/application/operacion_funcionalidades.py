from fastapi import HTTPException
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application.auxiliares.replace_setting import replace_setting
from salesia.modules.operaciones.application.auxiliares.setting_value import setting_value
from salesia.modules.operaciones.application.contracts.operacion_funcionalidades import FeatureToggleRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def get_feature_flags(current_user: AuthenticatedUser, db: Session):
    defaults = {
        "ai_insights_engine": False,
        "mfa_mandatory_enforcement": False,
        "advanced_inventory": True,
        "payment_integrations": True,
    }

    stored = setting_value(db, current_user.company_id, "feature_flags", {})

    return {"flags": {**defaults, **stored}}


def toggle_feature_flag(payload: FeatureToggleRequest, current_user: AuthenticatedUser, db: Session):
    allowed = {"ai_insights_engine", "mfa_mandatory_enforcement", "advanced_inventory", "payment_integrations"}

    if payload.flag_key not in allowed:
        raise HTTPException(400, "La bandera solicitada no existe.")

    values = setting_value(db, current_user.company_id, "feature_flags", {})

    values[payload.flag_key] = payload.enabled

    row = replace_setting(db, current_user.company_id, "feature_flags", values)

    db.commit()

    return {"flag_key": payload.flag_key, "enabled": payload.enabled, "version": row.version}
