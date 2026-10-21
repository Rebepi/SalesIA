from fastapi import HTTPException, status

from salesia.modules.analitica.application.contracts.estadistica_esperanza import MathExpectationRequest
from salesia.modules.analitica.domain.advanced import calculate_mathematical_expectation
from salesia.shared.domain.exceptions import InvariantViolationException


def post_mathematical_expectation(payload: MathExpectationRequest):
    try:
        res = calculate_mathematical_expectation(
            payload.values, payload.probabilities, is_continuous=payload.is_continuous
        )

        return {**res, "expected_value": str(res["expected_value"]), "probabilities_sum": str(res["probabilities_sum"])}

    except InvariantViolationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
