from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application.auxiliares.now import now
from salesia.modules.operaciones.application.auxiliares.setting_value import setting_value
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.models import JobModel, OutboxEventModel


def get_system_operational_status(current_user: AuthenticatedUser, db: Session):
    pending = db.scalar(
        select(func.count())
        .select_from(JobModel)
        .where(JobModel.company_id == current_user.company_id, JobModel.status.in_(("pending", "running")))
    )

    outbox = db.scalar(
        select(func.count())
        .select_from(OutboxEventModel)
        .where(OutboxEventModel.company_id == current_user.company_id, OutboxEventModel.processed_at.is_(None))
    )

    failed = db.scalar(
        select(func.count())
        .select_from(JobModel)
        .where(JobModel.company_id == current_user.company_id, JobModel.status == "failed")
    )

    maintenance = setting_value(db, current_user.company_id, "maintenance", {"active": False})

    degraded = setting_value(db, current_user.company_id, "degraded_mode", {"active": False})

    state = (
        "maintenance" if maintenance.get("active") else "degraded" if degraded.get("active") or failed else "healthy"
    )

    return {
        "status": state,
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "pending_jobs": pending,
        "failed_jobs": failed,
        "outbox_backlog": outbox,
        "maintenance": maintenance,
        "degraded_mode": degraded,
        "measured_at": now().isoformat(),
    }
