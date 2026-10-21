from fastapi import APIRouter

import salesia.modules.analitica.application.analitica_anomalias as service_analitica_anomalias
from salesia.modules.analitica.application.contracts.analitica_anomalias import AnomalyDetectionRequest

router = APIRouter(prefix="")


@router.post("/analytics/anomaly-detection")
def post_anomaly_detection(payload: AnomalyDetectionRequest):

    return service_analitica_anomalias.post_anomaly_detection(payload=payload)
