from sqlalchemy import select

from salesia.modules.seguridad.domain.roles import get_role_catalog
from salesia.modules.seguridad.infrastructure.models import CustomRole


def role_exists(db, company_id, role):
    if role == "platform_admin":
        return False
    return (
        any(r.role.value == role for r in get_role_catalog())
        or db.scalar(select(CustomRole.id).where(CustomRole.company_id == company_id, CustomRole.role_key == role))
        is not None
    )
