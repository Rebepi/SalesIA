from fastapi import APIRouter

import salesia.modules.analitica.application.analitica_demanda as service_analitica_demanda
from salesia.modules.analitica.application.contracts.analitica_demanda import DemandForecastCensoredRequest

router = APIRouter(prefix="")


@router.post("/analytics/demand-forecast")
def post_demand_forecast(payload: DemandForecastCensoredRequest):

    return service_analitica_demanda.post_demand_forecast(payload=payload)
