from fastapi import APIRouter

import salesia.modules.analitica.application.estadistica_estabilidad as service_estadistica_estabilidad
from salesia.modules.analitica.application.contracts.estadistica_estabilidad import NumericalStabilityRequest

router = APIRouter(prefix="")


@router.post("/statistics/numerical-stability")
def post_numerical_stability(payload: NumericalStabilityRequest):

    return service_estadistica_estabilidad.post_numerical_stability(payload=payload)
