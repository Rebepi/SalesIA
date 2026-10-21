from fastapi import APIRouter

import salesia.modules.analitica.application.analitica_series_temporales as service_analitica_series_temporales
from salesia.modules.analitica.application.contracts.analitica_series_temporales import TimeSeriesSplitRequest

router = APIRouter(prefix="")


@router.post("/analytics/time-series")
def post_time_series(payload: TimeSeriesSplitRequest):

    return service_analitica_series_temporales.post_time_series(payload=payload)
