import json

from sqlalchemy import select

from salesia.modules.operaciones.infrastructure_models import OperationSetting


def setting_value(db, company_id, key, default):

    row = db.scalar(
        select(OperationSetting).where(OperationSetting.company_id == company_id, OperationSetting.key == key)
    )

    return json.loads(row.value_json) if row else default
