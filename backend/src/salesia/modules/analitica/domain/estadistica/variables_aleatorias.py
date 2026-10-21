from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Optional, Sequence

from salesia.modules.analitica.domain.estadistica.configuracion import DEFAULT_DECIMAL_PRECISION
from salesia.modules.analitica.domain.estadistica.distribuciones import calculate_distribution
from salesia.modules.analitica.domain.estadistica.validacion import sanitize_numeric_values
from salesia.shared.domain.exceptions import EmptySampleException


def analyze_discrete_random_variable(
    observations: Sequence[Any], declared_support: Optional[Sequence[Any]] = None
) -> dict:
    if not observations:
        raise EmptySampleException()

    cleaned, null_count = sanitize_numeric_values(observations, null_policy="skip")
    if not cleaned:
        raise EmptySampleException()

    counts: dict[Decimal, int] = {}
    for x in cleaned:
        counts[x] = counts.get(x, 0) + 1

    support_set = set(counts.keys())
    if declared_support:
        cleaned_supp, _ = sanitize_numeric_values(declared_support, null_policy="skip")
        for s in cleaned_supp:
            support_set.add(s)

    sorted_support = sorted(support_set)
    n_dec = Decimal(str(len(cleaned)))
    pmf = []
    total_prob = Decimal("0.000000")

    for val in sorted_support:
        c = counts.get(val, 0)
        prob = (Decimal(str(c)) / n_dec).quantize(DEFAULT_DECIMAL_PRECISION, rounding=ROUND_HALF_EVEN)
        total_prob += prob
        pmf.append({"value": str(val), "observed_count": c, "probability": str(prob)})

    return {
        "support": [str(x) for x in sorted_support],
        "support_cardinality": len(sorted_support),
        "observations_count": len(cleaned),
        "null_count": null_count,
        "empirical_pmf": pmf,
        "total_probability_mass": str(total_prob),
        "mass_is_unitary": abs(total_prob - Decimal("1.000000")) <= Decimal("0.000010"),
    }


def analyze_continuous_random_variable(observations: Sequence[Any], num_bins: Optional[int] = None) -> dict:
    dist_info = calculate_distribution(observations, num_bins=num_bins)
    n = dist_info["total_observations"]
    w = Decimal(dist_info["bin_width"])

    density_bins = []
    for b in dist_info["bins"]:
        count = b["count"]
        density = (Decimal(str(count)) / (Decimal(str(n)) * w)).quantize(
            DEFAULT_DECIMAL_PRECISION, rounding=ROUND_HALF_EVEN
        )
        density_bins.append({**b, "empirical_density": str(density)})

    explanation = (
        "En variables continuas, la probabilidad puntual en cualquier valor exacto es cero P(X=x)=0. "
        "La altura del histograma representa densidad f(x), no probabilidad puntual. "
        "La probabilidad se calcula únicamente sobre intervalos finitos P(a <= X <= b)."
    )

    return {
        "total_observations": n,
        "bin_width": dist_info["bin_width"],
        "bins": density_bins,
        "estimation_method": "histogram_density_estimator",
        "didactic_concept": explanation,
    }
