import json
from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import Header

from salesia.modules.analitica.infrastructure.models.artefactos import AnalyticsArtifact
from salesia.modules.organizacion.application import calendario_operativo as service
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user, require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="/organization/operating-calendar")


@router.get("")
def get_operating_calendar(branch_id: UUID | None = None, user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.effective_calendar(db, user.company_id, branch_id)


@router.put("")
def save_operating_calendar(payload: service.CalendarSave, user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db), key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=128)):
    return service.save_calendar(db, user, payload, key)


@router.get("/history")
def operating_calendar_history(branch_id: UUID | None = None, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), user: AuthenticatedUser = Depends(require_permission("organization:manage")), db: Session = Depends(get_db)):
    service.scope_branch(db, user.company_id, branch_id)
    rows = db.scalars(select(AnalyticsArtifact).where(AnalyticsArtifact.company_id == user.company_id, AnalyticsArtifact.kind == "operating_calendar", AnalyticsArtifact.artifact_key == (str(branch_id) if branch_id else "company")).order_by(AnalyticsArtifact.version.desc()).limit(limit).offset(offset)).all()
    return [{"version": row.version, **json.loads(row.data_json)} for row in rows]


@router.get("/days")
def operating_calendar_days(start: date, days: int = Query(31, ge=1, le=366), branch_id: UUID | None = None, user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    calendar = service.effective_calendar(db, user.company_id, branch_id)
    if start.year > 9998:
        raise HTTPException(422, "La fecha inicial está fuera del rango de planificación.")
    return {"calendar": calendar, "items": [service.day_data(calendar, start + timedelta(days=index)) for index in range(days)]}


@router.post("/calculate")
def calculate_operating_date(payload: service.DateRequest, user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return service.calculate_date(service.effective_calendar(db, user.company_id, payload.branch_id), payload)
