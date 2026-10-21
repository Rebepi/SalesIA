from fastapi import HTTPException, status

from salesia.modules.analitica.application.contracts.estadistica_desviacion import StdevDetailedRequest
from salesia.modules.analitica.domain.advanced import calculate_stdev_detailed
from salesia.shared.domain.exceptions import EmptySampleException, InvariantViolationException


def post_stdev(payload: StdevDetailedRequest):
    try:
        res = calculate_stdev_detailed(payload.values, is_sample=payload.is_sample, variable_unit=payload.variable_unit)

        return {**res, "standard_deviation": str(res["standard_deviation"]), "variance": str(res["variance"])}

    except (EmptySampleException, InvariantViolationException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
