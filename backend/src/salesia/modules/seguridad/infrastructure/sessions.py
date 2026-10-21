import base64
import hashlib
import json
import secrets
import time
from datetime import datetime, timedelta, timezone
from uuid import UUID

from cryptography.fernet import Fernet
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from salesia.modules.seguridad.domain.roles import get_role_catalog
from salesia.modules.seguridad.infrastructure.models import AuthFactor, AuthSession, CustomRole, RecoveryCode
from salesia.modules.seguridad.infrastructure.security import (
    create_access_token,
    create_refresh_token,
    generate_totp_code,
)
from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.models import UserModel
from salesia.shared.infrastructure.tenant_scope import bind_company


def utcnow():
    return datetime.now(timezone.utc)


def aware(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def cipher():
    key = settings.auth_encryption_key
    if not key:
        key = base64.urlsafe_b64encode(hashlib.sha256(settings.secret_key.encode()).digest()).decode()
    return Fernet(key.encode())


def permissions_for(db: Session, user: UserModel):
    bind_company(db, user.company_id)
    role = next((r for r in get_role_catalog() if r.role.value == user.role), None)
    if role:
        return list(role.permissions)
    custom = db.scalar(
        select(CustomRole).where(CustomRole.company_id == user.company_id, CustomRole.role_key == user.role)
    )
    return json.loads(custom.permissions_json) if custom else []


def token_pair(db: Session, user: UserModel, session: AuthSession):
    payload = {
        "sub": str(user.id),
        "sid": str(session.id),
        "company_id": str(user.company_id),
        "email": user.email,
        "role": user.role,
        "permissions": permissions_for(db, user),
    }
    access = create_access_token(payload)
    refresh = create_refresh_token(payload)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": 3600,
        "user_id": user.id,
        "email": user.email,
        "company_id": user.company_id,
        "role": user.role,
        "permissions": payload["permissions"],
    }


def open_session(db: Session, user: UserModel, request):
    now = utcnow()
    session = AuthSession(
        user_id=user.id,
        company_id=user.company_id,
        refresh_hash=fingerprint(secrets.token_urlsafe(48)),
        created_at=now,
        expires_at=now + timedelta(days=7),
        user_agent=request.headers.get("user-agent", "")[:512],
        ip_address=request.client.host[:64] if request.client else "",
    )
    db.add(session)
    db.flush()
    pair = token_pair(db, user, session)
    session.refresh_hash = fingerprint(pair["refresh_token"])
    return pair


def revoke_user_sessions(db: Session, user_id: UUID):
    db.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=utcnow(), sudo_until=None)
    )


def consume_factor(db: Session, user: UserModel, code: str, allow_pending=False):
    factor = db.get(AuthFactor, user.id)
    if factor is None or not factor.enabled and not allow_pending:
        return False
    if code.isdigit() and len(code) == 6:
        secret = cipher().decrypt(factor.encrypted_secret.encode()).decode()
        current = int(time.time() // 30)
        for counter in (current, current - 1, current + 1):
            if secrets.compare_digest(generate_totp_code(secret, counter), code):
                changed = db.execute(
                    update(AuthFactor)
                    .where(AuthFactor.user_id == user.id, AuthFactor.last_counter < counter)
                    .values(last_counter=counter, enabled=True)
                )
                return changed.rowcount == 1
        return False
    if not factor.enabled:
        return False
    changed = db.execute(
        update(RecoveryCode)
        .where(
            RecoveryCode.user_id == user.id, RecoveryCode.code_hash == fingerprint(code), RecoveryCode.used_at.is_(None)
        )
        .values(used_at=utcnow())
    )
    return changed.rowcount == 1
