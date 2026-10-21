import json

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.analitica.infrastructure.models.artefactos import AnalyticsArtifact
from salesia.modules.organizacion.application import periodos_funcionales as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db
from salesia.shared.infrastructure.models import AuditLogModel

router = APIRouter(prefix="/organization/module-periods")


@router.get("")
def get_functional_periods(user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db)):
    return service.state(db, user.company_id)


@router.post("/preview")
def preview_functional_close(payload: service.ClosePreview, user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db)):
    return service.preview(db, user.company_id, payload)


@router.post("/close")
def close_functional_periods(payload: service.CloseRequest, user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.close(db, user, payload, key)


@router.post("/reopen")
def reopen_functional_period(payload: service.ReopenRequest, user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.reopen(db, user, payload, key)


@router.post("/revoke")
def revoke_functional_reopening(payload: service.RevokeRequest, user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.revoke(db, user, payload, key)


@router.get("/history")
def functional_period_history(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db)):
    rows = db.scalars(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == user.company_id, AnalyticsArtifact.kind == "period_control", AnalyticsArtifact.artifact_key == "company").order_by(AnalyticsArtifact.version.desc()).offset(offset).limit(limit)).all()
    return [{"version": row.version, **json.loads(row.data_json)} for row in rows]


@router.get("/changes")
def functional_period_changes(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db)):
    rows = db.scalars(select(AuditLogModel).where(AuditLogModel.company_id == user.company_id, AuditLogModel.action == "OPERATION_IN_REOPENED_PERIOD").order_by(AuditLogModel.created_at.desc(), AuditLogModel.id).offset(offset).limit(limit)).all()
    return [{"id": str(row.id), "actor": row.actor_email, "at": row.created_at.isoformat(), **json.loads(row.payload_diff)} for row in rows]
