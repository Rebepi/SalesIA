from fastapi import HTTPException, status

from salesia.modules.analitica.application.contracts.estadistica_distribucion_teorica import (
    TheoreticalDistributionRequest,
)
from salesia.modules.analitica.domain.advanced import evaluate_distribution_fit
from salesia.shared.domain.exceptions import EmptySampleException, InvariantViolationException


def post_theoretical_distribution(payload: TheoreticalDistributionRequest):
    try:
        return evaluate_distribution_fit(payload.values, candidate_family=payload.candidate_family)

    except (EmptySampleException, InvariantViolationException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
