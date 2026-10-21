import json

from sqlalchemy import select

from salesia.modules.seguridad.domain.roles import get_role_catalog
from salesia.modules.seguridad.infrastructure.models import CustomRole


def get_role_permissions(db, company_id, role_key):
    for r in get_role_catalog():
        if r.role.value == role_key:
            return sorted(list(r.permissions))
    custom = db.scalar(select(CustomRole).where(CustomRole.company_id == company_id, CustomRole.role_key == role_key))
    if custom:
        return sorted(json.loads(custom.permissions_json))
    return None
