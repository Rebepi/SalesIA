from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.historial as service_historial
from salesia.modules.analitica.application.contracts.historial import AnalysisCreateRequest, AnalysisRepeatRequest
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/analyses", status_code=status.HTTP_201_CREATED)
def create_analysis(
    payload: AnalysisCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_historial.create_analysis(payload=payload, current_user=current_user, db=db)


@router.get("/analyses")
def list_analyses(
    dataset_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_historial.list_analyses(
        dataset_id=dataset_id, status_filter=status_filter, limit=limit, offset=offset, current_user=current_user, db=db
    )


@router.get("/analyses/{analysis_id}")
def get_analysis(
    analysis_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_historial.get_analysis(analysis_id=analysis_id, current_user=current_user, db=db)


@router.post("/analyses/{analysis_id}/repeat")
def repeat_analysis(
    analysis_id: UUID,
    payload: Optional[AnalysisRepeatRequest] = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_historial.repeat_analysis(analysis_id=analysis_id, payload=payload, current_user=current_user, db=db)


@router.post("/analyses/{analysis_id}/cancel")
def cancel_analysis(
    analysis_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_historial.cancel_analysis(analysis_id=analysis_id, current_user=current_user, db=db)
