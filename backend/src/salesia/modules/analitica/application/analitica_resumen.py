from fastapi import HTTPException, status

from salesia.modules.analitica.application.contracts.estadistica_descriptiva import MeanRequest
from salesia.modules.analitica.domain.statistics import compute_statistical_summary
from salesia.shared.domain.exceptions import EmptySampleException


def post_analytics_summary_compat(payload: MeanRequest):
    try:
        res = compute_statistical_summary(payload.values)

        return {
            "count": res.count,
            "mean": str(res.mean),
            "median": str(res.median),
            "minimum": str(res.minimum),
            "maximum": str(res.maximum),
            "sum_total": str(res.sum_total),
            "skewness_direction": res.skewness_direction,
        }

    except EmptySampleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
