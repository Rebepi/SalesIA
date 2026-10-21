from fastapi import APIRouter

import salesia.modules.analitica.application.estadistica_esperanza as service_estadistica_esperanza
from salesia.modules.analitica.application.contracts.estadistica_esperanza import MathExpectationRequest

router = APIRouter(prefix="")


@router.post("/statistics/mathematical-expectation")
def post_mathematical_expectation(payload: MathExpectationRequest):

    return service_estadistica_esperanza.post_mathematical_expectation(payload=payload)
