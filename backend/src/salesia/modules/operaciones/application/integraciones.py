from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application.auxiliares.now import now
from salesia.modules.operaciones.application.contracts.integraciones import (
    IntegrationCreateRequest,
    IntegrationCredentialRequest,
    IntegrationModeRequest,
)
from salesia.modules.operaciones.infrastructure_models import IntegrationConnection
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.infrastructure.sessions import cipher


def list_integrations(current_user: AuthenticatedUser, db: Session):
    rows = db.scalars(
        select(IntegrationConnection)
        .where(IntegrationConnection.company_id == current_user.company_id)
        .order_by(IntegrationConnection.created_at.desc())
    ).all()

    return {
        "items": [
            {
                "id": str(row.id),
                "provider_name": row.provider,
                "category": row.category,
                "status": row.status if row.active else "unconfigured",
                "last_sync": row.last_sync.isoformat() if row.last_sync else None,
                "masked_key": f"cred_••••{str(row.id)[-4:]}",
                "mode": row.mode,
                "error_message": row.last_error,
                "latency_ms": row.latency_ms,
            }
            for row in rows
        ],
        "count": len(rows),
    }


def create_integration(payload: IntegrationCreateRequest, current_user: AuthenticatedUser, db: Session):
    existing = db.scalar(
        select(IntegrationConnection).where(
            IntegrationConnection.company_id == current_user.company_id,
            IntegrationConnection.provider == payload.provider.lower(),
            IntegrationConnection.category == payload.category.lower(),
            IntegrationConnection.active.is_(True),
        )
    )

    if existing:
        raise HTTPException(409, "Ya existe una integración activa para este proveedor y categoría.")

    row = IntegrationConnection(
        company_id=current_user.company_id,
        provider=payload.provider.lower(),
        category=payload.category.lower(),
        mode=payload.mode,
        status="connected",
        encrypted_secret=cipher().encrypt(payload.credential.encode()).decode(),
        active=True,
        updated_at=now(),
    )

    db.add(row)

    db.commit()

    return {
        "id": str(row.id),
        "provider_name": row.provider,
        "category": row.category,
        "mode": row.mode,
        "status": row.status,
        "masked_key": f"cred_••••{str(row.id)[-4:]}",
    }


def rotate_integration_credential(
    connection_id: UUID, payload: IntegrationCredentialRequest, current_user: AuthenticatedUser, db: Session
):
    row = db.scalar(
        select(IntegrationConnection)
        .where(IntegrationConnection.id == connection_id, IntegrationConnection.company_id == current_user.company_id)
        .with_for_update()
    )

    if not row:
        raise HTTPException(404, "Integración no encontrada.")

    row.previous_encrypted_secret = row.encrypted_secret

    row.previous_valid_until = now() + timedelta(minutes=15)

    row.encrypted_secret = cipher().encrypt(payload.credential.encode()).decode()

    row.status = "connected"

    row.active = True

    row.last_error = None

    row.updated_at = now()

    db.commit()

    return {
        "id": str(row.id),
        "status": row.status,
        "rotated_at": row.updated_at.isoformat(),
        "previous_valid_until": row.previous_valid_until.isoformat(),
    }


def update_integration_mode(
    connection_id: UUID, payload: IntegrationModeRequest, current_user: AuthenticatedUser, db: Session
):
    row = db.scalar(
        select(IntegrationConnection)
        .where(IntegrationConnection.id == connection_id, IntegrationConnection.company_id == current_user.company_id)
        .with_for_update()
    )

    if not row:
        raise HTTPException(404, "Integración no encontrada.")

    row.mode = payload.mode

    row.updated_at = now()

    db.commit()

    return {"id": str(row.id), "mode": row.mode, "updated_at": row.updated_at.isoformat()}


def diagnose_integration(connection_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(IntegrationConnection)
        .where(IntegrationConnection.id == connection_id, IntegrationConnection.company_id == current_user.company_id)
        .with_for_update()
    )

    if not row:
        raise HTTPException(404, "Integración no encontrada.")

    started = datetime.now(timezone.utc)

    valid = row.active and bool(row.encrypted_secret)

    row.status = "connected" if valid else "unconfigured"

    row.last_error = None if valid else "La integración no tiene una credencial activa."

    row.last_sync = now()

    row.latency_ms = max(1, int((datetime.now(timezone.utc) - started).total_seconds() * 1000))

    row.updated_at = now()

    db.commit()

    if not valid:
        raise HTTPException(409, row.last_error)

    return {
        "id": str(row.id),
        "status": row.status,
        "latency_ms": row.latency_ms,
        "checked_at": row.last_sync.isoformat(),
        "scope": "credential_configuration",
    }
