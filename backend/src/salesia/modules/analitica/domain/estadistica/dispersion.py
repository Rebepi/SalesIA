from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Sequence

from salesia.modules.analitica.domain.estadistica.configuracion import ALGORITHM_VERSION, DEFAULT_DECIMAL_PRECISION
from salesia.modules.analitica.domain.estadistica.distribuciones import calculate_frequencies
from salesia.modules.analitica.domain.estadistica.tipos import StatisticalSummary, VariableScale
from salesia.modules.analitica.domain.estadistica.validacion import sanitize_numeric_values
from salesia.shared.domain.exceptions import EmptySampleException, InvariantViolationException


def calculate_mean(
    values: Sequence[Any], null_policy: str = "skip", precision: Decimal = DEFAULT_DECIMAL_PRECISION
) -> Decimal:
    if not values:
        raise EmptySampleException()

    cleaned, _ = sanitize_numeric_values(values, null_policy=null_policy)
    if not cleaned:
        raise EmptySampleException()

    total = sum(cleaned, Decimal("0"))
    count = Decimal(str(len(cleaned)))
    return (total / count).quantize(precision, rounding=ROUND_HALF_EVEN)


def calculate_median(
    values: Sequence[Any], null_policy: str = "skip", precision: Decimal = DEFAULT_DECIMAL_PRECISION
) -> Decimal:
    if not values:
        raise EmptySampleException()

    cleaned, _ = sanitize_numeric_values(values, null_policy=null_policy)
    if not cleaned:
        raise EmptySampleException()

    sorted_values = sorted(cleaned)
    n = len(sorted_values)
    mid = n // 2
    if n % 2 == 1:
        return sorted_values[mid].quantize(precision, rounding=ROUND_HALF_EVEN)
    else:
        med = (sorted_values[mid - 1] + sorted_values[mid]) / Decimal("2")
        return med.quantize(precision, rounding=ROUND_HALF_EVEN)


def calculate_median_exact(values: Sequence[Any], null_policy: str = "skip") -> Decimal:
    if not values:
        raise EmptySampleException()

    cleaned, _ = sanitize_numeric_values(values, null_policy=null_policy)
    if not cleaned:
        raise EmptySampleException()

    sorted_values = sorted(cleaned)
    n = len(sorted_values)
    mid = n // 2
    if n % 2 == 1:
        return sorted_values[mid]
    else:
        return (sorted_values[mid - 1] + sorted_values[mid]) / Decimal("2")


