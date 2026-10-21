import json

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.analitica.infrastructure.models.artefactos import AnalyticsArtifact
from salesia.modules.organizacion.application import perfil_operativo as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/organization/operating-profile")


@router.get("")
def get_operating_profile(user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.current(db, user.company_id)


@router.post("/preview")
def preview_operating_profile(payload: service.ProfileChange, user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db)):
    return service.preview(db, user.company_id, payload)


@router.put("")
def save_operating_profile(payload: service.ProfileSave, user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.save(db, user, payload, key)


@router.get("/history")
def operating_profile_history(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db)):
    rows = db.scalars(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == user.company_id, AnalyticsArtifact.kind == "operating_profile", AnalyticsArtifact.artifact_key == "company").order_by(AnalyticsArtifact.version.desc()).offset(offset).limit(limit)).all()
    return [{"version": row.version, **json.loads(row.data_json)} for row in rows]
