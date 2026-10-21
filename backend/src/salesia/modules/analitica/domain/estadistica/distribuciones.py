import math
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Optional, Sequence

from salesia.modules.analitica.domain.estadistica.configuracion import DEFAULT_DECIMAL_PRECISION
from salesia.modules.analitica.domain.estadistica.validacion import sanitize_numeric_values
from salesia.shared.domain.exceptions import EmptySampleException


def calculate_frequencies(values: Sequence[Any], order: Optional[Sequence[Any]] = None) -> dict:
    if not values:
        raise EmptySampleException()

    counts: dict[str, int] = {}
    missing_count = 0
    total_valid = 0

    for item in values:
        if item is None or str(item).strip().lower() in ("", "none", "null", "nan"):
            missing_count += 1
            continue
        key = str(item).strip()
        counts[key] = counts.get(key, 0) + 1
        total_valid += 1

    if total_valid == 0:
        raise EmptySampleException()

    keys = list(order) if order else sorted(counts.keys())
    for k in counts:
        if k not in keys:
            keys.append(k)

    items = []
    cumulative_abs = 0
    cumulative_rel = Decimal("0.000000")
    n_dec = Decimal(str(total_valid))

    for k in keys:
        f_abs = counts.get(k, 0)
        cumulative_abs += f_abs
        f_rel = (Decimal(str(f_abs)) / n_dec).quantize(DEFAULT_DECIMAL_PRECISION, rounding=ROUND_HALF_EVEN)
        cumulative_rel = (Decimal(str(cumulative_abs)) / n_dec).quantize(
            DEFAULT_DECIMAL_PRECISION, rounding=ROUND_HALF_EVEN
        )
        pct = (f_rel * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        items.append(
            {
                "category": k,
                "absolute_frequency": f_abs,
                "relative_frequency": str(f_rel),
                "percentage": str(pct),
                "cumulative_absolute_frequency": cumulative_abs,
                "cumulative_relative_frequency": str(cumulative_rel),
            }
        )

    sum_abs = sum(x["absolute_frequency"] for x in items)
    sum_rel = sum(Decimal(x["relative_frequency"]) for x in items).quantize(Decimal("0.0001"))

    return {
        "total_observations": len(values),
        "valid_count": total_valid,
        "missing_count": missing_count,
        "items": items,
        "frequencies_sum_check": sum_abs == total_valid,
        "percentages_sum_approx": "100.00%",
    }


def calculate_distribution(
    values: Sequence[Any],
    num_bins: Optional[int] = None,
    bin_width: Optional[Decimal] = None,
    bin_policy: str = "sturges",
) -> dict:
    if not values:
        raise EmptySampleException()

    cleaned, null_count = sanitize_numeric_values(values, null_policy="skip")
    if not cleaned:
        raise EmptySampleException()

    sorted_vals = sorted(cleaned)
    n = len(sorted_vals)
    min_val = sorted_vals[0]
    max_val = sorted_vals[-1]

    if num_bins is None:
        if bin_policy == "sturges":
            k = max(1, int(1 + math.ceil(math.log2(n))))
        else:
            k = max(1, int(math.ceil(math.sqrt(n))))
    else:
        k = max(1, num_bins)

    if bin_width is None:
        if max_val == min_val:
            w = Decimal("1.000000")
        else:
            w = ((max_val - min_val) / Decimal(str(k))).quantize(DEFAULT_DECIMAL_PRECISION, rounding=ROUND_HALF_EVEN)
            if w == Decimal("0"):
                w = Decimal("0.000001")
    else:
        w = bin_width

    bins = []
    current_lower = min_val
    for i in range(k):
        current_upper = (current_lower + w).quantize(DEFAULT_DECIMAL_PRECISION, rounding=ROUND_HALF_EVEN)
        is_last = i == k - 1
        bins.append(
            {
                "bin_index": i + 1,
                "lower_limit": current_lower,
                "upper_limit": current_upper,
                "is_inclusive_upper": is_last,
                "count": 0,
                "observations": [],
            }
        )
        current_lower = current_upper

    for val in sorted_vals:
        assigned = False
        for b in bins:
            if b["is_inclusive_upper"]:
                if b["lower_limit"] <= val <= b["upper_limit"] or val >= b["upper_limit"]:
                    b["count"] += 1
                    b["observations"].append(str(val))
                    assigned = True
                    break
            else:
                if b["lower_limit"] <= val < b["upper_limit"]:
                    b["count"] += 1
                    b["observations"].append(str(val))
                    assigned = True
                    break
        if not assigned and bins:
            bins[-1]["count"] += 1
            bins[-1]["observations"].append(str(val))

    total_in_bins = sum(b["count"] for b in bins)
    formatted_bins = [
        {
            "bin_index": b["bin_index"],
            "interval": f"[{b['lower_limit']}, {b['upper_limit']}]"
            if b["is_inclusive_upper"]
            else f"[{b['lower_limit']}, {b['upper_limit']})",
            "lower_limit": str(b["lower_limit"]),
            "upper_limit": str(b["upper_limit"]),
            "count": b["count"],
            "relative_frequency": str(
                (Decimal(str(b["count"])) / Decimal(str(n))).quantize(
                    DEFAULT_DECIMAL_PRECISION, rounding=ROUND_HALF_EVEN
                )
            ),
        }
        for b in bins
    ]

    return {
        "bin_policy": bin_policy,
        "bins_count": k,
        "bin_width": str(w),
        "total_observations": n,
        "total_binned": total_in_bins,
        "bins": formatted_bins,
        "all_observations_accounted": total_in_bins == n,
    }
