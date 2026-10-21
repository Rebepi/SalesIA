from fastapi import HTTPException, status

from salesia.modules.analitica.application.contracts.estadistica_varianza import VarianceDetailedRequest
from salesia.modules.analitica.domain.advanced import calculate_variance_detailed
from salesia.shared.domain.exceptions import EmptySampleException, InvariantViolationException


def post_variance(payload: VarianceDetailedRequest):
    try:
        res = calculate_variance_detailed(
            payload.values, is_sample=payload.is_sample, variable_unit=payload.variable_unit
        )

        return {**res, "variance": str(res["variance"])}

    except (EmptySampleException, InvariantViolationException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
