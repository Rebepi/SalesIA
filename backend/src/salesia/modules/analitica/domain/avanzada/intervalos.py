import math
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

import scipy.stats as sp_stats

from salesia.modules.analitica.domain.statistics import calculate_mean, calculate_stdev
from salesia.shared.domain.exceptions import InvariantViolationException


def calculate_confidence_interval_detailed(
    values: list[Decimal], confidence_level: Decimal = Decimal("0.95"), method: str = "student_t"
) -> dict[str, Any]:
    if not values or len(values) < 2:
        raise InvariantViolationException("Se requieren al menos 2 observaciones para calcular intervalos de confianza")
    if not (Decimal("0.50") < confidence_level < Decimal("0.9999")):
        raise InvariantViolationException("Nivel de confianza fuera de rango [0.50, 0.9999]")

    n = len(values)
    mean_d = calculate_mean(values)
    std_d = calculate_stdev(values, is_sample=True)

    alpha = 1.0 - float(confidence_level)
    df = n - 1
    se = float(std_d) / math.sqrt(n)

    if method == "normal_z":
        crit = float(sp_stats.norm.ppf(1.0 - alpha / 2.0))
    else:
        method = "student_t"
        crit = float(sp_stats.t.ppf(1.0 - alpha / 2.0, df=df))

    margin = crit * se
    low = float(mean_d) - margin
    high = float(mean_d) + margin

    return {
        "parameter": "mean",
        "method": method,
        "confidence_level": confidence_level,
        "point_estimate": mean_d,
        "standard_error": se,
        "degrees_of_freedom": df,
        "margin_of_error": margin,
        "lower_bound": Decimal(str(low)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN),
        "upper_bound": Decimal(str(high)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN),
        "assumptions": "Muestreo aleatorio simple e independencia de observaciones",
        "didactic_disclaimer": (
            f"El intervalo al {confidence_level * 100}% indica que bajo muestreo repetido identico el "
            f"{confidence_level * 100}% de los intervalos cubririan la media real; no interpretar como probabilidad "
            "posterior subjetiva del parametro fijo."
        ),
    }
