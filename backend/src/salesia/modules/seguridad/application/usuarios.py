from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.domain.roles import get_role_catalog
from salesia.modules.seguridad.infrastructure.models import AuthChallenge, AuthSession, CustomRole
from salesia.modules.seguridad.infrastructure.sessions import aware, utcnow
from salesia.shared.infrastructure.models import UserModel


def list_users(page: int, page_size: int, current_user: AuthenticatedUser, db: Session):
    total = db.scalar(
        select(func.count()).select_from(UserModel).where(UserModel.company_id == current_user.company_id)
    )
    offset = (page - 1) * page_size
    rows = db.scalars(
        select(UserModel).where(UserModel.company_id == current_user.company_id).offset(offset).limit(page_size)
    ).all()
    role_names = {role.role.value: role.title for role in get_role_catalog()}
    role_names.update(
        {
            role.role_key: role.title
            for role in db.scalars(select(CustomRole).where(CustomRole.company_id == current_user.company_id)).all()
        }
    )
    pending_invitations = set(
        db.scalars(
            select(AuthChallenge.user_id).where(AuthChallenge.purpose == "invitation", AuthChallenge.used_at.is_(None))
        ).all()
    )
    items = [
        {
            "user_id": u.id,
            "full_name": u.full_name or "",
            "email": u.email,
            "role": u.role,
            "role_name": role_names.get(u.role, u.role),
            "company_id": u.company_id,
            "is_active": u.is_active,
            "status": "active" if u.is_active else "invited" if u.id in pending_invitations else "suspended",
        }
        for u in rows
    ]
    return {"items": items, "total_count": total, "page": page, "page_size": page_size}


def member_security(user_id: UUID, current_user: AuthenticatedUser, db: Session):
    user = db.scalar(select(UserModel).where(UserModel.id == user_id, UserModel.company_id == current_user.company_id))
    if not user:
        raise HTTPException(404, "Usuario no encontrado.")
    sessions = db.scalars(
        select(AuthSession).where(AuthSession.user_id == user.id, AuthSession.company_id == current_user.company_id)
    ).all()
    active = [session for session in sessions if not session.revoked_at and aware(session.expires_at) > utcnow()]
    invitation = db.scalar(
        select(AuthChallenge).where(
            AuthChallenge.user_id == user.id,
            AuthChallenge.purpose == "invitation",
            AuthChallenge.used_at.is_(None),
            AuthChallenge.expires_at > utcnow(),
        )
    )
    last = max((aware(session.created_at) for session in sessions), default=None)
    return {
        "mfa_enabled": user.mfa_enabled,
        "last_access": last.isoformat() if last else None,
        "active_sessions": len(active),
        "invitation_pending": invitation is not None,
        "credentials_configured": bool(user.hashed_password) and user.is_active,
    }
