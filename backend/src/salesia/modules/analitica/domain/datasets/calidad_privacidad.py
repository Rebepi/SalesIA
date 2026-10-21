from typing import Any


def build_data_quality_report(
    total_received: int, used_rows: list[dict[str, Any]], excluded_counts: dict[str, int], variable_names: list[str]
) -> dict[str, Any]:
    total_used = len(used_rows)
    total_excluded = sum(excluded_counts.values())
    null_counts: dict[str, int] = {}
    for var in variable_names:
        null_counts[var] = sum(
            1 for r in used_rows if r.get(var) is None or str(r.get(var)).strip().lower() in ("", "none", "null")
        )

    total_cells = total_used * len(variable_names) if (total_used and variable_names) else 0
    total_nulls = sum(null_counts.values())
    completeness = round(((total_cells - total_nulls) / total_cells * 100.0), 2) if total_cells > 0 else 100.0

    return {
        "total_received": total_received,
        "total_used": total_used,
        "total_excluded": total_excluded,
        "excluded_by_reason": excluded_counts,
        "null_counts": null_counts,
        "duplicate_count": 0,
        "completeness_pct": completeness,
    }


def mask_sensitive_row(row: dict[str, Any], can_view_costs: bool, can_view_sensitive: bool) -> dict[str, Any]:
    copied = dict(row)
    if not can_view_costs:
        for k in ("unit_cost", "cost_amount", "unit_margin", "total_margin"):
            if k in copied:
                copied[k] = "***"
    if not can_view_sensitive:
        for k in ("email", "phone", "doc_number"):
            if k in copied:
                val = str(copied[k]) if copied[k] is not None else ""
                copied[k] = f"***{val[-3:]}" if len(val) >= 4 else "***"
    return copied
