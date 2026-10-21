import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.auditoria.application.contracts.seguridad_claves_api import ApiKeyCreateRequest
from salesia.modules.operaciones.infrastructure_models import ApiCredential
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser


def create_api_key(payload: ApiKeyCreateRequest, current_user: AuthenticatedUser, db: Session):
    key_id = uuid4()
    raw_secret = f"sal_live_{secrets.token_urlsafe(36)}"
    secret_hash = hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()
    prefix = raw_secret[:12]
    masked = f"{prefix}...{raw_secret[-4:]}"
    now_utc = datetime.now(timezone.utc)
    db.add(
        ApiCredential(
            id=key_id,
            company_id=current_user.company_id,
            name=payload.name,
            prefix=prefix,
            secret_hash=secret_hash,
            scope=payload.scope,
            created_by=current_user.user_id,
        )
    )
    db.commit()
    return {
        "key_id": str(key_id),
        "name": payload.name,
        "masked_key": masked,
        "raw_secret_key": raw_secret,
        "scope": payload.scope,
        "warning": "Esta es la única vez que se muestra la clave completa. Guárdela de forma segura.",
        "created_at": now_utc.isoformat(),
    }


def list_api_keys(current_user: AuthenticatedUser, db: Session):
    rows = db.scalars(
        select(ApiCredential)
        .where(ApiCredential.company_id == current_user.company_id)
        .order_by(ApiCredential.created_at.desc())
    ).all()
    items = [
        {
            "key_id": str(row.id),
            "name": row.name,
            "masked_key": f"{row.prefix}...",
            "scope": row.scope,
            "created_by": str(row.created_by),
            "is_active": row.revoked_at is None,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]
    return {"items": items, "count": len(items)}


def revoke_api_key(key_id: UUID, current_user: AuthenticatedUser, db: Session):
    entry = db.scalar(
        select(ApiCredential)
        .where(ApiCredential.id == key_id, ApiCredential.company_id == current_user.company_id)
        .with_for_update()
    )
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key no encontrada")
    entry.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return {"revoked": True, "key_id": str(key_id)}


def verify_api_key_endpoint(required_scope: Optional[str], x_api_key: Optional[str], db: Session):
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Encabezado X-API-Key requerido")
    secret_hash = hashlib.sha256(x_api_key.encode("utf-8")).hexdigest()
    cred = db.scalar(select(ApiCredential).where(ApiCredential.secret_hash == secret_hash))
    if not cred:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key no válida o inexistente")
    if cred.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key revocada")
    if required_scope and cred.scope != required_scope and cred.scope != "integration":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Scope insuficiente: se requiere '{required_scope}' pero la clave posee '{cred.scope}'",
        )
    return {
        "valid": True,
        "key_id": str(cred.id),
        "name": cred.name,
        "scope": cred.scope,
        "company_id": str(cred.company_id),
    }
