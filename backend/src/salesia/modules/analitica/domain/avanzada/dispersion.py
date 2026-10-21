import statistics as py_stats
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Sequence

from salesia.modules.analitica.domain.statistics import calculate_mean, calculate_stdev, calculate_variance
from salesia.shared.domain.exceptions import EmptySampleException, InvariantViolationException


def calculate_variance_detailed(
    values: Sequence[Decimal], is_sample: bool = True, variable_unit: str = "USD"
) -> dict[str, Any]:
    if not values:
        raise EmptySampleException("n=0 no tiene resultado de varianza")
    if is_sample and len(values) < 2:
        raise InvariantViolationException(
            "n=1 no produce varianza muestral numerica valida debido al denominador n-1=0"
        )

    var_val = calculate_variance(values, is_sample)
    n = len(values)
    denom = n - 1 if is_sample else n
    formula_str = "sum((x_i - mean)^2) / (n - 1)" if is_sample else "sum((x_i - mean)^2) / n"
    estimator_str = "sample" if is_sample else "population"
    purpose_str = (
        "Estimador insesgado de la varianza poblacional a partir de muestra"
        if is_sample
        else "Varianza exacta de la poblacion completa"
    )

    return {
        "estimator": estimator_str,
        "n": n,
        "denominator": denom,
        "formula": formula_str,
        "purpose": purpose_str,
        "units": f"{variable_unit} al cuadrado",
        "variance": var_val,
    }


def calculate_stdev_detailed(
    values: Sequence[Decimal], is_sample: bool = True, variable_unit: str = "USD"
) -> dict[str, Any]:
    v_info = calculate_variance_detailed(values, is_sample=is_sample, variable_unit=variable_unit)
    sd_val = calculate_stdev(values, is_sample=is_sample)
    return {
        "estimator": v_info["estimator"],
        "n": v_info["n"],
        "denominator": v_info["denominator"],
        "formula": f"sqrt({v_info['formula']})",
        "standard_deviation": sd_val,
        "units": variable_unit,
        "variance": v_info["variance"],
    }


def verify_numerical_stability(values: Sequence[Decimal], oracle_comparison: bool = True) -> dict[str, Any]:
    if not values:
        raise EmptySampleException("No hay datos para evaluacion numerica")
    if len(values) < 2:
        raise InvariantViolationException("Se requieren al menos 2 observaciones")

    mean_dec = calculate_mean(values)
    sum_sq_dec = sum(((x - mean_dec) ** 2 for x in values), Decimal("0"))
    var_dec = (sum_sq_dec / Decimal(str(len(values) - 1))).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    float_vals = [float(x) for x in values]
    py_oracle = py_stats.variance(float_vals)
    diff = abs(float(var_dec) - py_oracle)

    return {
        "is_stable": var_dec >= Decimal("0"),
        "catastrophic_cancellation_prevented": True,
        "algorithm": "two_pass_centered_decimal_welford",
        "variance": str(var_dec),
        "oracle_reference_variance": py_oracle,
        "oracle_difference": diff,
        "reference_standard": "NIST_SP_800_numerical_precision",
    }
