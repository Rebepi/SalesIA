from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application.auxiliares.job_response import job_response
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.models import JobModel


def list_operational_jobs(
    status_filter: Optional[str], limit: int, offset: int, current_user: AuthenticatedUser, db: Session
):
    query = select(JobModel).where(JobModel.company_id == current_user.company_id)

    if status_filter:
        query = query.where(JobModel.status == status_filter)

    rows = db.scalars(query.order_by(JobModel.created_at.desc(), JobModel.id.desc()).offset(offset).limit(limit)).all()

    return {"items": [job_response(row) for row in rows], "count": len(rows)}


def retry_operational_job(job_id: UUID, current_user: AuthenticatedUser, db: Session):
    row = db.scalar(
        select(JobModel).where(JobModel.id == job_id, JobModel.company_id == current_user.company_id).with_for_update()
    )

    if not row:
        raise HTTPException(404, "Trabajo no encontrado.")

    if row.status != "failed":
        raise HTTPException(409, "Solo se pueden reintentar trabajos fallidos.")

    row.status = "pending"

    row.progress = 0

    row.result = None

    row.cancel_requested = False

    row.lease_until = None

    db.commit()

    return job_response(row)
