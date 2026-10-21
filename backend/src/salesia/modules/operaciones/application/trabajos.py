from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application.auxiliares.job_response import job_response
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.errors import DomainForbiddenException
from salesia.shared.infrastructure.models import JobModel


def get_job_status(job_id: UUID, current_user: AuthenticatedUser, db: Session):
    job = db.scalar(select(JobModel).where(JobModel.id == job_id, JobModel.company_id == current_user.company_id))

    if not job:
        other = db.scalar(select(JobModel.id).where(JobModel.id == job_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Trabajo no encontrado.")

    return job_response(job)


def cancel_job(job_id: UUID, current_user: AuthenticatedUser, db: Session):
    job = db.scalar(
        select(JobModel).where(JobModel.id == job_id, JobModel.company_id == current_user.company_id).with_for_update()
    )

    if not job:
        other = db.scalar(select(JobModel.id).where(JobModel.id == job_id))

        if other:
            raise DomainForbiddenException("Recurso de otra empresa no permitido.")

        raise HTTPException(404, "Trabajo no encontrado.")

    if job.status in ("completed", "failed", "cancelled"):
        return job_response(job)

    job.cancel_requested = True

    if job.status in ("pending", "staged"):
        job.status = "cancelled"

    db.commit()

    return job_response(job)
