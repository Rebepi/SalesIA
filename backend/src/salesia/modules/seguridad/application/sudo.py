from datetime import timedelta

from sqlalchemy.orm import Session

from salesia.modules.seguridad.application.contracts.mfa import SudoVerifyRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.infrastructure.models import AuthSession
from salesia.modules.seguridad.infrastructure.security import verify_password
from salesia.modules.seguridad.infrastructure.sessions import consume_factor, utcnow
from salesia.shared.infrastructure.errors import DomainUnauthorizedException
from salesia.shared.infrastructure.models import UserModel


def verify_sudo_mode(req: SudoVerifyRequest, current_user: AuthenticatedUser, db: Session):
    user = db.get(UserModel, current_user.user_id)
    valid = verify_password(req.password, user.hashed_password)
    if valid and user.mfa_enabled:
        valid = consume_factor(db, user, req.mfa_code or "")
    if not valid:
        raise DomainUnauthorizedException("Credencial o segundo factor incorrectos.")
    session = db.get(AuthSession, current_user.session_id)
    session.sudo_until = utcnow() + timedelta(minutes=15)
    db.commit()
    return {"sudo_mode_active": True, "expires_in_seconds": 900, "session_id": session.id}
