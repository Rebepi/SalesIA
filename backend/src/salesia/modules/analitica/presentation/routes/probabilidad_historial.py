from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.probabilidad_historial as service_probabilidad_historial
from salesia.modules.analitica.application.contracts.probabilidad_historial import (
    DuplicateScenarioRequest,
    ProbabilityAnalysisSaveRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/probability/analyses")
def post_probability_analysis_save(
    payload: ProbabilityAnalysisSaveRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_probabilidad_historial.post_probability_analysis_save(
        payload=payload, current_user=current_user, db=db
    )


@router.get("/probability/analyses")
def list_probability_analyses(
    current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_probabilidad_historial.list_probability_analyses(current_user=current_user, db=db)


@router.get("/probability/analyses/{analysis_id}")
def get_probability_analysis(
    analysis_id: UUID, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_probabilidad_historial.get_probability_analysis(
        analysis_id=analysis_id, current_user=current_user, db=db
    )


@router.post("/probability/analyses/{analysis_id}/duplicate-scenario")
def duplicate_probability_scenario(
    analysis_id: UUID,
    payload: DuplicateScenarioRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_probabilidad_historial.duplicate_probability_scenario(
        analysis_id=analysis_id, payload=payload, current_user=current_user, db=db
    )
