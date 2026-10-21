from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application.auxiliares.now import now
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.models import JobModel


def get_operational_metrics(current_user: AuthenticatedUser, db: Session):
    total_jobs = (
        db.scalar(select(func.count()).select_from(JobModel).where(JobModel.company_id == current_user.company_id)) or 0
    )

    failed_jobs = (
        db.scalar(
            select(func.count())
            .select_from(JobModel)
            .where(JobModel.company_id == current_user.company_id, JobModel.status == "failed")
        )
        or 0
    )

    completed_jobs = (
        db.scalar(
            select(func.count())
            .select_from(JobModel)
            .where(JobModel.company_id == current_user.company_id, JobModel.status == "completed")
        )
        or 0
    )

    failure_rate = failed_jobs / total_jobs if total_jobs else 0.0

    return {
        "jobs": {"total": total_jobs, "completed": completed_jobs, "failed": failed_jobs, "failure_rate": failure_rate},
        "slo_targets": {
            "availability_target": settings.availability_target,
            "rpo_minutes": settings.recovery_point_objective_minutes,
            "rto_minutes": settings.recovery_time_objective_minutes,
        },
        "measured_at": now().isoformat(),
    }
