from fastapi import APIRouter

import salesia.modules.analitica.application.estadistica_intervalos as service_estadistica_intervalos
from salesia.modules.analitica.application.contracts.estadistica_intervalos import ConfidenceIntervalRequest

router = APIRouter(prefix="")


@router.post("/statistics/confidence-interval")
def post_confidence_interval(payload: ConfidenceIntervalRequest):

    return service_estadistica_intervalos.post_confidence_interval(payload=payload)
