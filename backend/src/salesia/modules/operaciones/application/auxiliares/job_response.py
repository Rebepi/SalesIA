import json


def job_response(row):

    return {
        "job_id": str(row.id),
        "company_id": str(row.company_id),
        "job_type": row.job_type,
        "status": row.status,
        "progress_pct": row.progress,
        "result": json.loads(row.result) if row.result else None,
        "cancel_requested": row.cancel_requested,
        "attempts": row.attempts,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }
