import json

from sqlalchemy import select

from salesia.modules.operaciones.application.auxiliares.now import now
from salesia.modules.operaciones.infrastructure_models import OperationSetting


def replace_setting(db, company_id, key, value):

    row = db.scalar(
        select(OperationSetting)
        .where(OperationSetting.company_id == company_id, OperationSetting.key == key)
        .with_for_update()
    )

    if row:
        row.value_json = json.dumps(value)

        row.version += 1

        row.updated_at = now()

    else:
        row = OperationSetting(
            company_id=company_id, key=key, value_json=json.dumps(value), version=1, updated_at=now()
        )

        db.add(row)

    return row
