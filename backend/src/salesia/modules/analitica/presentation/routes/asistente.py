from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.asistente as service_asistente
from salesia.modules.analitica.application.contracts.asistente import (
    AiQueryRequest,
    AiSimulationRequest,
    EmergencyPauseRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/ai/query")
def post_ai_query(
    payload: AiQueryRequest, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return service_asistente.post_ai_query(payload=payload, current_user=current_user, db=db)


@router.post("/ai/simulate-action")
def post_simulate_action(payload: AiSimulationRequest, current_user: AuthenticatedUser = Depends(get_current_user)):

    return service_asistente.post_simulate_action(payload=payload, current_user=current_user)


@router.post("/ai/emergency-pause")
def post_emergency_pause(
    payload: EmergencyPauseRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_asistente.post_emergency_pause(payload=payload, current_user=current_user, db=db)


@router.post("/ai/resume")
def post_ai_resume(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)):

    return service_asistente.post_ai_resume(current_user=current_user, db=db)
