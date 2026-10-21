from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from salesia.shared.domain.exceptions import EmptySampleException, InvariantViolationException, ZeroEvidenceException


def validate_manual_bayes_inputs(
    prior_a: Decimal, likelihood_b_given_a: Decimal, evidence_b: Decimal, mode: str = "proportion"
) -> tuple[Decimal, Decimal, Decimal]:
    if mode == "percentage":
        if not (Decimal("0") <= prior_a <= Decimal("100")):
            raise InvariantViolationException("En modo porcentaje, P(A) debe estar entre 0 y 100")
        if not (Decimal("0") <= likelihood_b_given_a <= Decimal("100")):
            raise InvariantViolationException("En modo porcentaje, P(B|A) debe estar entre 0 y 100")
        if not (Decimal("0") <= evidence_b <= Decimal("100")):
            raise InvariantViolationException("En modo porcentaje, P(B) debe estar entre 0 y 100")
        prior_a = prior_a / Decimal("100")
        likelihood_b_given_a = likelihood_b_given_a / Decimal("100")
        evidence_b = evidence_b / Decimal("100")
    else:
        if prior_a > Decimal("1") or likelihood_b_given_a > Decimal("1") or evidence_b > Decimal("1"):
            raise InvariantViolationException(
                "En modo proporcion, los valores deben estar en [0, 1]. Si ingreso valores porcentuales, active modo porcentaje explicitamente"
            )
        if not (Decimal("0") <= prior_a <= Decimal("1")):
            raise InvariantViolationException("P(A) debe estar en el intervalo [0, 1]")
        if not (Decimal("0") <= likelihood_b_given_a <= Decimal("1")):
            raise InvariantViolationException("P(B|A) debe estar en el intervalo [0, 1]")
        if not (Decimal("0") <= evidence_b <= Decimal("1")):
            raise InvariantViolationException("P(B) debe estar en el intervalo [0, 1]")

    if evidence_b == Decimal("0"):
        raise ZeroEvidenceException(
            "Evidencia imposible: P(B)=0 carece de soporte observacional y no permite condicionar"
        )

    intersection = (likelihood_b_given_a * prior_a).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
    max_possible_intersection = min(prior_a, evidence_b).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
    if intersection > max_possible_intersection:
        raise InvariantViolationException(
            f"Inconsistencia probabilistica: la interseccion estimada ({intersection}) supera la evidencia o el prior maximo ({max_possible_intersection})"
        )

    min_frechet = max(Decimal("0"), prior_a + evidence_b - Decimal("1")).quantize(
        Decimal("0.000001"), rounding=ROUND_HALF_EVEN
    )
    if intersection < min_frechet:
        raise InvariantViolationException(
            f"Inconsistencia probabilistica: la interseccion ({intersection}) es inferior a la cota minima de Frechet ({min_frechet})"
        )

    posterior = (intersection / evidence_b).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
    if posterior > Decimal("1.000000"):
        raise InvariantViolationException(f"Inconsistencia probabilistica: P(A|B) calculada ({posterior}) supera 1.0")

    return prior_a, likelihood_b_given_a, evidence_b


