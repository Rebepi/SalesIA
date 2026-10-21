from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from salesia.modules.seguridad.application.auxiliares.mail_challenge import mail_challenge
from salesia.modules.seguridad.application.configuracion import COMMON_PASSWORDS
from salesia.modules.seguridad.application.contracts.contrasenas import PasswordResetConfirmModel
from salesia.modules.seguridad.application.contracts.mfa_status import PasswordResetRequestModel
from salesia.modules.seguridad.infrastructure.models import AuthChallenge
from salesia.modules.seguridad.infrastructure.security import hash_password
from salesia.modules.seguridad.infrastructure.sessions import aware, fingerprint, revoke_user_sessions, utcnow
from salesia.shared.infrastructure.errors import DomainUnauthorizedException
from salesia.shared.infrastructure.models import UserModel


def request_password_reset(req: PasswordResetRequestModel, db: Session):
    user = db.scalar(
        select(UserModel).where(func.lower(UserModel.email) == str(req.email).lower(), UserModel.is_active.is_(True))
    )
    if user:
        mail_challenge(db, user, "reset")
        db.commit()
    return {"status": "received", "detail": "Si la cuenta está registrada, recibirá instrucciones."}


def confirm_password_reset(req: PasswordResetConfirmModel, db: Session):
    challenge = db.scalar(select(AuthChallenge).where(AuthChallenge.token_hash == fingerprint(req.reset_token)))
    if not challenge or challenge.used_at or aware(challenge.expires_at) <= utcnow():
        raise DomainUnauthorizedException("Token inválido o expirado.")
    changed = db.execute(
        update(AuthChallenge)
        .where(AuthChallenge.id == challenge.id, AuthChallenge.used_at.is_(None), AuthChallenge.expires_at > utcnow())
        .values(used_at=utcnow())
        .execution_options(synchronize_session=False)
    )
    if changed.rowcount != 1:
        raise DomainUnauthorizedException("Token ya utilizado.")
    if req.new_password.lower() in COMMON_PASSWORDS:
        raise DomainUnauthorizedException("La contraseña especificada es vulnerable o demasiado común.")
    user = db.get(UserModel, challenge.user_id)
    user.hashed_password = hash_password(req.new_password)
    if challenge.purpose == "invitation":
        user.is_active = True
    revoke_user_sessions(db, user.id)
    db.commit()
    return {"status": "success", "detail": "Contraseña actualizada. Inicie sesión nuevamente."}
