from fastapi import HTTPException, status

from salesia.modules.analitica.application.contracts.estadistica_comparacion_grupos import GroupsTestRequest
from salesia.modules.analitica.domain.advanced import run_two_groups_test_detailed
from salesia.shared.domain.exceptions import EmptySampleException, InvariantViolationException


def post_groups_test(payload: GroupsTestRequest):
    try:
        res = run_two_groups_test_detailed(
            group_a=payload.group_a,
            group_b=payload.group_b,
            paired=payload.paired,
            alternative=payload.alternative,
            equal_var=payload.equal_var,
            preregistered=payload.preregistered,
        )

        return {**res, "p_value": str(res["p_value"])}

    except (EmptySampleException, InvariantViolationException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
