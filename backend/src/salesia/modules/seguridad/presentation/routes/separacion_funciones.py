import json

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.analitica.infrastructure.models.artefactos import AnalyticsArtifact
from salesia.modules.seguridad.application import separacion_funciones as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/business/function-separation")


@router.get("")
def get_function_separation(user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db)):
    return service.current(db, user.company_id)


@router.put("")
def save_function_separation(payload: service.SeparationSave, user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.save(db, user, payload, key)


@router.get("/history")
def function_separation_history(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db)):
    rows = db.scalars(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == user.company_id, AnalyticsArtifact.kind == "function_separation", AnalyticsArtifact.artifact_key == "company").order_by(AnalyticsArtifact.version.desc()).offset(offset).limit(limit)).all()
    return [{"version": row.version, **json.loads(row.data_json)} for row in rows]
