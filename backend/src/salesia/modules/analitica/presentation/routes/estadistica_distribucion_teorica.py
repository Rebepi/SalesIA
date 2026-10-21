from fastapi import APIRouter

import salesia.modules.analitica.application.estadistica_distribucion_teorica as service_estadistica_distribucion_teorica
from salesia.modules.analitica.application.contracts.estadistica_distribucion_teorica import (
    TheoreticalDistributionRequest,
)

router = APIRouter(prefix="")


@router.post("/statistics/theoretical-distribution")
def post_theoretical_distribution(payload: TheoreticalDistributionRequest):

    return service_estadistica_distribucion_teorica.post_theoretical_distribution(payload=payload)
