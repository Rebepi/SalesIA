from sqlalchemy import func, select

from salesia.modules.seguridad.domain.roles import get_role_catalog
from salesia.modules.seguridad.infrastructure.models import CustomRole


def role_title_exists(db, company_id, title):
    normalized = title.strip().casefold()
    if any(role.title.strip().casefold() == normalized for role in get_role_catalog()):
        return True
    return (
        db.scalar(
            select(CustomRole.id).where(
                CustomRole.company_id == company_id, func.lower(func.btrim(CustomRole.title)) == title.strip().lower()
            )
        )
        is not None
    )
