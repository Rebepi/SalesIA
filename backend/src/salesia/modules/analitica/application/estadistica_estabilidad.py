from fastapi import HTTPException, status

from salesia.modules.analitica.application.contracts.estadistica_estabilidad import NumericalStabilityRequest
from salesia.modules.analitica.domain.advanced import verify_numerical_stability
from salesia.shared.domain.exceptions import EmptySampleException, InvariantViolationException


def post_numerical_stability(payload: NumericalStabilityRequest):
    try:
        return verify_numerical_stability(payload.values, oracle_comparison=payload.oracle_comparison)

    except (EmptySampleException, InvariantViolationException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
