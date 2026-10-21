from fastapi import APIRouter

import salesia.modules.analitica.application.estadistica_efecto as service_estadistica_efecto
from salesia.modules.analitica.application.contracts.estadistica_efecto import EffectSizeRequest

router = APIRouter(prefix="")


@router.post("/statistics/effect-size")
def post_effect_size(payload: EffectSizeRequest):

    return service_estadistica_efecto.post_effect_size(payload=payload)
