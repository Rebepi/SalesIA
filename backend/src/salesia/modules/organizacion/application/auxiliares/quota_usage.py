import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from salesia.shared.infrastructure.models import AttachmentModel, JobModel


def quota_usage(db: Session, company_id: UUID) -> dict[str, int]:
    active_statuses = ("pending", "running")
    files_used = (
        db.scalar(
            select(func.count())
            .select_from(AttachmentModel)
            .where(AttachmentModel.company_id == company_id, AttachmentModel.uploaded.is_(True))
        )
        or 0
    )
    exports_active = (
        db.scalar(
            select(func.count())
            .select_from(JobModel)
            .where(
                JobModel.company_id == company_id,
                JobModel.status.in_(active_statuses),
                JobModel.job_type.in_(("export", "report", "report_export")),
            )
        )
        or 0
    )
    import_results = db.scalars(
        select(JobModel.result).where(
            JobModel.company_id == company_id,
            JobModel.job_type.like("import:%"),
            JobModel.status == "completed",
            JobModel.created_at >= datetime.now(timezone.utc) - timedelta(hours=24),
        )
    ).all()
    recent_import_rows = 0
    for raw_result in import_results:
        if raw_result:
            try:
                recent_import_rows += int(json.loads(raw_result).get("processed_rows", 0))
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
    intensive_queries_running = (
        db.scalar(
            select(func.count())
            .select_from(JobModel)
            .where(
                JobModel.company_id == company_id,
                JobModel.status.in_(active_statuses),
                JobModel.job_type.in_(("analysis", "analytics", "statistics", "probability")),
            )
        )
        or 0
    )
    return {
        "files_used": int(files_used),
        "exports_active": int(exports_active),
        "recent_import_rows": recent_import_rows,
        "intensive_queries_running": int(intensive_queries_running),
    }
