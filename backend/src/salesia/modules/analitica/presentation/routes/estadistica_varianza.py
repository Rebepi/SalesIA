from fastapi import APIRouter

import salesia.modules.analitica.application.estadistica_varianza as service_estadistica_varianza
from salesia.modules.analitica.application.contracts.estadistica_varianza import VarianceDetailedRequest

router = APIRouter(prefix="")


@router.post("/statistics/variance")
def post_variance(payload: VarianceDetailedRequest):

    return service_estadistica_varianza.post_variance(payload=payload)
