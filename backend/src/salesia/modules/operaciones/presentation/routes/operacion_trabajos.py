from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.operacion_trabajos as service_operacion_trabajos
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import require_permission
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/operations/jobs")
def list_operational_jobs(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(require_permission("operations:manage")),
    db: Session = Depends(get_db),
):

    return service_operacion_trabajos.list_operational_jobs(
        status_filter=status_filter, limit=limit, offset=offset, current_user=current_user, db=db
    )


@router.post("/operations/jobs/{job_id}/retry", status_code=202)
def retry_operational_job(
    job_id: UUID,
    current_user: AuthenticatedUser = Depends(require_permission("operations:manage")),
    db: Session = Depends(get_db),
):

    return service_operacion_trabajos.retry_operational_job(job_id=job_id, current_user=current_user, db=db)
