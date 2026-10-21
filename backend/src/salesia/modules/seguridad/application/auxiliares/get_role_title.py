from sqlalchemy import select

from salesia.modules.seguridad.domain.roles import get_role_catalog
from salesia.modules.seguridad.infrastructure.models import CustomRole


def get_role_title(db, company_id, role_key):
    for role in get_role_catalog():
        if role.role.value == role_key:
            return role.title
    custom = db.scalar(select(CustomRole).where(CustomRole.company_id == company_id, CustomRole.role_key == role_key))
    return custom.title if custom else role_key
