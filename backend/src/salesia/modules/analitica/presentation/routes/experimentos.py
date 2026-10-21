from fastapi import APIRouter

import salesia.modules.analitica.application.experimentos as service_experimentos
from salesia.modules.analitica.application.contracts.experimentos import ABExperimentRequest

router = APIRouter(prefix="")


@router.post("/experiments/ab-test")
def post_ab_test(payload: ABExperimentRequest):

    return service_experimentos.post_ab_test(payload=payload)
