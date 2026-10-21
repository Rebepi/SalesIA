import secrets
from datetime import timedelta

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from salesia.modules.seguridad.application.contracts.email import EmailChangeRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.infrastructure.models import AuthChallenge, AuthMail, AuthSession
from salesia.modules.seguridad.infrastructure.sessions import aware, cipher, fingerprint, utcnow
from salesia.shared.infrastructure.errors import DomainConflictException, DomainUnauthorizedException
from salesia.shared.infrastructure.models import UserModel


def request_email_change(req: EmailChangeRequest, current_user: AuthenticatedUser, db: Session):
    session = db.get(AuthSession, current_user.session_id)
    if not session or not session.sudo_until or aware(session.sudo_until) <= utcnow():
        raise DomainUnauthorizedException(
            "Se requiere reautenticación (modo sudo) reciente para cambiar el correo electrónico."
        )
    new_email_clean = str(req.new_email).lower()
    existing = db.scalar(select(UserModel.id).where(func.lower(UserModel.email) == new_email_clean))
    if existing:
        raise DomainConflictException("El correo especificado ya se encuentra en uso.")
    token = secrets.token_urlsafe(48)
    db.execute(
        update(AuthChallenge)
        .where(
            AuthChallenge.user_id == current_user.user_id,
            AuthChallenge.purpose == "email_change",
            AuthChallenge.used_at.is_(None),
        )
        .values(used_at=utcnow())
    )
    challenge = AuthChallenge(
        user_id=current_user.user_id,
        token_hash=fingerprint(f"{new_email_clean}:{token}"),
        purpose="email_change",
        expires_at=utcnow() + timedelta(hours=1),
    )
    db.add(challenge)
    notice = f"Se ha solicitado cambiar el correo principal de tu cuenta a {new_email_clean}. Si no fuiste tú, revoca tus sesiones de inmediato."
    db.add(
        AuthMail(
            recipient=current_user.email,
            encrypted_body=cipher().encrypt(notice.encode()).decode(),
            subject="SalesIA: Alerta de cambio de correo",
            created_at=utcnow(),
        )
    )
    db.commit()
    return {
        "status": "pending_verification",
        "target_email": new_email_clean,
        "notice": "Verificación iniciada con notificación de seguridad al correo anterior.",
    }
