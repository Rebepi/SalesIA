from datetime import timedelta
from uuid import UUID

from fastapi import HTTPException, Request
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.seguridad.application.configuracion import _DUMMY_HASH
from salesia.modules.seguridad.application.contracts.autenticacion import LoginRequest, RefreshTokenRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.infrastructure.models import AuthSession, LoginThrottle
from salesia.modules.seguridad.infrastructure.security import decode_token, hash_password, needs_rehash, verify_password
from salesia.modules.seguridad.infrastructure.sessions import (
    aware,
    consume_factor,
    fingerprint,
    open_session,
    token_pair,
    utcnow,
)
from salesia.shared.infrastructure.errors import DomainUnauthorizedException
from salesia.shared.infrastructure.models import CompanyModel, UserModel
from salesia.shared.infrastructure.tenant_scope import bind_company


def login(req: LoginRequest, request: Request, db: Session):
    email = str(req.email).lower().strip()
    now = utcnow()
    key = fingerprint(email)
    throttle = db.get(LoginThrottle, key)
    if throttle and throttle.blocked_until and aware(throttle.blocked_until) > now:
        raise HTTPException(
            429, "Demasiados intentos. Intente nuevamente en 15 minutos.", headers={"Retry-After": "900"}
        )
    user = db.scalar(select(UserModel).where(func.lower(UserModel.email) == email))
    valid = verify_password(req.password, user.hashed_password if user else _DUMMY_HASH)
    company = db.get(CompanyModel, user.company_id) if user else None
    valid = valid and user is not None and user.is_active and company is not None and company.is_active
    if user and company:
        bind_company(db, user.company_id)
    if valid and user.mfa_enabled:
        valid = consume_factor(db, user, req.mfa_code or "")
    if not valid:
        if not throttle:
            throttle = LoginThrottle(key=key, attempts=0, window_start=now)
            db.add(throttle)
        if aware(throttle.window_start) + timedelta(minutes=15) <= now:
            throttle.attempts = 0
            throttle.window_start = now
        throttle.attempts += 1
        if throttle.attempts >= 5:
            throttle.blocked_until = now + timedelta(minutes=15)
        if user and company:
            record_audit_event(
                db,
                company_id=user.company_id,
                actor_id=user.id,
                actor_email=user.email,
                action="LOGIN_BLOCKED" if throttle.attempts >= 5 else "LOGIN_FAILED",
                entity_type="User",
                entity_id=user.id,
                reason="Demasiados intentos" if throttle.attempts >= 5 else "Credenciales o segundo factor incorrectos",
                result="FAILURE",
                category="AUTH",
                request=request,
                fail_critical=False,
            )
        db.commit()
        raise DomainUnauthorizedException("Credenciales o segundo factor incorrectos.")
    if throttle:
        db.delete(throttle)
    if needs_rehash(user.hashed_password):
        user.hashed_password = hash_password(req.password)
        db.flush()
    pair = open_session(db, user, request)
    record_audit_event(
        db,
        company_id=user.company_id,
        actor_id=user.id,
        actor_email=user.email,
        action="LOGIN_SUCCESS",
        entity_type="User",
        entity_id=user.id,
        diff={"ip": request.client.host if request.client else None},
        result="SUCCESS",
        category="AUTH",
        request=request,
        fail_critical=False,
    )
    db.commit()
    return pair


def refresh_tokens(req: RefreshTokenRequest, db: Session):
    try:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("type")
        session = db.get(AuthSession, UUID(payload["sid"]))
        user = db.get(UserModel, UUID(payload["sub"]))
        if (
            not session
            or not user
            or session.user_id != user.id
            or session.company_id != user.company_id
            or not user.is_active
            or session.revoked_at
            or aware(session.expires_at) <= utcnow()
        ):
            raise ValueError("session")
        company = db.get(CompanyModel, user.company_id)
        if not company or not company.is_active:
            raise ValueError("company")
        if session.refresh_hash != fingerprint(req.refresh_token):
            session.revoked_at = utcnow()
            session.sudo_until = None
            db.commit()
            raise ValueError("replay")
    except (KeyError, ValueError, TypeError):
        raise DomainUnauthorizedException("Sesión de renovación inválida o revocada.")
    pair = token_pair(db, user, session)
    rotated = db.execute(
        update(AuthSession)
        .where(
            AuthSession.id == session.id,
            AuthSession.refresh_hash == fingerprint(req.refresh_token),
            AuthSession.revoked_at.is_(None),
        )
        .values(refresh_hash=fingerprint(pair["refresh_token"]))
    )
    if rotated.rowcount != 1:
        db.execute(update(AuthSession).where(AuthSession.id == session.id).values(revoked_at=utcnow(), sudo_until=None))
        db.commit()
        raise DomainUnauthorizedException("Reutilización de token detectada; vuelva a iniciar sesión.")
    db.commit()
    return pair


def logout(current_user: AuthenticatedUser, db: Session):
    session = db.get(AuthSession, current_user.session_id)
    session.revoked_at = utcnow()
    session.sudo_until = None
    db.commit()
    return {"message": "Sesión cerrada correctamente"}