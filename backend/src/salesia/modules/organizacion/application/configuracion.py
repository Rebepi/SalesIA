import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.organizacion.application.auxiliares.default_settings_dict import default_settings_dict
from salesia.modules.organizacion.application.contracts.configuracion import SettingsUpdateModel
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import AuditLogModel, CompanyModel
from salesia.shared.infrastructure.transactions import CompanySettings


def get_settings(current_user: AuthenticatedUser, db: Session):
    row = db.get(CompanySettings, current_user.company_id)
    defaults = default_settings_dict()
    saved = json.loads(row.values_json) if row and row.values_json else {}
    merged = {**defaults, **saved}
    return {"company_id": current_user.company_id, "version": row.version if row else 0, **merged}


def update_settings(req: SettingsUpdateModel, current_user: AuthenticatedUser, db: Session):
    db.scalar(select(CompanyModel).where(CompanyModel.id == current_user.company_id).with_for_update())
    row = db.get(CompanySettings, current_user.company_id)
    current_version = row.version if row else 0
    if current_version != req.version:
        raise HTTPException(409, "La configuración cambió; recargue antes de guardar.")

    raw_updates = req.model_dump(mode="json", exclude={"version"}, exclude_none=True, exclude_unset=True)
    if req.default_tax_rate is not None:
        raw_updates["default_tax_rate"] = str(req.default_tax_rate)

    current_values = default_settings_dict()
    if row and row.values_json:
        current_values.update(json.loads(row.values_json))
    for protected_key in ("closed_until", "closed_periods"):
        if protected_key in raw_updates and raw_updates[protected_key] != current_values.get(protected_key):
            raise HTTPException(422, "Los cierres de período se modifican desde su flujo de cierre y reapertura con motivo documentado.")
    if "commission_policy" in raw_updates:
        previous = current_values.get("commission_policy", {})
        proposed = raw_updates["commission_policy"]
        from salesia.modules.ventas.application.politicas_comision import archive_policy
        from salesia.modules.organizacion.application.contracts.politicas import CommissionPolicy
        archive_policy(db, current_user, previous, "Adopción de configuración de comisiones")
        proposed = {**previous, **proposed, "version": int(previous.get("version", 0)) + 1}
        raw_updates["commission_policy"] = CommissionPolicy.model_validate(proposed).model_dump(mode="json")
        archive_policy(db, current_user, raw_updates["commission_policy"], "Actualización desde configuración de empresa")
    current_values.update(raw_updates)

    if row:
        row.version += 1
        row.values_json = json.dumps(current_values)
    else:
        row = CompanySettings(company_id=current_user.company_id, version=1, values_json=json.dumps(current_values))
        db.add(row)

    db.add(
        AuditLogModel(
            id=uuid4(),
            company_id=current_user.company_id,
            actor_id=current_user.user_id,
            actor_email=current_user.email,
            action="SETTINGS_UPDATED",
            entity_type="CompanySettings",
            entity_id=current_user.company_id,
            trace_id=uuid4().hex,
            payload_diff=json.dumps(raw_updates),
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()
    return {"company_id": current_user.company_id, "version": row.version, **current_values}
