from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.reportes_programacion as service_reportes_programacion
from salesia.modules.analitica.application.contracts.reportes_programacion import ReportScheduleCreateRequest
from salesia.modules.analitica.application.contracts.reportes_programacion import ReportScheduleUpdateRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.patch("/report-schedules/{schedule_id}")
def update_report_schedule(schedule_id: UUID, payload: ReportScheduleUpdateRequest, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return service_reportes_programacion.update_report_schedule(schedule_id, payload, current_user, db)


@router.post("/report-schedules", status_code=status.HTTP_201_CREATED)
def create_report_schedule(
    payload: ReportScheduleCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_reportes_programacion.create_report_schedule(payload=payload, current_user=current_user, db=db)


@router.post("/report-schedules/{schedule_id}/execute")
def execute_report_schedule(
    schedule_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_reportes_programacion.execute_report_schedule(
        schedule_id=schedule_id, current_user=current_user, db=db
    )


@router.get("/report-schedules")
def list_report_schedules(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):

    return service_reportes_programacion.list_report_schedules(current_user=current_user, db=db)


@router.delete("/report-schedules/{schedule_id}")
def delete_report_schedule(
    schedule_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_reportes_programacion.delete_report_schedule(
        schedule_id=schedule_id, current_user=current_user, db=db
    )
