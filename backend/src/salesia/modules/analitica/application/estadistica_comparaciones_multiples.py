from fastapi import HTTPException, status

from salesia.modules.analitica.application.contracts.estadistica_comparaciones_multiples import (
    MultipleComparisonsRequest,
)
from salesia.modules.analitica.domain.advanced import adjust_multiple_comparisons_detailed
from salesia.shared.domain.exceptions import InvariantViolationException


def post_multiple_comparisons(payload: MultipleComparisonsRequest):
    try:
        res = adjust_multiple_comparisons_detailed(payload.p_values, method=payload.method, alpha=payload.alpha)

        return {**res, "adjusted_alpha": str(res["adjusted_alpha"]), "fwer_unadjusted": str(res["fwer_unadjusted"])}

    except InvariantViolationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
