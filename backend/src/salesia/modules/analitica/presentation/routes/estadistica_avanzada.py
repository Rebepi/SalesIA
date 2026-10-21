from fastapi import APIRouter

import salesia.modules.analitica.application.estadistica_avanzada as service_estadistica_avanzada
from salesia.modules.analitica.application.contracts.estadistica_avanzada import AdvancedStatisticsRequest

router = APIRouter(prefix="")


@router.post("/statistics/advanced")
def post_advanced_statistics(payload: AdvancedStatisticsRequest):

    return service_estadistica_avanzada.post_advanced_statistics(payload=payload)
