from fastapi import HTTPException, status

from salesia.modules.analitica.application.contracts.estadistica_avanzada import AdvancedStatisticsRequest
from salesia.modules.analitica.domain.statistics import (
    calculate_quantiles,
    calculate_stdev,
    calculate_variance,
    compute_statistical_summary,
)
from salesia.shared.domain.exceptions import EmptySampleException


def post_advanced_statistics(payload: AdvancedStatisticsRequest):
    try:
        summary = compute_statistical_summary(payload.values)

        var = calculate_variance(payload.values, payload.is_sample)

        stdev = calculate_stdev(payload.values, payload.is_sample)

        quantiles = calculate_quantiles(payload.values)

        return {
            "count": summary.count,
            "mean": str(summary.mean),
            "median": str(summary.median),
            "minimum": str(summary.minimum),
            "maximum": str(summary.maximum),
            "variance": str(var),
            "standard_deviation": str(stdev),
            "is_sample": payload.is_sample,
            "q1": str(quantiles["q1"]),
            "q3": str(quantiles["q3"]),
            "iqr": str(quantiles["iqr"]),
            "lower_fence": str(quantiles["lower_fence"]),
            "upper_fence": str(quantiles["upper_fence"]),
            "outliers": [str(x) for x in quantiles["outliers"]],
            "outliers_count": len(quantiles["outliers"]),
            "skewness": summary.skewness_direction,
        }

    except EmptySampleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
