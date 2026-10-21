from decimal import Decimal
from typing import Any, Optional

import numpy as np
import scipy.stats as sp_stats

from salesia.shared.domain.exceptions import EmptySampleException, InvariantViolationException


def evaluate_distribution_fit(values: list[Decimal], candidate_family: Optional[str] = "normal") -> dict[str, Any]:
    if not values:
        raise EmptySampleException("No hay observaciones para evaluar distribucion")
    n = len(values)
    if n < 3:
        raise InvariantViolationException("Se requieren al menos 3 observaciones")

    float_vals = np.array([float(x) for x in values])
    mean_val = float(np.mean(float_vals))
    std_val = float(np.std(float_vals, ddof=1)) if n > 1 else 0.0
    skewness = float(sp_stats.skew(float_vals))
    kurtosis = float(sp_stats.kurtosis(float_vals))

    if n <= 5000:
        stat_w, p_val = sp_stats.shapiro(float_vals)
        test_used = "shapiro_wilk"
    else:
        stat_w, p_val = sp_stats.jarque_bera(float_vals)
        test_used = "jarque_bera"

    normality_rejected = bool(p_val < 0.05 or abs(skewness) > 1.0 or abs(kurtosis) > 2.0)
    family_assigned = "normal" if not normality_rejected else "asymmetric_empirical"

    return {
        "distribution_family": family_assigned,
        "has_mean": True,
        "assumed_normal_by_default": False,
        "normality_rejected": normality_rejected,
        "parameters": {"mean": mean_val, "stdev": std_val, "skewness": skewness, "kurtosis": kurtosis},
        "support": "real_line_R" if not normality_rejected else "non_negative_half_line",
        "goodness_of_fit_test": test_used,
        "test_statistic": float(stat_w),
        "p_value": float(p_val),
        "didactic_warning": (
            "No se asume normalidad solo porque exista una media calculable. "
            "La asimetria o el rechazo de la prueba obligan a modelar con frecuencias empiricas o distribuciones pesadas."
        ),
    }
