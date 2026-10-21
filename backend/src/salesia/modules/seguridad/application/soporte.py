import secrets
from datetime import timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.seguridad.application.contracts.soporte import SupportGrantCreateRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.infrastructure.models import SupportGrant
from salesia.modules.seguridad.infrastructure.sessions import fingerprint, utcnow
from salesia.shared.infrastructure.errors import DomainNotFoundException


def create_support_grant(req: SupportGrantCreateRequest, current_user: AuthenticatedUser, db: Session):
    token = secrets.token_urlsafe(48)
    grant_id = uuid4()
    now = utcnow()
    exp = now + timedelta(minutes=req.duration_minutes)
    grant = SupportGrant(
        id=grant_id,
        company_id=current_user.company_id,
        granted_by=current_user.user_id,
        reason=req.reason,
        scope=req.scope,
        token_hash=fingerprint(token),
        created_at=now,
        expires_at=exp,
        revoked_at=None,
    )
    db.add(grant)
    db.commit()
    return {
        "grant_id": str(grant.id),
        "token": token,
        "scope": grant.scope,
        "reason": grant.reason,
        "expires_at": grant.expires_at.isoformat(),
    }


def list_support_grants(current_user: AuthenticatedUser, db: Session):
    rows = db.scalars(
        select(SupportGrant)
        .where(SupportGrant.company_id == current_user.company_id)
        .order_by(SupportGrant.created_at.desc())
    ).all()
    items = [
        {
            "grant_id": str(g.id),
            "reason": g.reason,
            "scope": g.scope,
            "created_at": g.created_at.isoformat(),
            "expires_at": g.expires_at.isoformat(),
            "revoked_at": g.revoked_at.isoformat() if g.revoked_at else None,
        }
        for g in rows
    ]
    return {"items": items, "count": len(items)}


def revoke_support_grant(grant_id: UUID, current_user: AuthenticatedUser, db: Session):
    grant = db.scalar(
        select(SupportGrant).where(SupportGrant.id == grant_id, SupportGrant.company_id == current_user.company_id)
    )
    if not grant:
        raise DomainNotFoundException("Concesión de soporte no encontrada.")
    grant.revoked_at = utcnow()
    db.commit()
    return {"status": "revoked", "grant_id": str(grant.id)}
