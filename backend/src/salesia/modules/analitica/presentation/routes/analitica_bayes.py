from fastapi import APIRouter

import salesia.modules.analitica.application.analitica_bayes as service_analitica_bayes
from salesia.modules.analitica.application.contracts.probabilidad_bayes import BayesCalculationRequest

router = APIRouter(prefix="")


@router.post("/analytics/bayes")
def post_analytics_bayes_compat(payload: BayesCalculationRequest):

    return service_analitica_bayes.post_analytics_bayes_compat(payload=payload)
