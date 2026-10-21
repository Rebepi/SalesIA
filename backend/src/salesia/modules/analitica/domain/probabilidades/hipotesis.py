import math
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from salesia.shared.domain.exceptions import EmptySampleException, InvariantViolationException


def run_two_proportions_hypothesis_test(
    count_1: int, total_1: int, count_2: int, total_2: int, confidence_level: Decimal = Decimal("0.95")
) -> dict[str, Any]:
    if total_1 <= 0 or total_2 <= 0:
        raise EmptySampleException(
            "Los tamanos de muestra deben ser estrictamente positivos para la prueba de hipotesis"
        )
    if count_1 < 0 or count_1 > total_1 or count_2 < 0 or count_2 > total_2:
        raise InvariantViolationException("Los recuentos observados no pueden exceder los totales muestrales")

    p1 = Decimal(str(count_1)) / Decimal(str(total_1))
    p2 = Decimal(str(count_2)) / Decimal(str(total_2))
    p_pool = (Decimal(str(count_1 + count_2))) / Decimal(str(total_1 + total_2))
    q_pool = Decimal("1") - p_pool

    se_pool = p_pool * q_pool * (Decimal("1") / Decimal(str(total_1)) + Decimal("1") / Decimal(str(total_2)))
    se_pool_float = float(se_pool) ** 0.5

    diff = float(p1 - p2)
    if se_pool_float > 0:
        z_score = diff / se_pool_float
    else:
        z_score = 0.0

    p_value = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(z_score) / (2.0**0.5))))
    p_val_dec = Decimal(str(p_value)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    se_diff_float = (float(p1 * (1 - p1) / Decimal(str(total_1)) + p2 * (1 - p2) / Decimal(str(total_2)))) ** 0.5
    z_critical = 1.95996
    ci_low = diff - (z_critical * se_diff_float)
    ci_high = diff + (z_critical * se_diff_float)

    assumptions_ok = count_1 >= 5 and (total_1 - count_1) >= 5 and count_2 >= 5 and (total_2 - count_2) >= 5

    reject_null = p_value < float(Decimal("1") - confidence_level)
    decision = (
        "Rechazar H0: diferencia estadisticamente significativa"
        if reject_null
        else "No rechazar H0: no hay evidencia suficiente de diferencia"
    )

    return {
        "test_type": "two_proportions_z_test",
        "h0_statement": "H0: p1 = p2 (Las proporciones de ambos grupos son iguales)",
        "h1_statement": "H1: p1 != p2 (Las proporciones difieren)",
        "sample_1_proportion": str(p1.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)),
        "sample_2_proportion": str(p2.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)),
        "difference": str(Decimal(str(diff)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)),
        "z_statistic": f"{z_score:.4f}",
        "p_value": str(p_val_dec),
        "confidence_level": str(confidence_level),
        "confidence_interval_diff_low": f"{ci_low:.6f}",
        "confidence_interval_diff_high": f"{ci_high:.6f}",
        "expected_value_group_1": str(count_1),
        "expected_value_group_2": str(count_2),
        "assumptions_met": assumptions_ok,
        "assumptions_detail": {"min_success_failure_count_met": assumptions_ok, "threshold_required": 5},
        "decision": decision,
        "didactic_explanation": (
            f"El p-valor ({p_val_dec}) es la probabilidad de observar una diferencia muestral tan o mas extrema "
            "asumiendo que la hipotesis nula H0 es verdadera. NO representa la probabilidad de que la hipotesis "
            "nula o alternativa sea cierta."
        ),
    }