def compute_statistical_summary(values: Sequence[Decimal]) -> StatisticalSummary:
    if not values:
        raise EmptySampleException()

    cleaned, null_count = sanitize_numeric_values(values, null_policy="skip")
    if not cleaned:
        raise EmptySampleException()

    mean_val = calculate_mean(cleaned)
    median_val = calculate_median(cleaned)
    min_val = min(cleaned)
    max_val = max(cleaned)
    sum_val = sum(cleaned, Decimal("0"))

    diff = mean_val - median_val
    threshold = Decimal("0.001")
    if abs(diff) <= threshold:
        skew = "simetrica"
    elif diff > Decimal("0"):
        skew = "sesgo_positivo_derecha"
    else:
        skew = "sesgo_negativo_izquierda"

    sorted_v = sorted(cleaned)
    n = len(sorted_v)
    if n == 1:
        q1 = sorted_v[0]
        q3 = sorted_v[0]
        iqr = Decimal("0.000000")
        outliers_list = []
    else:
        lower_half = sorted_v[: n // 2]
        upper_half = sorted_v[(n + 1) // 2 :] if n % 2 != 0 else sorted_v[n // 2 :]
        q1 = calculate_median(lower_half)
        q3 = calculate_median(upper_half)
        iqr = (q3 - q1).quantize(DEFAULT_DECIMAL_PRECISION, rounding=ROUND_HALF_EVEN)
        lower_fence = q1 - (Decimal("1.5") * iqr)
        upper_fence = q3 + (Decimal("1.5") * iqr)
        outliers_list = [x for x in sorted_v if x < lower_fence or x > upper_fence]

    var_val = calculate_variance(cleaned, is_sample=True) if len(cleaned) > 1 else Decimal("0.000000")
    stdev_val = calculate_stdev(cleaned, is_sample=True) if len(cleaned) > 1 else Decimal("0.000000")

    explanation_text = (
        "La diferencia observada entre media y mediana describe asimetría muestral empírica, "
        "pero no permite concluir por sí sola causalidad operativa, presencia de fraude o la forma exacta de la distribución."
    )

    return StatisticalSummary(
        count=len(cleaned),
        mean=mean_val,
        median=median_val,
        minimum=min_val,
        maximum=max_val,
        sum_total=sum_val,
        skewness_direction=skew,
        null_count=null_count,
        distinct_values=len(set(cleaned)),
        explanation=explanation_text,
        outliers_count=len(outliers_list),
        variance=var_val,
        stdev=stdev_val,
        q1=q1,
        q3=q3,
        iqr=iqr,
        algorithm_version=ALGORITHM_VERSION,
        tolerance=str(DEFAULT_DECIMAL_PRECISION),
    )


def compare_mean_median(values: Sequence[Any], null_policy: str = "skip", variable_name: str = "variable") -> dict:
    if not values:
        raise EmptySampleException()

    cleaned, null_count = sanitize_numeric_values(values, null_policy=null_policy)
    if not cleaned:
        raise EmptySampleException()

    mean_val = calculate_mean(cleaned)
    median_val = calculate_median(cleaned)
    diff_abs = abs(mean_val - median_val).quantize(DEFAULT_DECIMAL_PRECISION, rounding=ROUND_HALF_EVEN)
    rel_diff = None
    if median_val != Decimal("0"):
        rel_diff = (diff_abs / abs(median_val)).quantize(DEFAULT_DECIMAL_PRECISION, rounding=ROUND_HALF_EVEN)

    explanation = (
        "La diferencia observada entre media y mediana describe la asimetría muestral empírica, "
        "pero no permite concluir por sí sola causalidad operativa, presencia de fraude o la forma analítica exacta de la distribución."
    )

    return {
        "variable_name": variable_name,
        "count": len(cleaned),
        "null_count": null_count,
        "mean": str(mean_val),
        "median": str(median_val),
        "absolute_difference": str(diff_abs),
        "relative_difference": str(rel_diff) if rel_diff is not None else None,
        "explanation": explanation,
        "algorithm_version": ALGORITHM_VERSION,
        "tolerance": str(DEFAULT_DECIMAL_PRECISION),
    }


def analyze_extreme_values(values: Sequence[Any], null_policy: str = "skip") -> dict:
    if not values:
        raise EmptySampleException()

    cleaned, null_count = sanitize_numeric_values(values, null_policy=null_policy)
    if not cleaned:
        raise EmptySampleException()

    q_info = calculate_quantiles(cleaned)
    outliers = q_info["outliers"]
    trimmed_values = [x for x in cleaned if x not in outliers]

    orig_summary = compute_statistical_summary(cleaned)
    trimmed_summary = compute_statistical_summary(trimmed_values) if trimmed_values else None

    return {
        "rule": "tukey_iqr_1.5",
        "lower_fence": str(q_info["lower_fence"]),
        "upper_fence": str(q_info["upper_fence"]),
        "outliers": [str(x) for x in outliers],
        "outliers_count": len(outliers),
        "original_summary": {
            "count": orig_summary.count,
            "mean": str(orig_summary.mean),
            "median": str(orig_summary.median),
            "minimum": str(orig_summary.minimum),
            "maximum": str(orig_summary.maximum),
        },
        "trimmed_summary": {
            "count": trimmed_summary.count,
            "mean": str(trimmed_summary.mean),
            "median": str(trimmed_summary.median),
            "minimum": str(trimmed_summary.minimum),
            "maximum": str(trimmed_summary.maximum),
        }
        if trimmed_summary
        else None,
        "excluded_observations_count": len(outliers),
        "retains_original_dataset": True,
    }


def compute_descriptive_summary(
    values: Sequence[Any],
    scale: VariableScale = VariableScale.QUANTITATIVE_CONTINUOUS,
    null_policy: str = "skip",
    variable_name: str = "variable",
) -> dict:
    if not values:
        raise EmptySampleException()

    if scale in (VariableScale.QUALITATIVE_NOMINAL, VariableScale.QUALITATIVE_ORDINAL):
        freq_info = calculate_frequencies(values)
        return {
            "variable_name": variable_name,
            "scale": scale.value,
            "count": freq_info["total_observations"],
            "valid_count": freq_info["valid_count"],
            "null_count": freq_info["missing_count"],
            "sum_total": None,
            "mean": None,
            "median": None,
            "minimum": None,
            "maximum": None,
            "distinct_categories": len(freq_info["items"]),
            "frequencies": freq_info["items"],
            "note": "Las variables cualitativas no admiten suma ni media numerica.",
        }

    cleaned, null_count = sanitize_numeric_values(values, null_policy=null_policy)
    if not cleaned:
        raise EmptySampleException()

    summary = compute_statistical_summary(cleaned)
    return {
        "variable_name": variable_name,
        "scale": scale.value,
        "count": summary.count,
        "null_count": null_count,
        "sum_total": str(summary.sum_total),
        "mean": str(summary.mean),
        "median": str(summary.median),
        "minimum": str(summary.minimum),
        "maximum": str(summary.maximum),
        "variance": str(summary.variance) if summary.variance is not None else None,
        "stdev": str(summary.stdev) if summary.stdev is not None else None,
        "q1": str(summary.q1) if summary.q1 is not None else None,
        "q3": str(summary.q3) if summary.q3 is not None else None,
        "iqr": str(summary.iqr) if summary.iqr is not None else None,
        "skewness_direction": summary.skewness_direction,
    }


def calculate_weighted_mean(values: Sequence[Any], weights: Sequence[Any], method: str = "weighted_by_units") -> dict:
    if not values or not weights:
        raise EmptySampleException()

    if len(values) != len(weights):
        raise InvariantViolationException("La cantidad de valores y pesos debe ser identica")

    cleaned_vals, _ = sanitize_numeric_values(values, null_policy="error")
    cleaned_weights, _ = sanitize_numeric_values(weights, null_policy="error")

    total_weight = Decimal("0")
    weighted_sum = Decimal("0")
    simple_sum = Decimal("0")

    for v, w in zip(cleaned_vals, cleaned_weights):
        if w < Decimal("0"):
            raise InvariantViolationException("Los pesos deben ser no negativos")
        weighted_sum += v * w
        total_weight += w
        simple_sum += v

    if total_weight <= Decimal("0"):
        raise InvariantViolationException("La suma de pesos debe ser estrictamente positiva")

    w_mean = (weighted_sum / total_weight).quantize(DEFAULT_DECIMAL_PRECISION, rounding=ROUND_HALF_EVEN)
    simple_mean = (simple_sum / Decimal(str(len(cleaned_vals)))).quantize(
        DEFAULT_DECIMAL_PRECISION, rounding=ROUND_HALF_EVEN
    )

    return {
        "method_applied": method,
        "weighted_mean_by_units": str(w_mean),
        "simple_average_per_sale": str(simple_mean),
        "total_weight": str(total_weight),
        "observations_count": len(cleaned_vals),
        "tolerance": str(DEFAULT_DECIMAL_PRECISION),
        "algorithm_version": ALGORITHM_VERSION,
    }


def calculate_variance(values: Sequence[Decimal], is_sample: bool = True) -> Decimal:
    if not values:
        raise EmptySampleException("n=0 no tiene resultado de varianza")
    if is_sample and len(values) < 2:
        raise InvariantViolationException(
            "n=1 no produce varianza muestral numerica valida debido al denominador n-1=0"
        )
    mean_val = calculate_mean(values)
    sum_sq = sum(((x - mean_val) ** 2 for x in values), Decimal("0"))
    divisor = Decimal(str(len(values) - 1 if is_sample else len(values)))
    return (sum_sq / divisor).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)


def calculate_stdev(values: Sequence[Decimal], is_sample: bool = True) -> Decimal:
    var_val = calculate_variance(values, is_sample)
    std_float = float(var_val) ** 0.5
    return Decimal(str(std_float)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)


def calculate_quantiles(values: Sequence[Decimal]) -> dict:
    if not values:
        raise EmptySampleException()
    sorted_v = sorted(values)
    n = len(sorted_v)
    med = calculate_median(sorted_v)
    if n == 1:
        return {
            "q1": sorted_v[0],
            "median": med,
            "q3": sorted_v[0],
            "iqr": Decimal("0.000000"),
            "lower_fence": sorted_v[0],
            "upper_fence": sorted_v[0],
            "outliers": [],
        }
    lower_half = sorted_v[: n // 2]
    upper_half = sorted_v[(n + 1) // 2 :] if n % 2 != 0 else sorted_v[n // 2 :]
    q1 = calculate_median(lower_half)
    q3 = calculate_median(upper_half)
    iqr = (q3 - q1).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
    lower_fence = (q1 - (Decimal("1.5") * iqr)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
    upper_fence = (q3 + (Decimal("1.5") * iqr)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
    outliers = [x for x in sorted_v if x < lower_fence or x > upper_fence]
    return {
        "q1": q1,
        "median": med,
        "q3": q3,
        "iqr": iqr,
        "lower_fence": lower_fence,
        "upper_fence": upper_fence,
        "outliers": outliers,
    }
