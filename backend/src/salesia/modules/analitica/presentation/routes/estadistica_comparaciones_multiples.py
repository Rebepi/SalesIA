from fastapi import APIRouter

import salesia.modules.analitica.application.estadistica_comparaciones_multiples as service_estadistica_comparaciones_multiples
from salesia.modules.analitica.application.contracts.estadistica_comparaciones_multiples import (
    MultipleComparisonsRequest,
)

router = APIRouter(prefix="")


@router.post("/statistics/multiple-comparisons")
def post_multiple_comparisons(payload: MultipleComparisonsRequest):

    return service_estadistica_comparaciones_multiples.post_multiple_comparisons(payload=payload)
