from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.dashboard as service_dashboard
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.get("/dashboard/summary")
def get_dashboard_summary(
    period: str = "30d",
    branch_id: Optional[UUID] = None,
    currency: Optional[str] = None,
    seller_id: Optional[UUID] = None,
    category: Optional[str] = None,
    zone: Optional[str] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_dashboard.get_dashboard_summary(
        period=period,
        branch_id=branch_id,
        currency=currency,
        seller_id=seller_id,
        category=category,
        zone=zone,
        current_user=current_user,
        db=db,
    )


@router.get("/dashboard/evidence")
def get_dashboard_evidence(
    key: str,
    as_of: datetime,
    period: str = "30d",
    branch_id: Optional[UUID] = None,
    currency: Optional[str] = None,
    category: Optional[str] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return service_dashboard.get_dashboard_summary(period=period, branch_id=branch_id, currency=currency, seller_id=None, category=category, zone=None, current_user=current_user, db=db, evidence_key=key, as_of=as_of)


@router.get("/dashboard/export")
def export_dashboard(
    as_of: datetime,
    period: str = "30d",
    branch_id: Optional[UUID] = None,
    currency: Optional[str] = None,
    category: Optional[str] = None,
    granularity: str = "day",
    visible_panels: Optional[str] = None,
    expected_revenue: Optional[str] = None,
    expected_documents: Optional[int] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from salesia.modules.analitica.application.exportacion_dashboard import build_export
    payload, report = build_export(db, current_user, period, branch_id, currency, category, as_of, granularity, visible_panels, expected_revenue, expected_documents)
    filename = report["filename"]
    return Response(content=payload, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{filename}"', "Cache-Control": "no-store"})
