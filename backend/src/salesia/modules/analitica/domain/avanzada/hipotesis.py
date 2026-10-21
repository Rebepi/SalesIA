import math
from datetime import datetime, timezone
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Optional

import numpy as np
import scipy.stats as sp_stats

from salesia.shared.domain.exceptions import EmptySampleException, InvariantViolationException


def preregister_hypothesis(
    hypothesis_id: str,
    h0: str,
    h1: str,
    variable: str,
    group_a: str,
    group_b: str,
    direction: str = "two_sided",
    alpha: Decimal = Decimal("0.05"),
    test_type: str = "welch_t",
) -> dict[str, Any]:
    if direction not in ("two_sided", "greater", "less"):
        raise InvariantViolationException("Direccion de hipotesis invalida: use two_sided, greater o less")
    if not (Decimal("0") < alpha < Decimal("0.5")):
        raise InvariantViolationException("Nivel de significancia alpha fuera de rango")

    return {
        "hypothesis_id": hypothesis_id,
        "h0": h0,
        "h1": h1,
        "variable": variable,
        "group_a": group_a,
        "group_b": group_b,
        "direction": direction,
        "alpha": str(alpha),
        "test_type": test_type,
        "preregistered": True,
        "is_confirmatory": True,
        "status": "preregistered_active",
        "preregistered_at": datetime.now(timezone.utc).isoformat(),
    }


def run_two_groups_test_detailed(
    group_a: list[Decimal],
    group_b: list[Decimal],
    paired: bool = False,
    alternative: str = "two-sided",
    equal_var: Optional[bool] = None,
    preregistered: bool = True,
) -> dict[str, Any]:
    if not group_a or not group_b:
        raise EmptySampleException("Ambos grupos deben contener observaciones")

    na, nb = len(group_a), len(group_b)
    if paired:
        if na != nb:
            raise InvariantViolationException(
                "Para prueba pareada ambos grupos deben tener exactamente el mismo tamano"
            )

    fa = [float(x) for x in group_a]
    fb = [float(x) for x in group_b]

    alt_scipy = alternative
    if alternative == "two_sided":
        alt_scipy = "two-sided"

    if paired:
        res = sp_stats.ttest_rel(fa, fb, alternative=alt_scipy)
        df_val = float(na - 1)
        test_name = "paired_t_test"
        validity = "Observaciones pareadas con diferencias continuas"
    else:
        if equal_var is None:
            _, lev_p = sp_stats.levene(fa, fb)
            equal_var = bool(lev_p > 0.05)

        res = sp_stats.ttest_ind(fa, fb, equal_var=equal_var, alternative=alt_scipy)
        test_name = "student_t_test" if equal_var else "welch_t_test"
        if equal_var:
            df_val = float(na + nb - 2)
        else:
            sa2 = np.var(fa, ddof=1)
            sb2 = np.var(fb, ddof=1)
            num = (sa2 / na + sb2 / nb) ** 2
            den = ((sa2 / na) ** 2) / (na - 1) + ((sb2 / nb) ** 2) / (nb - 1)
            df_val = float(num / den) if den > 0 else float(na + nb - 2)
        validity = "Muestras independientes con varianzas tratadas sin asumir homogeneidad forzada"

    stat_val = float(res.statistic)
    p_val = float(res.pvalue)

    return {
        "test_name": test_name,
        "is_paired": paired,
        "statistic": stat_val,
        "degrees_of_freedom": df_val,
        "p_value": Decimal(str(p_val)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN),
        "validity_conditions": validity,
        "preregistered": preregistered,
        "didactic_p_value_explanation": (
            f"El p-valor ({p_val:.6f}) mide la probabilidad de datos tan extremos o mas bajo H0. "
            "No es la probabilidad de que H0 sea verdadera ni de que la hipotesis alternativa lo sea."
        ),
    }


def calculate_effect_size_detailed(group_a: list[Decimal], group_b: list[Decimal]) -> dict[str, Any]:
    if not group_a or not group_b:
        raise EmptySampleException("Ambos grupos deben contener observaciones")

    na, nb = len(group_a), len(group_b)
    fa = [float(x) for x in group_a]
    fb = [float(x) for x in group_b]

    ma, mb = np.mean(fa), np.mean(fb)
    va = np.var(fa, ddof=1) if na > 1 else 0.0
    vb = np.var(fb, ddof=1) if nb > 1 else 0.0

    denom_df = na + nb - 2
    if denom_df > 0:
        sp = math.sqrt(((na - 1) * va + (nb - 1) * vb) / denom_df)
    else:
        sp = 1.0

    diff = ma - mb
    d = abs(diff) / sp if sp > 1e-9 else 0.0

    if d < 0.20:
        mag = "negligible"
        meaningful = False
        interp = "Efecto de magnitud despreciable (|d| < 0.20); no extrapolar significancia numerica a exito comercial."
    elif d < 0.50:
        mag = "small"
        meaningful = True
        interp = "Efecto pequeno pero perceptible en operaciones comerciales masivas."
    elif d < 0.80:
        mag = "medium"
        meaningful = True
        interp = "Efecto mediano de impacto comercial directo."
    else:
        mag = "large"
        meaningful = True
        interp = "Efecto grande de alta relevancia estrategica."

    return {
        "cohens_d": Decimal(str(d)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN),
        "practical_difference": Decimal(str(diff)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN),
        "magnitude": mag,
        "is_commercially_meaningful": meaningful,
        "n_group_a": na,
        "n_group_b": nb,
        "interpretation": interp,
    }


def adjust_multiple_comparisons_detailed(
    p_values: list[dict[str, Any]], method: str = "bonferroni", alpha: Decimal = Decimal("0.05")
) -> dict[str, Any]:
    if not p_values:
        raise InvariantViolationException("No se suministraron pruebas para ajuste")

    m = len(p_values)
    adj_alpha = (alpha / Decimal(str(m))).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
    fwer = Decimal(str(1.0 - (1.0 - float(alpha)) ** m)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    out = []
    for item in p_values:
        p = Decimal(str(item["p_value"]))
        sig = p <= adj_alpha
        out.append(
            {
                "segment": item.get("segment", "unknown"),
                "original_p_value": str(p),
                "adjusted_threshold": str(adj_alpha),
                "significant_after_adjustment": sig,
            }
        )

    return {
        "method": method,
        "total_comparisons": m,
        "nominal_alpha": str(alpha),
        "adjusted_alpha": adj_alpha,
        "fwer_unadjusted": fwer,
        "results": out,
    }
