from fastapi import APIRouter

import salesia.modules.analitica.application.analitica_resumen as service_analitica_resumen
from salesia.modules.analitica.application.contracts.estadistica_descriptiva import MeanRequest

router = APIRouter(prefix="")


@router.post("/analytics/summary")
def post_analytics_summary_compat(payload: MeanRequest):

    return service_analitica_resumen.post_analytics_summary_compat(payload=payload)
