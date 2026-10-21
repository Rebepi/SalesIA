from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.probabilidad_bayes as service_probabilidad_bayes
from salesia.modules.analitica.application.contracts.probabilidad_bayes import (
    BayesCalculationRequest,
    SmoothedBayesRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/probability/bayes")
def post_probability_bayes(
    payload: BayesCalculationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_probabilidad_bayes.post_probability_bayes(payload=payload, current_user=current_user, db=db)


@router.post("/probability/smoothed-bayes")
def post_smoothed_bayes(payload: SmoothedBayesRequest):

    return service_probabilidad_bayes.post_smoothed_bayes(payload=payload)
