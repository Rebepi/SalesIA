from fastapi import HTTPException, status

from salesia.modules.analitica.application.contracts.estadistica_efecto import EffectSizeRequest
from salesia.modules.analitica.domain.advanced import calculate_effect_size_detailed
from salesia.shared.domain.exceptions import EmptySampleException, InvariantViolationException


def post_effect_size(payload: EffectSizeRequest):
    try:
        res = calculate_effect_size_detailed(payload.group_a, payload.group_b)

        return {**res, "cohens_d": str(res["cohens_d"]), "practical_difference": str(res["practical_difference"])}

    except (EmptySampleException, InvariantViolationException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
