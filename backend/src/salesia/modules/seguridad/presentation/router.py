from fastapi import APIRouter

from salesia.modules.seguridad.application.auxiliares.build_auth_mail_payload import (
    build_auth_mail_payload as build_auth_mail_payload,
)
from salesia.modules.seguridad.application.auxiliares.ensure_role_delegable import (
    ensure_role_delegable as ensure_role_delegable,
)
from salesia.modules.seguridad.application.auxiliares.get_role_permissions import (
    get_role_permissions as get_role_permissions,
)
from salesia.modules.seguridad.application.auxiliares.get_role_title import get_role_title as get_role_title
from salesia.modules.seguridad.application.auxiliares.mail_challenge import mail_challenge as mail_challenge
from salesia.modules.seguridad.application.auxiliares.role_exists import role_exists as role_exists
from salesia.modules.seguridad.application.auxiliares.role_title_exists import role_title_exists as role_title_exists
from salesia.modules.seguridad.application.contracts.autenticacion import LoginRequest as LoginRequest
from salesia.modules.seguridad.application.contracts.autenticacion import LoginResponse as LoginResponse
from salesia.modules.seguridad.application.contracts.autenticacion import RefreshTokenRequest as RefreshTokenRequest
from salesia.modules.seguridad.application.contracts.contrasenas import (
    PasswordResetConfirmModel as PasswordResetConfirmModel,
)
from salesia.modules.seguridad.application.contracts.email import EmailChangeRequest as EmailChangeRequest
from salesia.modules.seguridad.application.contracts.membresias import InvitationRequest as InvitationRequest
from salesia.modules.seguridad.application.contracts.membresias import MembershipUpdateModel as MembershipUpdateModel
from salesia.modules.seguridad.application.contracts.mfa import MfaVerifyRequest as MfaVerifyRequest
from salesia.modules.seguridad.application.contracts.mfa import SudoVerifyRequest as SudoVerifyRequest
from salesia.modules.seguridad.application.contracts.mfa_status import (
    PasswordResetRequestModel as PasswordResetRequestModel,
)
from salesia.modules.seguridad.application.contracts.perfil import ProfileUpdateRequest as ProfileUpdateRequest
from salesia.modules.seguridad.application.contracts.roles import RoleCloneModel as RoleCloneModel
from salesia.modules.seguridad.application.contracts.roles import RoleCreateModel as RoleCreateModel
from salesia.modules.seguridad.application.contracts.roles import RoleUpdateModel as RoleUpdateModel
from salesia.modules.seguridad.application.contracts.soporte import (
    SupportGrantCreateRequest as SupportGrantCreateRequest,
)
from salesia.modules.seguridad.application.contracts.sso import SsoLoginRequest as SsoLoginRequest
from salesia.modules.seguridad.presentation.routes import (
    autenticacion,
    contrasenas,
    email,
    membresias,
    mfa,
    mfa_status,
    perfil,
    roles,
    sesiones,
    soporte,
    sso,
    sudo,
    usuarios,
)

router = APIRouter(tags=["Identidad, Autenticación y Miembros"])
router.include_router(autenticacion.router)
router.include_router(mfa_status.router)
router.include_router(perfil.router)
router.include_router(contrasenas.router)
router.include_router(sesiones.router)
router.include_router(membresias.router)
router.include_router(usuarios.router)
router.include_router(roles.router)
router.include_router(soporte.router)
router.include_router(mfa.router)
router.include_router(sudo.router)
router.include_router(sso.router)
router.include_router(email.router)

_router_order = {
    name: index
    for index, name in enumerate(
        (
            "login",
            "get_mfa_status",
            "check_mfa_status",
            "refresh_tokens",
            "logout",
            "get_me",
            "get_profile",
            "update_profile",
            "request_password_reset",
            "confirm_password_reset",
            "list_sessions",
            "revoke_session",
            "invite_member",
            "resend_invitation",
            "cancel_invitation",
            "list_users",
            "update_membership",
            "transfer_admin",
            "list_roles",
            "compare_roles",
            "clone_role",
            "create_custom_role",
            "custom_role_impact",
            "update_custom_role",
            "delete_custom_role",
            "member_security",
            "create_support_grant",
            "list_support_grants",
            "revoke_support_grant",
            "setup_mfa",
            "verify_mfa",
            "regenerate_mfa_recovery_codes",
            "verify_sudo_mode",
            "sso_callback",
            "request_email_change",
        )
    )
}
router.routes.sort(key=lambda route: _router_order[route.name])
login = autenticacion.login
get_mfa_status = mfa_status.get_mfa_status
check_mfa_status = mfa_status.check_mfa_status
refresh_tokens = autenticacion.refresh_tokens
logout = autenticacion.logout
get_me = perfil.get_me
get_profile = perfil.get_profile
update_profile = perfil.update_profile
request_password_reset = contrasenas.request_password_reset
confirm_password_reset = contrasenas.confirm_password_reset
list_sessions = sesiones.list_sessions
revoke_session = sesiones.revoke_session
invite_member = membresias.invite_member
resend_invitation = membresias.resend_invitation
cancel_invitation = membresias.cancel_invitation
list_users = usuarios.list_users
update_membership = membresias.update_membership
transfer_admin = membresias.transfer_admin
list_roles = roles.list_roles
compare_roles = roles.compare_roles
clone_role = roles.clone_role
create_custom_role = roles.create_custom_role
custom_role_impact = roles.custom_role_impact
update_custom_role = roles.update_custom_role
delete_custom_role = roles.delete_custom_role
member_security = usuarios.member_security
create_support_grant = soporte.create_support_grant
list_support_grants = soporte.list_support_grants
revoke_support_grant = soporte.revoke_support_grant
setup_mfa = mfa.setup_mfa
verify_mfa = mfa.verify_mfa
regenerate_mfa_recovery_codes = mfa.regenerate_mfa_recovery_codes
verify_sudo_mode = sudo.verify_sudo_mode
sso_callback = sso.sso_callback
request_email_change = email.request_email_change

from salesia.modules.seguridad.presentation.routes.traspaso_usuario import router as user_handover_router

router.include_router(user_handover_router)

from salesia.modules.seguridad.presentation.routes.separacion_funciones import router as function_separation_router

router.include_router(function_separation_router)

from salesia.modules.seguridad.presentation.routes.acceso_efectivo import router as effective_access_router

router.include_router(effective_access_router)
