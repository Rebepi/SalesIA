import secrets
from urllib.parse import quote

from fastapi import HTTPException
from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from salesia.modules.seguridad.application.contracts.mfa import MfaVerifyRequest, SudoVerifyRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.infrastructure.models import AuthFactor, AuthSession, RecoveryCode
from salesia.modules.seguridad.infrastructure.security import generate_totp_secret, verify_password
from salesia.modules.seguridad.infrastructure.sessions import aware, cipher, consume_factor, fingerprint, utcnow
from salesia.shared.infrastructure.errors import DomainConflictException, DomainUnauthorizedException
from salesia.shared.infrastructure.models import UserModel


def setup_mfa(req: SudoVerifyRequest, current_user: AuthenticatedUser, db: Session):
    user = db.get(UserModel, current_user.user_id)
    if not verify_password(req.password, user.hashed_password):
        raise DomainUnauthorizedException("Credencial incorrecta.")
    if user.mfa_enabled:
        raise DomainConflictException("MFA ya está activo; no se puede reemplazar sin recuperación controlada.")
    secret = generate_totp_secret()
    factor = db.get(AuthFactor, user.id)
    if factor is None:
        factor = AuthFactor(user_id=user.id, encrypted_secret="", enabled=False, last_counter=-1)
        db.add(factor)
    factor.encrypted_secret = cipher().encrypt(secret.encode()).decode()
    factor.last_counter = -1
    factor.enabled = False
    codes = [secrets.token_urlsafe(18) for _ in range(8)]
    db.execute(delete(RecoveryCode).where(RecoveryCode.user_id == user.id))
    db.add_all([RecoveryCode(user_id=user.id, code_hash=fingerprint(code)) for code in codes])
    db.commit()
    return {
        "totp_secret": secret,
        "provisioning_uri": f"otpauth://totp/SalesIA:{quote(user.email)}?secret={secret}&issuer=SalesIA",
        "recovery_codes": codes,
    }


def verify_mfa(req: MfaVerifyRequest, current_user: AuthenticatedUser, db: Session):
    user = db.get(UserModel, current_user.user_id)
    if not consume_factor(db, user, req.code, allow_pending=True):
        raise HTTPException(400, "Segundo factor incorrecto o ya utilizado.")
    user.mfa_enabled = True
    user.mfa_secret = None
    db.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user.id, AuthSession.id != current_user.session_id)
        .values(revoked_at=utcnow(), sudo_until=None)
    )
    db.commit()
    return {"verified": True, "mfa_enabled": True}


def regenerate_mfa_recovery_codes(current_user: AuthenticatedUser, db: Session):
    user = db.get(UserModel, current_user.user_id)
    session = db.get(AuthSession, current_user.session_id)
    if not user or not user.mfa_enabled:
        raise DomainConflictException("MFA debe estar activo para regenerar códigos de respaldo.")
    if not session or not session.sudo_until or aware(session.sudo_until) <= utcnow():
        raise DomainUnauthorizedException("Se requiere reautenticación reciente para regenerar códigos de respaldo.")
    codes = [secrets.token_urlsafe(18) for _ in range(8)]
    db.execute(delete(RecoveryCode).where(RecoveryCode.user_id == user.id))
    db.add_all([RecoveryCode(user_id=user.id, code_hash=fingerprint(code)) for code in codes])
    db.commit()
    return {"recovery_codes": codes, "generated_at": utcnow().isoformat()}
