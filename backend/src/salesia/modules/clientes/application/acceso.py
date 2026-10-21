from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def user_can_read_sensitive(user: AuthenticatedUser) -> bool:
    if user.role in ("company_admin", "manager", "platform_admin"):
        return True
    return "customers:sensitive:read" in user.permissions
