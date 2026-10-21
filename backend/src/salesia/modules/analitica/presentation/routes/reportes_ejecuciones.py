from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.reportes_ejecuciones as service_reportes_ejecuciones
from salesia.modules.analitica.application.contracts.reportes_ejecuciones import ReportRunRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/report-runs", status_code=status.HTTP_202_ACCEPTED)
def trigger_report_run(
    payload: ReportRunRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_reportes_ejecuciones.trigger_report_run(payload=payload, current_user=current_user, db=db)


@router.get("/report-runs")
def list_report_runs(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):

    return service_reportes_ejecuciones.list_report_runs(current_user=current_user, db=db)


@router.get("/report-runs/{run_id}")
def get_report_run_status(
    run_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_reportes_ejecuciones.get_report_run_status(run_id=run_id, current_user=current_user, db=db)


@router.post("/report-runs/{run_id}/cancel")
def cancel_report_run(
    run_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_reportes_ejecuciones.cancel_report_run(run_id=run_id, current_user=current_user, db=db)


@router.post("/report-runs/{run_id}/retry")
def retry_report_run(
    run_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_reportes_ejecuciones.retry_report_run(run_id=run_id, current_user=current_user, db=db)


@router.get("/report-runs/{run_id}/download")
def download_report_run(
    run_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_reportes_ejecuciones.download_report_run(run_id=run_id, current_user=current_user, db=db)
