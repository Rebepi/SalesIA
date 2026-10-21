from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.auditoria.application.contracts.seguridad_incident import UserQuarantineRequest
from salesia.modules.auditoria.service import record_audit_event
from salesia.modules.operaciones.infrastructure_models import ApiCredential
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.infrastructure.models import AuthSession
from salesia.shared.infrastructure.models import UserModel


def quarantine_compromised_user(payload: UserQuarantineRequest, current_user: AuthenticatedUser, db: Session):
    start_time = datetime.now(timezone.utc)
    target_user = db.scalar(
        select(UserModel)
        .where(UserModel.id == payload.user_id, UserModel.company_id == current_user.company_id)
        .with_for_update()
    )
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario a poner en cuarentena no encontrado en la empresa."
        )
    target_user.is_active = False

    active_sessions = db.scalars(
        select(AuthSession)
        .where(AuthSession.user_id == target_user.id, AuthSession.revoked_at.is_(None))
        .with_for_update()
    ).all()
    now_utc = datetime.now(timezone.utc)
    for session_entry in active_sessions:
        session_entry.revoked_at = now_utc
        session_entry.sudo_until = None

    active_keys = db.scalars(
        select(ApiCredential)
        .where(ApiCredential.created_by == target_user.id, ApiCredential.revoked_at.is_(None))
        .with_for_update()
    ).all()
    for key_entry in active_keys:
        key_entry.revoked_at = now_utc

    record_audit_event(
        db,
        company_id=current_user.company_id,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        action="INCIDENT_ACCOUNT_QUARANTINED",
        entity_type="User",
        entity_id=target_user.id,
        diff={
            "ticket": payload.incident_ticket,
            "reason": payload.reason,
            "revoked_sessions": len(active_sessions),
            "revoked_api_keys": len(active_keys),
        },
        reason=f"Cuarentena de seguridad por incidente: {payload.incident_ticket}",
        category="GOVERNANCE",
        fail_critical=True,
    )
    db.commit()
    elapsed_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000.0

    return {
        "quarantined": True,
        "user_id": str(target_user.id),
        "email": target_user.email,
        "ticket": payload.incident_ticket,
        "sessions_revoked": len(active_sessions),
        "api_keys_revoked": len(active_keys),
        "containment_steps": [
            "Cuenta deshabilitada (is_active=False)",
            "Sesiones activas revocadas en base de datos",
            "Claves API generadas por el usuario invalidadas",
            "Evento forense registrado en auditoría inmutable",
        ],
        "elapsed_ms": round(elapsed_ms, 2),
    }
