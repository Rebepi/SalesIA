import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from salesia.modules.operaciones.application.auxiliares.job_response import job_response
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.shared.infrastructure.config import settings
from salesia.shared.infrastructure.models import BackupSnapshotModel, JobModel
from salesia.shared.infrastructure.transactions import claim_request, complete_request


def trigger_backup(current_user: AuthenticatedUser, db: Session, idempotency_key: str):
    if not settings.backup_encryption_key:
        raise HTTPException(503, "Configure BACKUP_ENCRYPTION_KEY antes de solicitar respaldos.")

    record, cached = claim_request(
        db,
        current_user.company_id,
        "backup.trigger",
        idempotency_key,
        {"company_id": str(current_user.company_id), "revision": settings.source_revision},
    )

    if cached is not None:
        return cached

    job = JobModel(
        company_id=current_user.company_id,
        requested_by=current_user.user_id,
        job_type="backup",
        status="pending",
        progress=0,
        payload_json=json.dumps({"source_revision": settings.source_revision}),
    )

    db.add(job)

    db.flush()

    result = job_response(job)

    complete_request(record, result)

    db.commit()

    return result


def get_backup_status(current_user: AuthenticatedUser, db: Session):
    rows = db.scalars(
        select(BackupSnapshotModel)
        .where(BackupSnapshotModel.company_id == current_user.company_id)
        .order_by(BackupSnapshotModel.created_at.desc())
        .limit(20)
    ).all()

    return {
        "items": [
            {
                "snapshot_id": row.snapshot_id,
                "status": row.status,
                "encrypted": row.encrypted,
                "checksum": row.checksum,
                "size_bytes": row.size_bytes,
                "source_revision": row.source_revision,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    }
