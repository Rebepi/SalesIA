from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.operaciones.application.trabajos as service_trabajos
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/jobs/{job_id}")
def get_job_status(
    job_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_trabajos.get_job_status(job_id=job_id, current_user=current_user, db=db)


@router.post("/jobs/{job_id}/cancel")
def cancel_job(
    job_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_trabajos.cancel_job(job_id=job_id, current_user=current_user, db=db)
