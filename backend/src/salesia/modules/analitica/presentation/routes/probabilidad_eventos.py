from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.probabilidad_eventos as service_probabilidad_eventos
from salesia.modules.analitica.application.contracts.probabilidad_eventos import (
    HypothesisTestRequest,
    OperationalLiveCountsRequest,
    PreregisterHypothesisRequest,
    ProbabilityEventsRequest,
    ScenarioCompareRequest,
    TemporalLeakageValidationRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/probability/events")
def post_probability_events(
    payload: ProbabilityEventsRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_probabilidad_eventos.post_probability_events(payload=payload, current_user=current_user, db=db)


@router.post("/probability/validate-temporal")
def post_validate_temporal(
    payload: TemporalLeakageValidationRequest, current_user: AuthenticatedUser = Depends(get_current_user)
):

    return service_probabilidad_eventos.post_validate_temporal(payload=payload, current_user=current_user)


@router.post("/probability/scenarios/compare")
def compare_probability_scenarios(
    payload: ScenarioCompareRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_probabilidad_eventos.compare_probability_scenarios(payload=payload, current_user=current_user, db=db)


@router.post("/probability/hypothesis-test")
def post_hypothesis_test(payload: HypothesisTestRequest, current_user: AuthenticatedUser = Depends(get_current_user)):

    return service_probabilidad_eventos.post_hypothesis_test(payload=payload, current_user=current_user)


@router.post("/probability/preregister-hypothesis")
def post_preregister_hypothesis(payload: PreregisterHypothesisRequest):

    return service_probabilidad_eventos.post_preregister_hypothesis(payload=payload)


@router.post("/probability/live-counts")
def get_operational_live_counts(
    payload: OperationalLiveCountsRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_probabilidad_eventos.get_operational_live_counts(payload=payload, current_user=current_user, db=db)
