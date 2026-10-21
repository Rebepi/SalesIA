from fastapi import HTTPException

from salesia.modules.seguridad.application.auxiliares.get_role_permissions import get_role_permissions
from salesia.shared.infrastructure.errors import DomainForbiddenException


def ensure_role_delegable(db, current_user, role_key):
    permissions = get_role_permissions(db, current_user.company_id, role_key)
    if permissions is None:
        raise HTTPException(422, "Rol no permitido.")
    if role_key == "company_admin" and current_user.role != "company_admin":
        raise DomainForbiddenException("Solo un administrador de empresa puede delegar ese rol.")
    missing = set(permissions) - set(current_user.permissions)
    if missing:
        raise DomainForbiddenException("No puede delegar permisos que su cuenta no posee.")
