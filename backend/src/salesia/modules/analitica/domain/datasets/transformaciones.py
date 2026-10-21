from decimal import Decimal
from typing import Any


def apply_variable_transformations(
    values: list[Decimal], transformations: list[str]
) -> tuple[list[Decimal], dict[str, Any]]:
    if not values:
        return [], {"mean": None, "median": None, "count": 0}

    current = list(values)
    metadata: dict[str, Any] = {}
    for t in transformations:
        if t == "winsorization_95" and len(current) >= 4:
            sorted_vals = sorted(current)
            n = len(sorted_vals)
            low_idx = int(n * 0.05)
            high_idx = int(n * 0.95)
            if high_idx >= n:
                high_idx = n - 1
            low_val = sorted_vals[low_idx]
            high_val = sorted_vals[high_idx]
            current = [min(max(v, low_val), high_val) for v in current]
            metadata["winsorized_bounds"] = {"low": str(low_val), "high": str(high_val)}

    mean_trans = (sum(current) / Decimal(len(current))).quantize(Decimal("0.000001"))
    sorted_curr = sorted(current)
    mid = len(sorted_curr) // 2
    med_trans = (
        sorted_curr[mid]
        if len(sorted_curr) % 2 != 0
        else ((sorted_curr[mid - 1] + sorted_curr[mid]) / Decimal("2")).quantize(Decimal("0.000001"))
    )

    metadata["mean"] = str(mean_trans)
    metadata["median"] = str(med_trans)
    metadata["count"] = len(current)
    return current, metadata
