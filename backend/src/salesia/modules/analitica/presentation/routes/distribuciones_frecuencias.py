from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.distribuciones_frecuencias as service_distribuciones_frecuencias
from salesia.modules.analitica.application.contracts.distribuciones_frecuencias import (
    DistributionRequest,
    FrequenciesRequest,
    OutliersAnalysisRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/statistics/frequencies")
def post_frequencies(
    payload: FrequenciesRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_distribuciones_frecuencias.post_frequencies(payload=payload, current_user=current_user, db=db)


@router.post("/statistics/distribution")
def post_distribution(
    payload: DistributionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_distribuciones_frecuencias.post_distribution(payload=payload, current_user=current_user, db=db)


@router.post("/statistics/outliers")
def post_outliers(payload: OutliersAnalysisRequest, current_user: AuthenticatedUser = Depends(get_current_user)):

    return service_distribuciones_frecuencias.post_outliers(payload=payload, current_user=current_user)
