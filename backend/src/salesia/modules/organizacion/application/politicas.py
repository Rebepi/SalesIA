import json

from salesia.modules.organizacion.application.auxiliares.default_settings_dict import default_settings_dict
from salesia.shared.infrastructure.transactions import CompanySettings


def effective_policy(db, company_id, name):
    defaults = default_settings_dict().get(name, {})
    row = db.get(CompanySettings, company_id)
    saved = json.loads(row.values_json or "{}") if row else {}
    return {**defaults, **saved.get(name, {})}
