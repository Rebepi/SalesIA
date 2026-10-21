from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

import salesia.modules.auditoria.application.auditoria_consulta as service_auditoria_consulta
from salesia.modules.auditoria.application.contracts.auditoria_consulta import (
    AuditLogCreateRequest,
    AuditRetentionPurgeRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/audit/logs", operation_id="list_audit_logs")
@router.get("/audit-logs", operation_id="list_audit_logs_alias", deprecated=True)
def list_audit_logs(
    cursor: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    action: Optional[str] = None,
    actor_id: Optional[UUID] = None,
    actor_email: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    result: Optional[str] = None,
    trace_id: Optional[str] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service_auditoria_consulta.list_audit_logs(
        cursor=cursor,
        limit=limit,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_id=actor_id,
        actor_email=actor_email,
        start_date=start_date,
        end_date=end_date,
        result=result,
        trace_id=trace_id,
        current_user=current_user,
        db=db,
    )


@router.get("/audit/timeline/{entity_type}/{entity_id}", operation_id="get_audit_timeline")
@router.get("/audit-logs/timeline/{entity_type}/{entity_id}", operation_id="get_audit_timeline_alias", deprecated=True)
def get_timeline(
    entity_type: str,
    entity_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service_auditoria_consulta.get_timeline(
        entity_type=entity_type, entity_id=entity_id, current_user=current_user, db=db
    )


@router.post("/audit/retention/purge", operation_id="purge_audit_retention")
@router.post("/audit-logs/retention/purge", operation_id="purge_audit_retention_alias", deprecated=True)
def purge_retention(
    payload: AuditRetentionPurgeRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service_auditoria_consulta.purge_retention(payload=payload, current_user=current_user, db=db)


@router.get("/audit/logs/{log_id}", operation_id="get_audit_log_detail")
@router.get("/audit-logs/{log_id}", operation_id="get_audit_log_detail_alias", deprecated=True)
def get_audit_log_detail(
    log_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    return service_auditoria_consulta.get_audit_log_detail(log_id=log_id, current_user=current_user, db=db)


@router.delete("/audit/logs/{log_id}", operation_id="deny_audit_log_delete")
@router.delete("/audit-logs/{log_id}", operation_id="deny_audit_log_delete_alias", deprecated=True)
@router.put("/audit/logs/{log_id}", operation_id="deny_audit_log_put")
@router.put("/audit-logs/{log_id}", operation_id="deny_audit_log_put_alias", deprecated=True)
def deny_audit_mutation(log_id: UUID):
    return service_auditoria_consulta.deny_audit_mutation(log_id=log_id)


@router.post("/audit/logs", status_code=status.HTTP_201_CREATED, operation_id="record_audit_log")
@router.post("/audit-logs", status_code=status.HTTP_201_CREATED, operation_id="record_audit_log_alias", deprecated=True)
def record_audit_log(
    payload: AuditLogCreateRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service_auditoria_consulta.record_audit_log(
        payload=payload, request=request, current_user=current_user, db=db
    )


@router.post("/audit/logs/export", operation_id="export_audit_logs")
@router.post("/audit-logs/export", operation_id="export_audit_logs_alias", deprecated=True)
def export_audit_logs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service_auditoria_consulta.export_audit_logs(
        start_date=start_date, end_date=end_date, current_user=current_user, db=db
    )
