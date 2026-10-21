from fastapi import HTTPException, status

from salesia.modules.analitica.application.contracts.estadistica_intervalos import ConfidenceIntervalRequest
from salesia.modules.analitica.domain.advanced import calculate_confidence_interval_detailed
from salesia.shared.domain.exceptions import InvariantViolationException


def post_confidence_interval(payload: ConfidenceIntervalRequest):
    try:
        res = calculate_confidence_interval_detailed(
            payload.values, confidence_level=payload.confidence_level, method=payload.method
        )

        return {
            **res,
            "confidence_level": str(res["confidence_level"]),
            "point_estimate": str(res["point_estimate"]),
            "lower_bound": str(res["lower_bound"]),
            "upper_bound": str(res["upper_bound"]),
        }

    except InvariantViolationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