def calculate_empirical_bayes_full(
    sample_space_size: int,
    event_a_count: int,
    event_b_count: int,
    intersection_count: int,
    smoothing_enabled: bool = False,
    alpha: Decimal = Decimal("1.0"),
    min_support_threshold: int = 30,
) -> dict[str, Any]:
    if sample_space_size <= 0:
        raise EmptySampleException("No es posible calcular Bayes sobre un universo vacio")
    if event_b_count <= 0:
        raise ZeroEvidenceException("Evidencia imposible: P(B)=0 no tiene soporte en el universo de datos")
    if event_a_count <= 0:
        raise InvariantViolationException("P(B|A) no es estimable desde conteos cuando P(A)=0")
    if intersection_count > min(event_a_count, event_b_count):
        raise InvariantViolationException("La interseccion no puede exceder los conteos individuales")

    n = Decimal(str(sample_space_size))
    na = Decimal(str(event_a_count))
    nb = Decimal(str(event_b_count))
    ni = Decimal(str(intersection_count))

    prior_a = (na / n).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
    evidence_b = (nb / n).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
    likelihood_b_given_a = (ni / na).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

    not_a_count = sample_space_size - event_a_count
    not_a_and_b_count = event_b_count - intersection_count
    if not_a_count > 0:
        likelihood_b_given_not_a = (Decimal(str(not_a_and_b_count)) / Decimal(str(not_a_count))).quantize(
            Decimal("0.000001"), rounding=ROUND_HALF_EVEN
        )
    else:
        likelihood_b_given_not_a = Decimal("0.000000")

    direct_posterior = (ni / nb).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
    formula_posterior = ((likelihood_b_given_a * prior_a) / evidence_b).quantize(
        Decimal("0.000001"), rounding=ROUND_HALF_EVEN
    )
    if formula_posterior > Decimal("1.000000"):
        formula_posterior = Decimal("1.000000")

    equivalence = abs(direct_posterior - formula_posterior) <= Decimal("0.000002")

    smoothed_data = None
    final_posterior = formula_posterior
    if smoothing_enabled:
        smooth_num_a = ni + alpha
        smooth_den_a = na + (Decimal("2") * alpha)
        smooth_lik_a = (smooth_num_a / smooth_den_a).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

        smooth_num_not_a = Decimal(str(not_a_and_b_count)) + alpha
        smooth_den_not_a = Decimal(str(not_a_count)) + (Decimal("2") * alpha) if not_a_count > 0 else Decimal("1")
        smooth_lik_not_a = (smooth_num_not_a / smooth_den_not_a).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)

        smooth_ev = (smooth_lik_a * prior_a) + (smooth_lik_not_a * (Decimal("1") - prior_a))
        smooth_post = (smooth_lik_a * prior_a) / smooth_ev if smooth_ev > Decimal("0") else Decimal("0.000000")
        if smooth_post > Decimal("1.000000"):
            smooth_post = Decimal("1.000000")
        final_posterior = smooth_post.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
        smoothed_data = {
            "alpha": str(alpha),
            "smoothed_likelihood_b_given_a": str(smooth_lik_a),
            "smoothed_likelihood_b_given_not_a": str(smooth_lik_not_a),
            "smoothed_evidence_b": str(smooth_ev.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)),
            "smoothed_posterior_a_given_b": str(final_posterior),
            "pseudocounts_applied": str(alpha * Decimal("2")),
        }

    low_sample = sample_space_size < min_support_threshold or min(event_a_count, event_b_count) < 5
    warn_text = None
    if low_sample:
        warn_text = f"Soporte muestral bajo (n={sample_space_size}). Resultado con alta incertidumbre muestral"

    contingency = {
        "a_and_b": intersection_count,
        "a_and_not_b": event_a_count - intersection_count,
        "not_a_and_b": not_a_and_b_count,
        "not_a_and_not_b": sample_space_size - (event_a_count + event_b_count - intersection_count),
        "total_a": event_a_count,
        "total_not_a": not_a_count,
        "total_b": event_b_count,
        "total_not_b": sample_space_size - event_b_count,
        "grand_total": sample_space_size,
    }

    formula_cards = [
        {
            "term": "P(A)",
            "label": "Prior (Probabilidad a priori de A)",
            "value": str(prior_a),
            "formula": "n(A) / n(Universo)",
        },
        {
            "term": "P(B|A)",
            "label": "Verosimilitud (Probabilidad de B dado A)",
            "value": str(likelihood_b_given_a),
            "formula": "n(A ∩ B) / n(A)",
        },
        {
            "term": "P(B|~A)",
            "label": "Verosimilitud complementaria",
            "value": str(likelihood_b_given_not_a),
            "formula": "n(~A ∩ B) / n(~A)",
        },
        {"term": "P(B)", "label": "Evidencia marginal de B", "value": str(evidence_b), "formula": "n(B) / n(Universo)"},
        {
            "term": "Conteo Directo",
            "label": "Equivalencia muestral directa",
            "value": str(direct_posterior),
            "formula": "n(A ∩ B) / n(B)",
        },
        {
            "term": "P(A|B)",
            "label": "Posterior (Probabilidad a posteriori)",
            "value": str(final_posterior),
            "formula": "P(B|A) × P(A) / P(B)",
        },
    ]

    return {
        "sample_space_size": sample_space_size,
        "prior_a": str(prior_a),
        "likelihood_b_given_a": str(likelihood_b_given_a),
        "likelihood_b_given_not_a": str(likelihood_b_given_not_a),
        "evidence_b": str(evidence_b),
        "posterior_a_given_b": str(final_posterior),
        "direct_count_posterior": str(direct_posterior),
        "equivalence_verified": equivalence,
        "smoothing_enabled": smoothing_enabled,
        "smoothing_details": smoothed_data,
        "contingency_table": contingency,
        "formula_cards": formula_cards,
        "low_sample_warning": low_sample,
        "warning_message": warn_text,
        "interpretation": f"La probabilidad posterior P(A|B) es de {final_posterior} frente a un prior P(A) de {prior_a}",
        "causality_disclaimer": "Asociacion condicional observada en la poblacion del dataset. No implica relacion de causa y efecto directa",
    }
