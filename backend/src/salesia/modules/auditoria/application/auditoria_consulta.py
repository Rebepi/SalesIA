import base64
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.auditoria.application.auxiliares.parse_diff import _parse_diff
from salesia.modules.auditoria.application.contracts.auditoria_consulta import (
    AuditLogCreateRequest,
    AuditRetentionPurgeRequest,
)
from salesia.modules.auditoria.service import get_business_timeline, purge_audit_logs, record_audit_event, redact_diff
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import AuditLogModel


def list_audit_logs(
    cursor: Optional[str],
    limit: int,
    entity_type: Optional[str],
    entity_id: Optional[UUID],
    action: Optional[str],
    actor_id: Optional[UUID],
    actor_email: Optional[str],
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    result: Optional[str],
    trace_id: Optional[str],
    current_user: AuthenticatedUser,
    db: Session,
):
    query = select(AuditLogModel).where(AuditLogModel.company_id == current_user.company_id)
    if entity_type:
        query = query.where(AuditLogModel.entity_type == entity_type)
    if entity_id:
        query = query.where(AuditLogModel.entity_id == entity_id)
    if action:
        query = query.where(AuditLogModel.action == action)
    if actor_id:
        query = query.where(AuditLogModel.actor_id == actor_id)
    if actor_email:
        query = query.where(AuditLogModel.actor_email == actor_email)
    if start_date:
        query = query.where(AuditLogModel.created_at >= start_date)
    if end_date:
        query = query.where(AuditLogModel.created_at <= end_date)
    if trace_id:
        query = query.where(AuditLogModel.trace_id == trace_id)

    if cursor:
        try:
            raw_cursor = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
            c_time_str, c_id_str = raw_cursor.split("|", 1)
            c_time = datetime.fromisoformat(c_time_str)
            c_id = UUID(c_id_str)
            query = query.where(
                (AuditLogModel.created_at < c_time) | ((AuditLogModel.created_at == c_time) & (AuditLogModel.id < c_id))
            )
        except Exception:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Cursor de paginación inválido")

    logs = (
        db.execute(query.order_by(AuditLogModel.created_at.desc(), AuditLogModel.id.desc()).limit(limit + 1))
        .scalars()
        .all()
    )
    has_more = len(logs) > limit
    page_logs = logs[:limit]

    next_cursor = None
    if has_more and page_logs:
        last = page_logs[-1]
        next_cursor = base64.urlsafe_b64encode(f"{last.created_at.isoformat()}|{last.id}".encode("utf-8")).decode(
            "utf-8"
        )

    items = []
    for log in page_logs:
        parsed_diff = _parse_diff(log.payload_diff)
        if result and isinstance(parsed_diff, dict) and parsed_diff.get("result") != result:
            continue
        items.append(
            {
                "id": str(log.id),
                "company_id": str(log.company_id),
                "actor_id": str(log.actor_id) if log.actor_id else None,
                "actor_email": log.actor_email,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": str(log.entity_id),
                "trace_id": log.trace_id,
                "ip_address": log.ip_address,
                "payload_diff": redact_diff(parsed_diff),
                "chain_hash": log.entry_hash,
                "created_at": log.created_at.isoformat(),
            }
        )

    return {"items": items, "count": len(items), "next_cursor": next_cursor}


def get_timeline(entity_type: str, entity_id: UUID, current_user: AuthenticatedUser, db: Session):
    return get_business_timeline(db, current_user.company_id, entity_type, entity_id)


def purge_retention(payload: AuditRetentionPurgeRequest, current_user: AuthenticatedUser, db: Session):
    return purge_audit_logs(db, current_user.company_id, payload.category, payload.retention_days, current_user)


def get_audit_log_detail(log_id: UUID, current_user: AuthenticatedUser, db: Session):
    log = db.execute(
        select(AuditLogModel).where(AuditLogModel.id == log_id, AuditLogModel.company_id == current_user.company_id)
    ).scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de auditoría no encontrado")
    return {
        "id": str(log.id),
        "actor_id": str(log.actor_id) if log.actor_id else None,
        "actor_email": log.actor_email,
        "action": log.action,
        "entity_type": log.entity_type,
        "entity_id": str(log.entity_id),
        "trace_id": log.trace_id,
        "payload_diff": redact_diff(_parse_diff(log.payload_diff)),
        "created_at": log.created_at.isoformat(),
    }


def deny_audit_mutation(log_id: UUID):
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Los registros de auditoría son inmutables y de sólo anexado.",
    )


def record_audit_log(payload: AuditLogCreateRequest, request: Request, current_user: AuthenticatedUser, db: Session):
    entry = record_audit_event(
        db=db,
        company_id=current_user.company_id,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        action=payload.action,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        diff=payload.payload_diff,
        request=request,
        fail_critical=True,
    )
    db.commit()

    return {
        "id": str(entry.id),
        "trace_id": entry.trace_id,
        "action": entry.action,
        "entity_type": entry.entity_type,
        "entity_id": str(entry.entity_id),
        "chain_hash": entry.entry_hash,
        "created_at": entry.created_at.isoformat(),
    }


def export_audit_logs(
    start_date: Optional[datetime], end_date: Optional[datetime], current_user: AuthenticatedUser, db: Session
):
    query = select(AuditLogModel).where(AuditLogModel.company_id == current_user.company_id)
    if start_date:
        query = query.where(AuditLogModel.created_at >= start_date)
    if end_date:
        query = query.where(AuditLogModel.created_at <= end_date)

    logs = db.execute(query.order_by(AuditLogModel.created_at.asc()).limit(5000)).scalars().all()

    payload_data = [
        {
            "id": str(entry.id),
            "actor": entry.actor_email,
            "action": entry.action,
            "entity": entry.entity_type,
            "entity_id": str(entry.entity_id),
            "trace_id": entry.trace_id,
            "created_at": entry.created_at.isoformat(),
        }
        for entry in logs
    ]
    raw_bytes = json.dumps(payload_data, sort_keys=True).encode("utf-8")
    seal_hash = f"sha256-{hashlib.sha256(raw_bytes).hexdigest()}"

    record_audit_event(
        db,
        company_id=current_user.company_id,
        actor_id=current_user.user_id,
        actor_email=current_user.email,
        action="AUDIT_LOGS_EXPORT",
        entity_type="AuditExport",
        entity_id=uuid4(),
        diff={"exported_count": len(payload_data), "seal": seal_hash},
        reason="Exportacion de traza de auditoria",
        category="GOVERNANCE",
    )
    db.commit()

    return {
        "exported_records": len(payload_data),
        "cryptographic_seal": seal_hash,
        "export_format": "json_immutable",
        "data": payload_data,
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
