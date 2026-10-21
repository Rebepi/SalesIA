from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Optional

from salesia.shared.domain.exceptions import InvariantViolationException


def calculate_mathematical_expectation(
    values: list[Decimal],
    probabilities: list[Decimal],
    is_continuous: bool = False,
    support: Optional[tuple[Decimal, Decimal]] = None,
) -> dict[str, Any]:
    if not values or not probabilities:
        raise InvariantViolationException("Los valores y probabilidades no pueden estar vacios")
    if len(values) != len(probabilities):
        raise InvariantViolationException("La cantidad de valores debe coincidir con la cantidad de probabilidades")

    for p in probabilities:
        if p < Decimal("0") or p > Decimal("1"):
            raise InvariantViolationException("Cada probabilidad p_i debe encontrarse en el intervalo [0, 1]")

    sum_probs = sum(probabilities, Decimal("0"))
    if abs(sum_probs - Decimal("1")) > Decimal("0.00001"):
        raise InvariantViolationException(f"La suma de probabilidades ({sum_probs}) debe ser igual a 1.0")

    ev = sum((v * p for v, p in zip(values, probabilities)), Decimal("0"))
    ev_rounded = ev.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    return {
        "expected_value": ev_rounded,
        "is_continuous": is_continuous,
        "support": [str(support[0]), str(support[1])] if support else [str(min(values)), str(max(values))],
        "valid_probabilities": True,
        "probabilities_sum": sum_probs.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN),
        "method": "riemann_quadrature" if is_continuous else "discrete_weighted_sum",
    }
