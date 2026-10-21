from fastapi import HTTPException
from sqlalchemy import select

from salesia.modules.operaciones.infrastructure_models import AnalyticsArtifact


def report_run_row(db, company_id, run_id, lock=False):

    query = select(AnalyticsArtifact).where(
        AnalyticsArtifact.id == run_id,
        AnalyticsArtifact.company_id == company_id,
        AnalyticsArtifact.kind == "report_run",
    )

    if lock:
        query = query.with_for_update()

    row = db.scalar(query)

    if not row:
        raise HTTPException(404, "Ejecución de reporte no encontrada.")

    return row
