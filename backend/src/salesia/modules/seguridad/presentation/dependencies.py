from typing import Callable, Optional
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from salesia.modules.seguridad.domain.identidad import AuthenticatedUser as AuthenticatedUser
from salesia.modules.seguridad.domain.roles import Permission
from salesia.modules.seguridad.infrastructure.models import AuthSession, SupportGrant
from salesia.modules.seguridad.infrastructure.security import decode_token
from salesia.modules.seguridad.infrastructure.sessions import aware, fingerprint, permissions_for, utcnow
from salesia.shared.infrastructure.database import get_db
from salesia.shared.infrastructure.errors import DomainForbiddenException, DomainUnauthorizedException
from salesia.shared.infrastructure.models import CompanyModel, UserModel
from salesia.shared.infrastructure.tenant_scope import bind_company, current_company


async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"), db: Session = Depends(get_db)
) -> AuthenticatedUser:
    user = await run_in_threadpool(resolve_current_user, authorization, db)
    current_company.set(str(user.company_id))
    return user


def resolve_current_user(authorization: Optional[str], db: Session) -> AuthenticatedUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise DomainUnauthorizedException("Se requiere una sesión válida.")
    raw_token = authorization[7:]
    try:
        payload = decode_token(raw_token)
        if payload.get("type") != "access":
            raise ValueError("token type")
        session = db.get(AuthSession, UUID(payload["sid"]))
        user = db.get(UserModel, UUID(payload["sub"]))
        if not session or not user or session.user_id != user.id or session.company_id != user.company_id:
            raise ValueError("session")
        if session.revoked_at or aware(session.expires_at) <= utcnow() or not user.is_active:
            raise ValueError("expired")
        company = db.get(CompanyModel, user.company_id)
        if not company or not company.is_active or str(user.company_id) != payload["company_id"]:
            raise ValueError("company")
        bind_company(db, user.company_id)
        return AuthenticatedUser(
            user_id=user.id,
            email=user.email,
            company_id=user.company_id,
            role=user.role,
            permissions=permissions_for(db, user),
            session_id=session.id,
            is_support_session=False,
        )
    except SQLAlchemyError:
        raise
    except Exception:
        grant = db.scalar(select(SupportGrant).where(SupportGrant.token_hash == fingerprint(raw_token)))
        if grant and aware(grant.expires_at) > utcnow() and grant.revoked_at is None:
            admin = db.get(UserModel, grant.granted_by)
            company = db.get(CompanyModel, grant.company_id)
            if admin and company and company.is_active:
                bind_company(db, company.id)
                support_perms = (
                    [p.value for p in Permission if p.value != "platform:manage"]
                    if grant.scope == "full_support"
                    else ["audit:logs:read", "sales:read", "customers:read", "products:read"]
                )
                return AuthenticatedUser(
                    user_id=admin.id,
                    email=f"support+{grant.id.hex[:6]}@salesia.enterprise",
                    company_id=company.id,
                    role="support_agent",
                    permissions=support_perms,
                    session_id=grant.id,
                    is_support_session=True,
                    support_grant_id=grant.id,
                )
        raise DomainUnauthorizedException("Sesión inválida, revocada o expirada.")


def require_permission(*required_permissions: str) -> Callable:
    async def permission_checker(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if not any(perm in current_user.permissions for perm in required_permissions):
            perms_str = "', '".join(required_permissions)
            raise DomainForbiddenException(f"No cuenta con el permiso requerido: '{perms_str}'.")
        return current_user

    return permission_checker
