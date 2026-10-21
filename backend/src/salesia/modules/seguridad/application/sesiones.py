from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.infrastructure.models import AuthSession
from salesia.modules.seguridad.infrastructure.sessions import utcnow
from salesia.shared.infrastructure.errors import DomainNotFoundException


def list_sessions(current_user: AuthenticatedUser, db: Session):
    rows = db.scalars(
        select(AuthSession)
        .where(
            AuthSession.user_id == current_user.user_id,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > utcnow(),
        )
        .order_by(AuthSession.created_at.desc())
    ).all()
    return [
        {
            "session_id": s.id,
            "user_agent": s.user_agent,
            "ip_address": s.ip_address,
            "created_at": s.created_at,
            "is_current": s.id == current_user.session_id,
        }
        for s in rows
    ]


def revoke_session(session_id: UUID, current_user: AuthenticatedUser, db: Session):
    session = db.scalar(
        select(AuthSession).where(AuthSession.id == session_id, AuthSession.user_id == current_user.user_id)
    )
    if not session:
        raise DomainNotFoundException("Sesión no encontrada.")
    session.revoked_at = utcnow()
    session.sudo_until = None
    db.commit()
    return {"status": "revoked", "session_id": session_id}
