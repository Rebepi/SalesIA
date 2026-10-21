from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.reportes_catalogo as service_reportes_catalogo
from salesia.modules.analitica.application.contracts.reportes_catalogo import ReportCompareRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/reports")
def list_reports(
    area: Optional[str] = Query(default=None),
    format: Optional[str] = Query(default=None),
    current_user: AuthenticatedUser = Depends(get_current_user),
):

    return service_reportes_catalogo.list_reports(area=area, format=format, current_user=current_user)


@router.get("/reports/preview")
def get_report_preview(
    report_type: Optional[str] = Query(default=None, min_length=2),
    template_code: Optional[str] = Query(default=None, min_length=2),
    limit: int = Query(default=20, ge=1, le=20),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_reportes_catalogo.get_report_preview(
        report_type=report_type, template_code=template_code, limit=limit, current_user=current_user, db=db
    )


@router.post("/reports/compare")
def compare_reports(
    payload: ReportCompareRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_reportes_catalogo.compare_reports(payload=payload, current_user=current_user, db=db)


@router.get("/reports/branding")
def get_report_branding(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):

    return service_reportes_catalogo.get_report_branding(current_user=current_user, db=db)
