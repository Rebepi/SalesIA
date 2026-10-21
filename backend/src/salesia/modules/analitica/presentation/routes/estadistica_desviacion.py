from fastapi import APIRouter

import salesia.modules.analitica.application.estadistica_desviacion as service_estadistica_desviacion
from salesia.modules.analitica.application.contracts.estadistica_desviacion import StdevDetailedRequest

router = APIRouter(prefix="")


@router.post("/statistics/stdev")
def post_stdev(payload: StdevDetailedRequest):

    return service_estadistica_desviacion.post_stdev(payload=payload)
