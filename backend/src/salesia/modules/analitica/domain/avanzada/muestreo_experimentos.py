import random
from typing import Any, Optional


def execute_reproducible_sampling(
    rows: list[dict[str, Any]],
    size: Optional[int] = None,
    fraction: Optional[float] = None,
    seed: int = 42,
    replace: bool = False,
    strata_column: Optional[str] = None,
) -> dict[str, Any]:
    n = len(rows)
    if n == 0:
        return {"universe_size": 0, "sample_rows": [], "sample_indices": [], "seed": seed}

    k = size or int(n * (fraction or 0.1))
    k = max(1, min(k, n if not replace else k))

    rng = random.Random(seed)
    if strata_column:
        groups: dict[Any, list[int]] = {}
        for idx, r in enumerate(rows):
            key = r.get(strata_column)
            groups.setdefault(key, []).append(idx)
        selected_indices = []
        for key, indices in groups.items():
            strata_k = max(1, int(len(indices) * (k / n)))
            if replace:
                selected_indices.extend(rng.choices(indices, k=strata_k))
            else:
                selected_indices.extend(rng.sample(indices, min(strata_k, len(indices))))
    else:
        all_indices = list(range(n))
        if replace:
            selected_indices = rng.choices(all_indices, k=k)
        else:
            selected_indices = rng.sample(all_indices, k)

    selected_rows = [rows[i] for i in selected_indices]
    return {
        "universe_size": n,
        "sample_size": len(selected_rows),
        "seed": seed,
        "replace": replace,
        "sample_indices": selected_indices,
        "sample_rows": selected_rows,
    }


def evaluate_ab_experiment(events: list[dict[str, Any]], is_randomized: bool = True) -> dict[str, Any]:
    user_seen: dict[str, dict[str, Any]] = {}
    unexposed_count = 0

    for ev in events:
        uid = str(ev.get("user_id"))
        exposed = bool(ev.get("exposed", True))
        if not exposed:
            unexposed_count += 1
            continue

        var = str(ev.get("variant", "A"))
        conv = int(ev.get("converted", 0))
        if uid not in user_seen:
            user_seen[uid] = {"variant": var, "converted": conv}
        else:
            user_seen[uid]["converted"] = max(user_seen[uid]["converted"], conv)

    users_a = [u for u in user_seen.values() if u["variant"] == "A"]
    users_b = [u for u in user_seen.values() if u["variant"] == "B"]

    na, nb = len(users_a), len(users_b)
    ca = sum(u["converted"] for u in users_a)
    cb = sum(u["converted"] for u in users_b)

    pa = (ca / na) if na > 0 else 0.0
    pb = (cb / nb) if nb > 0 else 0.0

    total_n = na + nb
    exp_each = total_n / 2.0
    srm_stat = ((na - exp_each) ** 2 + (nb - exp_each) ** 2) / exp_each if exp_each > 0 else 0.0

    return {
        "is_randomized_experiment": is_randomized,
        "method_type": "experimento_aleatorio_ab" if is_randomized else "analisis_observacional_cuasiexperimental",
        "deduplicated_users_count": len(user_seen),
        "unexposed_excluded_count": unexposed_count,
        "group_a": {"total": na, "conversions": ca, "rate": pa},
        "group_b": {"total": nb, "conversions": cb, "rate": pb},
        "uplift": pb - pa,
        "srm_test": {"statistic": srm_stat, "has_sample_ratio_mismatch": srm_stat > 3.841},
        "causality_disclaimer": (
            "Diseno experimental aleatorio controlado"
            if is_randomized
            else "Estudio observacional con factores de confusion; no confundir asociacion con causalidad directa."
        ),
    }
