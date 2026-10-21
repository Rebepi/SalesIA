from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import salesia.modules.analitica.application.estadistica_descriptiva as service_estadistica_descriptiva
from salesia.modules.analitica.application.contracts.estadistica_descriptiva import (
    CompareRequest,
    DescriptiveSummaryRequest,
    MeanRequest,
    MedianRequest,
    WeightedMeanRequest,
)
from salesia.modules.seguridad.domain.identidad import AuthenticatedUser
from salesia.modules.seguridad.presentation.dependencies import get_current_user
from salesia.shared.infrastructure.database import get_db

router = APIRouter(prefix="")


@router.post("/statistics/mean")
async def post_mean(
    payload: MeanRequest, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return await service_estadistica_descriptiva.post_mean(payload=payload, current_user=current_user, db=db)


@router.post("/statistics/median")
async def post_median(
    payload: MedianRequest, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return await service_estadistica_descriptiva.post_median(payload=payload, current_user=current_user, db=db)


@router.post("/statistics/compare")
async def post_compare(
    payload: CompareRequest, current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)
):

    return await service_estadistica_descriptiva.post_compare(payload=payload, current_user=current_user, db=db)


@router.post("/statistics/descriptive-summary")
def post_descriptive_summary(
    payload: DescriptiveSummaryRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service_estadistica_descriptiva.post_descriptive_summary(payload=payload, current_user=current_user, db=db)


@router.post("/statistics/weighted-mean")
def post_weighted_mean(payload: WeightedMeanRequest, current_user: AuthenticatedUser = Depends(get_current_user)):

    return service_estadistica_descriptiva.post_weighted_mean(payload=payload, current_user=current_user)
