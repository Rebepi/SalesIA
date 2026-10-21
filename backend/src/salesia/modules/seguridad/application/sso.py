from uuid import UUID

from fastapi import HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.seguridad.application.contracts.sso import SsoLoginRequest
from salesia.modules.seguridad.infrastructure.security import decode_token
from salesia.modules.seguridad.infrastructure.sessions import open_session
from salesia.shared.infrastructure.errors import DomainUnauthorizedException
from salesia.shared.infrastructure.models import CompanyModel, UserModel


def sso_callback(req: SsoLoginRequest, request: Request, db: Session):
    try:
        payload = decode_token(req.id_token)
        issuer = payload.get("iss", "")
        aud = payload.get("aud", "")
        if issuer != "https://auth.salesia.enterprise" or aud != "salesia-enterprise":
            raise DomainUnauthorizedException("Token SSO emitido para otra aplicación o proveedor no autorizado.")
        email = str(payload.get("email", "")).lower()
        company_id_str = payload.get("company_id")
        if not email or not company_id_str:
            raise DomainUnauthorizedException("Token SSO no contiene la identidad requerida.")
        user = db.scalar(
            select(UserModel).where(func.lower(UserModel.email) == email, UserModel.company_id == UUID(company_id_str))
        )
        if not user or not user.is_active:
            raise DomainUnauthorizedException("Usuario de SSO no registrado o inactivo en esta empresa.")
        company = db.get(CompanyModel, user.company_id)
        if not company or not company.is_active:
            raise DomainUnauthorizedException("Empresa no activa.")
        pair = open_session(db, user, request)
        db.commit()
        return pair
    except (DomainUnauthorizedException, HTTPException):
        raise
    except Exception:
        raise DomainUnauthorizedException("Token SSO inválido.")
